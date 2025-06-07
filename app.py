import streamlit as st
import json
from fpdf import FPDF
from typing import Optional
from random import randint
import requests

# Gemini API configuration
GEMINI_API_KEY = "AIzaSyAE1Y6-_7jtOjN3wGi4QR2ai0c_qrhMGbc"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"

def process_symptoms(symptoms: str) -> dict:
    """Process symptoms using Gemini API and return potential reasons and risk rating."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GEMINI_API_KEY}"
    }
    
    prompt = f"Based on these symptoms: {symptoms}\n1. What are the potential causes?\n2. Is this life threatening?\n3. On a scale of 1-10 (1 being lowest risk, 10 being highest risk), what is the risk rating?"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    try:
        response = requests.post(GEMINI_API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            response_text = data["candidates"][0]["content"]["parts"][0]["text"]
            
            # Parse the response to extract reasons and risk rating
            lines = response_text.split('\n')
            reasons = []
            risk_rating = 5  # Default risk rating
            
            for line in lines:
                if line.startswith('-') or line.startswith('*'):
                    reasons.append(line.strip('- *'))
                if 'risk rating' in line.lower():
                    try:
                        risk_rating = int(''.join(filter(str.isdigit, line)))
                    except ValueError:
                        pass
            
            return {"reasons": reasons, "risk_rating": risk_rating}
        else:
            return {"reasons": ["Unable to process symptoms"], "risk_rating": 0}
    except Exception as e:
        return {"reasons": [f"Error processing symptoms: {str(e)}"], "risk_rating": 0}

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

# Initialize session state for page navigation
if 'page' not in st.session_state:
    st.session_state.page = "User Info"

# Multi-page app
st.title("Pre-Doctor Visit Web App")

if st.session_state.page == "User Info":
    st.header("User Information")
    name = st.text_input("Enter your name:")
    dob = st.date_input("Enter your date of birth:")
    if st.button("Next"):
        save_patient_info({"name": name, "dob": str(dob)}, "user_info.json")
        st.session_state.page = "Insurance Info"
        st.rerun()

elif st.session_state.page == "Insurance Info":
    st.header("Insurance Information")
    insurance_name = st.text_input("Enter your insurance name:")
    insurance_id = st.text_input("Enter your insurance ID:")
    if st.button("Next"):
        save_patient_info({"insurance_name": insurance_name, "insurance_id": insurance_id}, "insurance_info.json")
        st.session_state.page = "Symptoms"
        st.rerun()

elif st.session_state.page == "Symptoms":
    st.header("Symptoms")
    symptoms = st.text_area("Describe your symptoms:")
    pain_rating = st.slider("Rate your pain (1-10):", 1, 10)
    if st.button("Process Symptoms"):
        result = process_symptoms(f"{symptoms} (Pain level: {pain_rating}/10)")
        st.write("Potential reasons for your symptoms:")
        for reason in result["reasons"]:
            st.write(f"- {reason}")
        st.write(f"Risk rating: {result['risk_rating']} (1 = Low risk, 10 = High risk)")
        if st.button("Schedule Appointment"):
            st.session_state.page = "Appointment"
            st.rerun()

elif st.session_state.page == "Appointment":
    st.header("Schedule Appointment")
    appointment_time = f"{randint(7, 17)}:{randint(0, 59):02d}"
    st.write("Your appointment has been scheduled with Dr. AIdrian.")
    st.write(f"Appointment time: {appointment_time}")
    if st.button("Start Over"):
        st.session_state.page = "User Info"
        st.rerun()
