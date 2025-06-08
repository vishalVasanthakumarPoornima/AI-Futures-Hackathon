from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi import HTTPException
from pydantic import BaseModel
from fpdf import FPDF
from typing import Optional
from dotenv import load_dotenv
import requests
import os
import json
import time

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    user_message: str
    follow_up: bool = False
    follow_up_ref: str | None = None

class CompareRequest(BaseModel):
    context: str
    answer: str

conversation_history = []
answers = []
question_index = 0
uploaded_doc_text = ""

all_questions = [
    "What is your full name?",
    "What is your date of birth?",
    "What gender do you identify as?",
    "What is your phone number?",
    "What is your current address?",
    "Do you have any allergies? If so, please list them.",
    "Do you have any chronic conditions? If so, please list them.",
    "Do you have any current symptoms or concerns?",
    "Have you had any surgeries in the past? If so, please list them.",
    "Have you had any hospitalizations in the past? If so, please list them.",
    "Do you have any current medications? If so, please list them.",
    "Do you have any family history of major illnesses? If so, please list them.",
    "Do you have health insurance? If so, please provide the name of the provider.",
    "What is your emergency contact's name and phone number?",
]

@app.post("/reset")
def reset_chat():
    global question_index, answers, conversation_history
    question_index = 0
    answers = []
    conversation_history = []
    return {"status": "reset"}

@app.post("/chat")
def chat(msg: Message):
    global question_index, conversation_history

    if msg.follow_up:
        conversation_history = [
            {"role": "system", "content": f"You are a medical assistant answering follow-up questions patients may have about their intake form. The patient is referring to: \"{msg.follow_up_ref}\""},
            {"role": "user", "content": msg.user_message or "Please elaborate on this."}
        ]
        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={"model": "deepseek-r1:8b", "messages": conversation_history}
            )
            reply_text = response.json().get("message", {}).get("content", "No reply.")
            return {"response": reply_text}
        except Exception as e:
            return {"response": f"Error generating follow-up: {str(e)}"}

    if question_index >= len(all_questions):
        return {"response": "Thank you! You've completed the full intake questionnaire.", "done": True}

    answers.append(msg.user_message)
    next_question = all_questions[question_index]
    question_index += 1
    return {"response": next_question, "done": False, "question": next_question}

@app.post("/analysis")
def process_symptoms(load: dict) -> dict:
    """Process symptoms using Gemini API and return potential reasons and risk rating."""
    headers = {
        "Content-Type": "application/json"
    }
    
    symptoms = load.get("sym")
    
    
    prompt = f"""Given these symptoms, please analyze:
    Symptoms: {symptoms}
    
    Please respond in this format:
    Potential Causes:
    - [cause 1]
    - [cause 2]
    - [cause 3]
    
    Life-Threatening Assessment:
    [Yes/No] - [brief explanation]
    
    Risk Rating: [1-10]
    """
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    try:
        query_params = {"key": GEMINI_API_KEY}
        response = requests.post(
            GEMINI_API_URL,
            params=query_params,
            json=payload,
            headers=headers
        )
        with open("gemini_response.json", "w") as f:
            f.write(response.text) 

        data = response.json()
        answer = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return {"answer": answer}
    except Exception as e:
        return {"answer": f"Error generating response: {str(e)}"}


@app.post("/follow_up")
def follow_up(payload: dict):

    headers = {
    "Content-Type": "application/json"
    }

    index = payload.get("ref_index")
    user_question = payload.get("question")

    if index is None or not user_question:
        raise HTTPException(status_code=400, detail="Missing reference index or question")

    if index >= len(all_questions) or index >= len(answers):
        return {"answer": "Invalid reference index."}

    reference = f"Question: {all_questions[index]}\nAnswer: {answers[index]}"
    prompt = f"""You are a helpful medical assistant answering follow-up questions from a patient.
This is the original intake data:\n\n{reference}\n\nNow the patient has this follow-up question:\n\n{user_question}\n\nAnswer:"""


    pay = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    try:
        query_params = {"key": GEMINI_API_KEY}
        response = requests.post(
        GEMINI_API_URL,
        params=query_params,
        json=pay,
        headers=headers
        )

        with open("gemini_response.json", "w") as f:
            f.write(response.text) 

        data = response.json()
        answer = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return {"answer": answer}
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    answer += data.get("response", "")
                except json.JSONDecodeError:
                    continue
        return {"answer": answer}
    except Exception as e:
        return {"answer": f"Error generating response: {str(e)}"}


def get_symptom_analysis(symptoms: str, pain_rating: int) -> dict:
    """Analyze symptoms and return structured health insights."""
    result = process_symptoms(f"{symptoms} (Pain level: {pain_rating}/10)")

    reasons = result.get("reasons", [])
    life_threat = result.get("life_threatening", "Assessment unavailable")
    risk_rating = result.get("risk_rating", 0)

    status = (
        "high" if risk_rating >= 7 else
        "moderate" if risk_rating >= 4 else
        "low"
    )

    return {
        "reasons": reasons,
        "life_threatening": life_threat,
        "risk_rating": risk_rating,
        "status": status,
        "urgent": risk_rating >= 8
    }




@app.get("/summary")
def get_summary():
    try:
        chat_summary_text = create_medical_prompt()
        headers = {
        "Content-Type": "application/json"
        }
        pay = {
        "contents": [{
            "parts": [{
                    "text": chat_summary_text
                }]
            }]
        }
        query_params = {"key": GEMINI_API_KEY}
        response = requests.post(
            GEMINI_API_URL,
            params=query_params,
            json=pay,
            headers=headers
        )
        with open("gemini_response.json", "w") as f:
            f.write(response.text) 
        data = response.json()
        answer = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return {"summary": answer}
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    summary += data.get("response", "")
                except json.JSONDecodeError:
                    continue
        return {"summary": summary}
    except requests.exceptions.RequestException as e:
        return {"summary": f"Error: {str(e)}"}

@app.get("/download_pdf")
def download_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Patient History Summary", ln=True, align="C")
    pdf.ln(10)
    for i, answer in enumerate(answers):
        q = all_questions[i] if i < len(all_questions) else "(Unknown Question)"
        pdf.multi_cell(0, 10, f"Q: {q}\nA: {answer}\n")
    file_path = "patient_summary.pdf"
    pdf.output(file_path)
    return FileResponse(file_path, media_type="application/pdf", filename=file_path)

@app.post("/upload_doc")
def upload_doc(file: UploadFile = File(...)):
    global uploaded_doc_text
    contents = file.file.read().decode("utf-8", errors="ignore")
    uploaded_doc_text = contents
    return {"status": "uploaded", "length": len(contents)}

@app.post("/ask_doc")
def ask_doc(payload: dict):
    question = payload.get("question", "")
    if not uploaded_doc_text:
        return JSONResponse(content={"answer": "No document uploaded yet."})
    system_prompt = f"""You are a medical assistant. Use the uploaded document to answer this question:\n\nDocument:\n{uploaded_doc_text}\n\nQuestion: {question}\nAnswer:"""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "mistral", "prompt": system_prompt, "stream": True},
        timeout=120,
        stream=True
    )
    summary = ""
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode("utf-8"))
                summary += data.get("response", "")
            except json.JSONDecodeError:
                continue
    return {"summary": summary}

def create_medical_prompt() -> str:
    medical_data = []
    for i, answer in enumerate(answers[:len(all_questions)]):
        question = all_questions[i].lower()
        if any(kw in question for kw in ['name', 'birth', 'diagnos', 'medic', 'hospital', 'surg', 'pain']):
            medical_data.append(f"{all_questions[i]}: {answer}")
    if not medical_data:
        return ""
    return (
        "Generate a professional medical summary using ONLY these facts:\n\n" +
        "\n".join(medical_data) +
        "\n\nFormat with these sections:\n1. Patient Demographics\n2. Medical History\n3. Current Medications\n" +
        "4. Treatment Plan\nUse bullet points and medical terminology."
    )
