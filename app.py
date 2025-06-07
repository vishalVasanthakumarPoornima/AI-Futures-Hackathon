import streamlit as st
import json
from fpdf import FPDF
from typing import Optional
import os

# Gemini API placeholder
class GeminiAPI:
    @staticmethod
    def ask_question(question: str) -> str:
        # Simulate API response
        return f"Response to: {question}"

# Save patient information locally
def save_patient_info(data: dict, filename: str):
    with open(filename, 'w') as file:
        json.dump(data, file)

# Generate PDF summary
def generate_pdf_summary(data: dict, filename: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Patient History Summary", ln=True, align='C')
    for key, value in data.items():
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)
    pdf.output(filename)

# Streamlit interface
st.title('AI Futures Hackathon')
st.write('Welcome to the AI Futures Hackathon Streamlit app!')

# Patient information
patient_info = {}

# Medical history questions
st.header("Patient Questionnaire")
questions = [
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
answers = {}
for question in questions:
    answer = st.text_input(question)
    if answer:
        answers[question] = answer

if st.button("Submit Questionnaire"):
    save_patient_info(answers, "patient_info.json")
    st.write("Questionnaire submitted successfully!")

# Generate PDF
if st.button("Download Patient History PDF"):
    generate_pdf_summary(answers, "patient_summary.pdf")
    st.write("PDF generated successfully! You can download it below.")
    with open("patient_summary.pdf", "rb") as file:
        st.download_button("Download PDF", file, "patient_summary.pdf")

# Schedule a visit
st.header("Schedule a Visit")
visit_reason = st.text_input("Why are you here today?")
if st.button("Submit Reason"):
    st.write("Your symptoms have been summarized:")
    st.write(visit_reason)
    st.write("The doctor has been contacted and will reach back shortly.")

# Chatbot interaction
st.header("Chatbot")
chat_question = st.text_input("Ask a question to the chatbot:")
if st.button("Get Response"):
    response = GeminiAPI.ask_question(chat_question)
    st.write(response)
