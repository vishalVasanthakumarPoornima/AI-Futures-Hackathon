from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from fpdf import FPDF
import requests
import os

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
    "What is your preferred language for reading?",
    "Are you able to read without difficulty?",
    "What is your current address?",
    "What is your phone number?",
    "What is your email address?",
    "How many children under 18 live with you?",
    "How many adults live in your household (excluding you)?",
    "What is your living environment? (e.g., city, suburb, rural)?",
    "What is the highest level of education you have completed?",
    "How do you prefer to learn health information?",
    "Do you have any challenges that affect your ability to learn or communicate (e.g., vision, hearing, cognitive issues)?",
    "Have you ever been diagnosed with any of the following conditions? (diabetes, asthma, cancer, etc.)?",
    "What medications are you currently taking?",
    "Have you had any hospitalizations in the past year?",
    "Have you had any surgeries in the past year?",
    "Do you experience chronic pain? If so, where?",
    "Does anyone in your family have a history of heart disease?",
    "Does anyone in your family have a history of cancer?",
    "Does anyone in your family have a history of mental health conditions?",
    "Does anyone in your family have a history of diabetes?",
    "Has anyone in your immediate family died of a hereditary illness?",
    "What is your current occupation?",
    "Do you smoke or use tobacco products? If so, how often?",
    "Do you consume alcohol? If so, how often?",
    "Do you use recreational drugs? If so, how often?",
    "Do you have any dietary restrictions?",
    "Do you exercise regularly? How many days a week?",
    "How would you rate your current emotional wellbeing? (Excellent, Good, Fair, Poor)?",
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

@app.get("/summary")
def summarize_conversation():
    if not answers:
        return {"summary": "No responses to summarize yet."}
    summary_prompt = "Summarize the following patient intake answers for use in a medical record:\n\n"
    for i, answer in enumerate(answers):
        summary_prompt += f"Q{i+1}: {all_questions[i]}\nA: {answer}\n\n"
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={"model": "deepseek-r1:8b", "messages": [{"role": "system", "content": summary_prompt}]}
    )
    summary = response.json().get("message", {}).get("content", "Summary generation failed.")
    return {"summary": summary}

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
        "http://localhost:11434/api/chat",
        json={"model": "deepseek-r1:8b", "messages": [{"role": "system", "content": system_prompt}]}
    )
    answer = response.json().get("message", {}).get("content", "Could not generate an answer.")
    return {"answer": answer}
