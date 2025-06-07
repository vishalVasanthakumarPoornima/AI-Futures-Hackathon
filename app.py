import streamlit as st
import json
from fpdf import FPDF
from typing import Optional
from random import randint
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

def process_symptoms(symptoms: str) -> dict:
    """Process symptoms using Gemini API and return potential reasons and risk rating."""
    headers = {
        "Content-Type": "application/json"
    }
    
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
        
        # Print response for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        response.raise_for_status()
        
        data = response.json()
        if 'candidates' in data and len(data['candidates']) > 0:
            response_text = data['candidates'][0]['content']['parts'][0]['text']
            
            # Parse the response
            reasons = []
            risk_rating = 5  # Default risk rating
            life_threatening = "No assessment available"
            
            sections = response_text.split('\n')
            
            # Extract information
            for line in sections:
                if line.strip().startswith('-'):
                    reasons.append(line.strip('- ').capitalize())
                elif 'risk rating:' in line.lower():
                    try:
                        risk_rating = int(''.join(filter(str.isdigit, line)))
                    except ValueError:
                        risk_rating = 5
                elif 'life-threatening' in line.lower():
                    life_threatening = line.split(':')[-1].strip()
            
            if not reasons:
                reasons = ["No specific causes identified"]
            
            return {
                "reasons": reasons,
                "risk_rating": risk_rating,
                "life_threatening": life_threatening
            }
        else:
            st.error("Unable to get a response from the AI service. Please try again.")
            return {
                "reasons": ["Unable to analyze symptoms. Please try again or contact support."],
                "risk_rating": 0,
                "life_threatening": "Assessment unavailable"
            }
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the AI service: {str(e)}")
        return {
            "reasons": ["Unable to process symptoms. Please try again later."],
            "risk_rating": 0,
            "life_threatening": "Assessment unavailable"
        }
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return {
            "reasons": ["System error. Please try again or contact support."],
            "risk_rating": 0,
            "life_threatening": "Assessment unavailable"
        }

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
    st.header("How can we help you today?")
    choice = st.radio("Choose an option:", ["Take Patient History", "Get Diagnosis"])
    
    if choice == "Take Patient History":
        st.subheader("Patient History Questionnaire")
        patient_history = {}
        
        # Patient history questions
        questions = {
            "x": st.text_input("x?"),
            "y": st.text_input("y?"),
            "z": st.text_input("z?")
        }
        
        if st.button("Submit History"):
            # Save all answers that were provided
            patient_history = {q: a for q, a in questions.items() if a}
            save_patient_info(patient_history, "patient_history.json")
            
            # Generate PDF with questions and answers
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Patient History Report", ln=True, align='C')
            pdf.ln(10)
            
            for question, answer in patient_history.items():
                pdf.multi_cell(0, 10, txt=f"Question: {question}?")
                pdf.multi_cell(0, 10, txt=f"Answer: {answer}")
                pdf.ln(5)
            
            pdf.output("patient_history.pdf")
            
            # Provide download button
            with open("patient_history.pdf", "rb") as file:
                st.download_button(
                    label="Download Patient History PDF",
                    data=file,
                    file_name="patient_history.pdf",
                    mime="application/pdf"
                )
    
    else:  # Get Diagnosis
        st.subheader("Symptom Analysis")
        symptoms = st.text_area("Describe your symptoms:")
        pain_rating = st.slider("Rate your pain (1-10):", 1, 10)
        if st.button("Process Symptoms"):
            with st.spinner("Analyzing symptoms..."):
                result = process_symptoms(f"{symptoms} (Pain level: {pain_rating}/10)")
                
                st.subheader("Analysis Results")
                
                st.write("**Potential Causes:**")
                for reason in result["reasons"]:
                    st.write(f"• {reason}")
                
                st.write("\n**Life-Threatening Assessment:**")
                st.write(result.get("life_threatening", "Assessment unavailable"))
                
                risk_rating = result["risk_rating"]
                st.write("\n**Risk Rating:**", risk_rating, "/10")
                
                # Visual risk indicator
                if risk_rating >= 7:
                    st.error(f"⚠️ High Risk ({risk_rating}/10)")
                elif risk_rating >= 4:
                    st.warning(f"⚠️ Moderate Risk ({risk_rating}/10)")
                else:
                    st.success(f"✓ Low Risk ({risk_rating}/10)")
                
                if risk_rating >= 8:
                    st.error("🚨 Please seek immediate medical attention!")
                
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
