from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi import HTTPException
from pydantic import BaseModel
from fpdf import FPDF
from typing import Optional
import requests
import os
import json
import time

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
    "What is your preferred language for speaking?",
    "What is your preferred language for reading?"
    # "Are you able to read without difficulty?",
    # "What is your current address?",
    # "What is your phone number?",
    # "What is your email address?",
    # "How many children under 18 live with you?",
    # "How many adults live in your household (excluding you)?",
    # "What is your living environment? (e.g., city, suburb, rural)?",
    # "What is the highest level of education you have completed?",
    # "How do you prefer to learn health information?",
    # "Do you have any challenges that affect your ability to learn or communicate (e.g., vision, hearing, cognitive issues)?",
    # "Have you ever been diagnosed with any of the following conditions? (diabetes, asthma, cancer, etc.)?",
    # "What medications are you currently taking?",
    # "Have you had any hospitalizations in the past year?",
    # "Have you had any surgeries in the past year?",
    # "Do you experience chronic pain? If so, where?",
    # "Does anyone in your family have a history of heart disease?",
    # "Does anyone in your family have a history of cancer?",
    # "Does anyone in your family have a history of mental health conditions?",
    # "Does anyone in your family have a history of diabetes?",
    # "Has anyone in your immediate family died of a hereditary illness?",
    # "What is your current occupation?",
    # "Do you smoke or use tobacco products? If so, how often?",
    # "Do you consume alcohol? If so, how often?",
    # "Do you use recreational drugs? If so, how often?",
    # "Do you have any dietary restrictions?",
    # "Do you exercise regularly? How many days a week?",
    # "How would you rate your current emotional wellbeing? (Excellent, Good, Fair, Poor)?",
    # "Have you ever been diagnosed or treated for a mental health condition?",
    # "Have you felt anxious, depressed, or hopeless in the last 2 weeks?",
    # "Have you ever tested positive for COVID-19?",
    # "Did you experience long-term symptoms such as fatigue, brain fog, or breathing issues?",
    # "Do you still experience any COVID-related symptoms today?",
    # "Do you have a primary care provider?",
    # "How long have you been seeing your primary care provider?",
    # "Are you following a care plan created with a doctor?",
    # "Are your medications reviewed regularly by a healthcare professional?",
    # "Do you feel confident managing your own health?",
    # "Do you need assistance from others to manage your health (e.g., emotional, financial, physical)?",
    # "Do you have insurance that covers your current health needs?"
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



def generate_llm_summary() -> Optional[str]:
    """Generate high-quality medical summary using DeepSeek LLM"""
    try:
        # 1. Prepare optimized medical prompt
        prompt = create_medical_prompt()
        if not prompt:
            return None

        # 2. Configure LLM request for medical context
        llm_config = {
            "model": "deepseek-r1:8b",
            "prompt": prompt,
            "system": "You are a medical assistant creating structured patient summaries.",
            "options": {
                "temperature": 0.3,
                "num_ctx": 2048,
                "repeat_penalty": 1.1
            },
            "stream": False
        }

        # 3. Execute request with proper error handling
        with requests.post(
            "http://localhost:11434/api/generate",
            json=llm_config,
            headers={"Content-Type": "application/json"},
            timeout=60
        ) as response:
            
            # 4. Validate and parse response
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, dict):
                    summary = result.get("response", "").strip()
                    if validate_medical_summary(summary):
                        return summary

    except Exception as e:
        print(f"LLM Summary Error: {str(e)}")
    
    return None

def create_medical_prompt() -> str:
    """Construct optimized medical prompt"""
    try:
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
    except Exception:
        return ""

def validate_medical_summary(text: str) -> bool:
    """Ensure summary meets quality standards"""
    return (
        isinstance(text, str) and 
        len(text) > 50 and 
        any(section in text.lower() for section in ["demographic", "history", "medication"])
    )

@app.get("/summary")
def get_summary():
    try:
        chat_summary_text = create_medical_prompt()  # however you create your prompt

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": chat_summary_text,
                "stream": True
            },
            timeout=120,
            stream=True  # must stream to process tokens incrementally
        )

        summary = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    summary += data.get("response", "")
                except json.JSONDecodeError:
                    continue  # skip malformed lines

        return {"summary": summary}

    except requests.exceptions.HTTPError as e:
        print("LLM returned an HTTP error:", e.response.text)
        return {"summary": "Error: LLM failed with a server error."}
    except requests.exceptions.RequestException as e:
        print("Request failed:", e)
        return {"summary": "Error: Unable to generate summary."}

def generate_structured_fallback() -> str:
    """High-quality fallback without LLM"""
    sections = {
        "Patient Demographics": [],
        "Medical History": [],
        "Current Medications": [],
        "Health Risks": []
    }
    
    for i, answer in enumerate(answers[:len(all_questions)]):
        question = all_questions[i].lower()
        
        if 'name' in question or 'birth' in question:
            sections["Patient Demographics"].append(answer)
        elif 'diagnos' in question or 'hospital' in question:
            sections["Medical History"].append(answer)
        elif 'medic' in question:
            sections["Current Medications"].append(answer)
        elif 'smok' in question or 'alcohol' in question:
            sections["Health Risks"].append(answer)
    
    summary = ["MEDICAL SUMMARY", "="*40]
    for section, items in sections.items():
        if items:
            summary.append(f"\n{section.upper()}:")
            summary.extend(f" • {item}" for item in items)
    
    return "\n".join(summary) if len(summary) > 2 else "Insufficient medical data"

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
            json={
                "model": "mistral",
                "prompt": system_prompt,
                "stream": True
            },
            timeout=120,
            stream=True  # must stream to process tokens incrementally
        )
    summary = ""
    for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    summary += data.get("response", "")
                except json.JSONDecodeError:
                    continue  # skip malformed lines

    return {"summary": summary}
