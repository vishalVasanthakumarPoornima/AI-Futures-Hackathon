from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
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

conversation_history = []
answers = []
question_index = 0
uploaded_doc_text = ""

# (Your full all_questions list here — truncated for brevity)
all_questions = [
     "Are you ready to get your medical history recorded?",
    "What is your full name?",
    "What is your date of birth?",
    "What gender do you identify as?",
    "What is your preferred language for speaking?",
    "What is your preferred language for reading?",
    "What is your preferred language for writing?",
    "What is your preferred method of communication? (e.g., phone, email, in-person)",
    "Do you have any allergies? If so, please list them.",
    "Do you have any chronic conditions? If so, please list them.",
    "Do you have any current symptoms or concerns?",
    "What is your emergency contact's name?",
    "What is your emergency contact's relationship to you?",
    "What is your emergency contact's phone number?",
    "What is your emergency contact's email address?",
    "Do you have a preferred pharmacy? If so, please provide the name and address.",
    "Do you have any health insurance? If so, please provide the name of the provider.",
    "What is your health insurance policy number?",
    "What is your health insurance group number?",
    "What is your occupation?",
    "What is your current employment status? (e.g., employed, unemployed, retired)",
    "What is your highest level of education?",
    "Do you have any disabilities? If so, please describe them.",
    "Do you have any special needs or accommodations that we should be aware of?",
    "Do you have any cultural or religious beliefs that may affect your healthcare?",
    "Do you have any pets? If so, please list them.",
    "Do you have any dietary restrictions? If so, please list them.",
    "Do you have any specific health goals or concerns that you would like to address?",
    "Do you have a primary care provider? If so, please provide their name and contact information.",
    "Have you had any surgeries in the past? If so, please list them.",
    "Have you had any hospitalizations in the past? If so, please list them.",
    "Have you had any major illnesses in the past? If so, please list them.",
    "Do you have any family history of major illnesses? If so, please list them.",
    "Do you have any current medications? If so, please list them.",
    "Do you have any past medications that you have taken? If so, please list them.",
    "Do you have any allergies to medications? If so, please list them.",
    "Do you have any allergies to foods? If so, please list them.",
    "Do you have any allergies to environmental factors? If so, please list them.",
    "Do you have any history of mental health conditions? If so, please describe them.",
    "Do you have any history of substance abuse? If so, please describe it.",
    "Do you have any history of domestic violence or abuse? If so, please describe it.",
    "Do you have any history of sexual abuse or assault? If so, please describe it.",
    "Do you have any history of trauma or PTSD? If so, please describe it.",
    "Do you have any history of self-harm or suicidal thoughts? If so, please describe it.",
    "Do you have any history of eating disorders? If so, please describe it.",
    "Do you have any history of sleep disorders? If so, please describe it.",
    "Do you have any history of chronic pain? If so, please describe it.",
    "Do you have any history of heart disease? If so, please describe it.",
    "Do you have any history of lung disease? If so, please describe it.",
    "Do you have any history of liver disease? If so, please describe it.",
    "Do you have any history of kidney disease? If so, please describe it.",
    "Do you have any history of gastrointestinal disease? If so, please describe it.",
    "Do you have any history of neurological disease? If so, please describe it.",
    "Do you have any history of autoimmune disease? If so, please describe it.",
    "Do you have any history of cancer? If so, please describe it.",
    "Do you have any history of diabetes? If so, please describe it.",
    "Do you have any history of hypertension? If so, please describe it.",
    "Do you have any history of high cholesterol? If so, please describe it.",
    "Do you have any history of stroke? If so, please describe it.",
    "Do you have any history of seizures? If so, please describe it.",
    "Do you have any history of thyroid disease? If so, please describe it.",
    "Do you have any history of asthma or other respiratory conditions? If so, please describe it.",
    "Do you have any history of allergies or allergic reactions? If so, please describe it.",
    "Do you have any history of skin conditions? If so, please describe it.",
    "Do you have any history of eye conditions? If so, please describe it.",
    "Do you have any history of hearing conditions? If so, please describe it.",
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

@app.post("/follow_up")
def follow_up(payload: dict):
    index = payload.get("ref_index")
    user_question = payload.get("question")

    if index is None or not user_question:
        raise HTTPException(status_code=400, detail="Missing reference index or question")

    if index >= len(all_questions) or index >= len(answers):
        return {"answer": "Invalid reference index."}

    reference = f"Question: {all_questions[index]}\nAnswer: {answers[index]}"
    prompt = (
        "You are a helpful medical assistant answering follow-up questions from a patient.\n"
        f"This is the original intake data:\n\n{reference}\n\n"
        f"Now the patient has this follow-up question:\n\n{user_question}\n\nAnswer:"
    )

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "mistral", "prompt": prompt, "stream": True},
            timeout=120,
            stream=True
        )
        answer = ""
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
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "mistral", "prompt": chat_summary_text, "stream": True},
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
    except requests.exceptions.RequestException as e:
        return {"summary": f"Error: {str(e)}"}

@app.get("/download_pdf")
def download_pdf():
    class PatientIntakePDF(FPDF):
        def header(self):
            try:
                self.image("logo.png", x=10, y=10, w=30)
            except:
                self.set_xy(10, 10)
                self.set_fill_color(200, 200, 200)
                self.rect(10, 10, 30, 30, style="F")
            self.set_xy(45, 10)
            self.set_font("Arial", "B", 16)
            self.cell(0, 10, "Patient Intake Form", ln=True, align="L")
            self.ln(20)

        def add_section(self, title: str):
            self.set_fill_color(230, 230, 230)
            self.set_font("Arial", "B", 13)
            self.cell(0, 10, title, ln=True, fill=True)
            self.ln(3)

        def add_qa(self, q: str, a: str):
            self.set_font("Arial", "B", 12)
            self.multi_cell(0, 8, f"{q}")
            self.set_font("Arial", "", 12)
            self.multi_cell(0, 8, f"{a}")
            self.ln(2)

        def add_signature_block(self):
            self.ln(10)
            self.set_font("Arial", "B", 12)
            self.cell(0, 10, "Physician Signature: ___________________________", ln=True)
            self.ln(5)
            self.cell(0, 10, "Date: ________________", ln=True)

    pdf = PatientIntakePDF()
    pdf.add_page()

    # Example: categorize first few questions
    sections = {
        "Patient Information": list(range(0, 6)),  # Extend these ranges based on full questions
        "Emergency Contact": list(range(11, 15)),
        "Medical History": list(range(29, 55)),
    }

    for section_name, indexes in sections.items():
        pdf.add_section(section_name)
        for i in indexes:
            if i < len(answers):
                pdf.add_qa(all_questions[i], answers[i])

    # Add uncategorized remaining answers
    remaining = [i for i in range(len(answers)) if not any(i in idxs for idxs in sections.values())]
    if remaining:
        pdf.add_section("Additional Information")
        for i in remaining:
            pdf.add_qa(all_questions[i], answers[i])

    pdf.add_signature_block()

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
    system_prompt = (
        f"You are a medical assistant. Use the uploaded document to answer this question:\n\n"
        f"Document:\n{uploaded_doc_text}\n\n"
        f"Question: {question}\nAnswer:"
    )
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
        "\n\nFormat with these sections:\n1. Patient Demographics\n2. Medical History\n3. Current Medications\n"
        "4. Treatment Plan\nUse bullet points and medical terminology."
    )
