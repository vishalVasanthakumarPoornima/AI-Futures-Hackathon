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
from datetime import datetime

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
    "Are you ready to get your medical history recorded?",
    "What is your full name?",
    "What is your date of birth?",
    "What gender do you identify as?",
    "What is your preferred language, if any?",
    "What is your preferred method of communication? (e.g., phone, email, in-person)",
    "Do you have any allergies or chronic conditions? If so, please list them.",
    "Do you have any current symptoms or concerns?",
    "Do you have any disabilities? If so, please describe them.",
    "Have you had any surgeries in the past? If so, please list them.",
    "Have you had any hospitalizations in the past? If so, please list them.",
    "Have you had any major illnesses in the past? If so, please list them.",
    "Do you have any family history of major illnesses? If so, please list them.",
    "Do you have any history of mental health conditions, substance abuse, domestic violence or abuse, sexual abuse, PTSD, self-harm, eating disorders, sleep disorders, chronic pain, heart disease, or any other illnesses? If so, please describe them.",
    "Do you smoke or use tobacco products? If so, how often?",
    "Do you consume alcohol? If so, how often?",
    "Do you use recreational drugs? If so, how often?",
    "Do you have any dietary restrictions?",
    "Have you ever been diagnosed or treated for a mental health condition?",
    "Have you felt anxious, depressed, or hopeless in the last 2 weeks?",
    "Have you ever tested positive for COVID-19?",
    "Did you experience long-term symptoms such as fatigue, brain fog, or breathing issues?",
    "Do you still experience any COVID-related symptoms today?",
    "Do you have a primary care provider?",
    "How long have you been seeing your primary care provider?",
    "Are you following a care plan created with a doctor?",
    "Are your medications reviewed regularly by a healthcare professional?",
    "Do you feel confident managing your own health?",
    "Do you need assistance from others to manage your health (e.g., emotional, financial, physical)?",
    "Do you have insurance that covers your current health needs?"   
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
    try:
        pdf.image("logo_clean.png", x=10, y=8, w=30)
    except RuntimeError:
        pass
    pdf.set_xy(45, 10)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, "Patient History Summary", ln=True, align="L")
    pdf.ln(15)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", ln=True)
    pdf.ln(5)
    sections = {
        "Basic Information": range(1, 6),
        "Medical Background": range(6, 14),
        "Behavioral and Mental Health": range(14, 20),
        "COVID-19 History": range(20, 23),
        "Care Management": range(23, 27),
        "Self-Management & Support": range(27, 30),
        "Insurance": range(29, 30)
    }
    for section, q_range in sections.items():
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(30, 144, 255)
        pdf.cell(0, 10, f"  {section}", ln=True, fill=True)
        pdf.set_draw_color(0, 0, 0)
        pdf.set_line_width(0.8)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        pdf.set_font("Helvetica", "", 12)
        for i in q_range:
            if i >= len(all_questions): break
            question = all_questions[i]
            answer = answers[i] if i < len(answers) else "No response."
            pdf.set_text_color(0)
            pdf.multi_cell(0, 8, f"Q{i+1}: {question}")
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(0, 8, f"A{i+1}: {answer}")
            pdf.ln(3)
        pdf.ln(4)
    file_path = "patient_summary.pdf"
    pdf.output(file_path)
    return FileResponse(path=file_path, media_type="application/pdf", filename="patient_summary.pdf")

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
        timeout=180,
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
