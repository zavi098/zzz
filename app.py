import streamlit as st
from pymongo import MongoClient
import os
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
from PyPDF2 import PdfReader
import re
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# MongoDB connection
mongo_uri = os.getenv("MONGODB_URI")
client = MongoClient(mongo_uri)
db = client['resume_short']

# Define collections
resumeFetchedData = db.resumeFetchedData
applied_emp = db.Applied_EMP
irs_users = db.IRS_USERS
jobs = db.JOBS

# Create directory for saving resumes if it doesn't exist
resume_save_path = "uploaded_resumes"
os.makedirs(resume_save_path, exist_ok=True)

# Initialize session state
if 'shortlisted_resumes' not in st.session_state:
    st.session_state.shortlisted_resumes = []

# Function to read PDF files
def input_pdf_text(uploaded_file):
    text = ""
    try:
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            text += page.extract_text() or ""
    except Exception as e:
        logging.error(f"Error reading PDF {uploaded_file.name}: {e}")
        st.error(f"Error reading PDF: {e}")
        return None
    return text

# Function to get AI response (simulate LLM)
def get_gemini_response(input_text):
    try:
        model = genai.GenerativeModel('gemini-1.0-pro')
        response = model.generate_content(input_text)
        return response.text
    except Exception as e:
        logging.error(f"Error generating AI response: {e}")
        st.error(f"Error generating AI response: {e}")
        return None

# Function to extract name and email from resume
def extract_name_and_email(resume_text):
    name_pattern = r'(?i)(?<=Name: |name: |NAME: )([A-Za-z\s]+)'
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    name_match = re.search(name_pattern, resume_text)
    email_match = re.search(email_pattern, resume_text)
    
    name = name_match.group(0).strip() if name_match else "Unknown"
    email = email_match.group(0).strip() if email_match else "No Email Found"
    
    return name, email

# Function to extract skills using LLM
def extract_skills_with_llm(resume_text, job_description):
    prompt = f"Given the following resume text, identify the relevant skills for the job description provided:\n\nJob Description: {job_description}\n\nResume Text: {resume_text}\n\nRelevant Skills:"
    skills_response = get_gemini_response(prompt)
    if skills_response:
        return [skill.strip() for skill in skills_response.split(',')]
    return []

# Function to extract key skills from job description
def extract_skills_from_jd(job_description):
    prompt = f"Extract a list of key skills from the following job description:\n\n{job_description}\n\nSkills:"
    skills_response = get_gemini_response(prompt)
    if skills_response:
        return [skill.strip() for skill in skills_response.split(',')]
    return []

# Function to evaluate candidate fit using LLM
def evaluate_candidate_fit(resume_text, job_description):
    prompt = f"Based on the following resume and job description, evaluate the candidate's fit. Highlight strengths and weaknesses:\n\nJob Description: {job_description}\n\nResume Text: {resume_text}\n\nCandidate Evaluation:"
    evaluation_response = get_gemini_response(prompt)
    return evaluation_response if evaluation_response else "No evaluation generated."

# Function to extract experience from resume
def extract_experience(resume_text):
    exp_pattern = r'(\d+)\+?\s*(years|year)\s*experience'
    experience_match = re.search(exp_pattern, resume_text, re.IGNORECASE)
    return int(experience_match.group(1)) if experience_match else 0

# Function to calculate match percentage based on skills and experience
def calculate_match_score(resume_skills, jd_skills, jd_experience, resume_experience):
    skill_overlap = len(set(resume_skills) & set(jd_skills))
    skill_match_score = (skill_overlap / len(jd_skills)) * 100 if jd_skills else 0
    
    experience_score = min((resume_experience / jd_experience) * 100, 100) if jd_experience > 0 else 0
    
    total_score = (skill_match_score * 0.7) + (experience_score * 0.3)
    return total_score, skill_match_score, experience_score

# Function to rank resumes
def rank_resumes(jd, uploaded_files, jd_experience, jd_skills):
    ranked_resumes = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        st.progress((i + 1) / len(uploaded_files))
        text = input_pdf_text(uploaded_file)
        if not text:
            continue

        candidate_name, candidate_email = extract_name_and_email(text)
        resume_experience = extract_experience(text)

        # Extract skills using LLM
        resume_skills = extract_skills_with_llm(text, jd)

        # Calculate match score based on skills and experience
        total_match_score, skill_match_score, experience_score = calculate_match_score(
            resume_skills, jd_skills, jd_experience, resume_experience)

        # Evaluate candidate fit
        candidate_evaluation = evaluate_candidate_fit(text, jd)

        resume_data = {
            "candidate_name": candidate_name,
            "candidate_email": candidate_email,
            "match_percentage": total_match_score,
            "skills_matched": resume_skills,
            "experience_matched": resume_experience,
            "skill_match_score": skill_match_score,
            "experience_score": experience_score,
            "evaluation": candidate_evaluation
        }

        ranked_resumes.append(resume_data)

        # Save the uploaded resume
        save_path = os.path.join(resume_save_path, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Save resume data to MongoDB
        resumeFetchedData.insert_one(resume_data)

    # Sort resumes by match percentage
    ranked_resumes = sorted(ranked_resumes, key=lambda x: x["match_percentage"], reverse=True)
    return ranked_resumes

# Sidebar for navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.selectbox("Choose a section", ["Home", "Upload Resumes", "Ranked Resumes"])

# Get JD experience dynamically
jd_experience = st.sidebar.number_input("Required Experience (Years)", min_value=0, value=5, step=1)

if app_mode == "Home":
    st.title("Welcome to the Resume Ranking System")
    st.write("""
        This app allows you to upload resumes, rank them based on a provided job description, and view the ranked results.
        Use the navigation menu to get started.
    """)

elif app_mode == "Upload Resumes":
    st.title("Upload Resumes and Job Description")

    jd = st.text_area("Paste the Job Description")
    uploaded_files = st.file_uploader("Upload Your Resumes", type="pdf", accept_multiple_files=True)

    submit = st.button("Submit")

    if submit:
        if not jd.strip():
            st.error("Please provide a valid job description.")
        elif not uploaded_files:
            st.error("Please upload at least one resume.")
        else:
            jd_skills = extract_skills_from_jd(jd)
            ranked_resumes = rank_resumes(jd, uploaded_files, jd_experience, jd_skills)
            st.session_state.shortlisted_resumes = ranked_resumes
            st.success("Resumes ranked successfully! Go to 'Ranked Resumes' to view the results.")

elif app_mode == "Ranked Resumes":
    st.title("Ranked Resumes")
    if 'shortlisted_resumes' in st.session_state and st.session_state.shortlisted_resumes:
        ranked_resumes = st.session_state.shortlisted_resumes
        for rank, resume in enumerate(ranked_resumes, start=1):
            with st.expander(f"Rank {rank}: {resume['candidate_name']} ({resume['match_percentage']:.2f}%)"):
                st.write(f"*Email:* {resume['candidate_email']}")
                st.write(f"*Skills Matched:* {', '.join(resume['skills_matched'])}")
                st.write(f"*Experience:* {resume['experience_matched']} years")
                st.write(f"*Skill Match Score:* {resume['skill_match_score']:.2f}%")
                st.write(f"*Experience Score:* {resume['experience_score']:.2f}%")
                st.write("*Evaluation:*")
                st.write(resume['evaluation'])

        csv = pd.DataFrame(ranked_resumes).to_csv(index=False)
        st.download_button(
            label="Download Results as CSV",
            data=csv,
            file_name="ranked_resumes.csv",
            mime="text/csv",
        )
    else:
        st.warning("No resumes have been ranked yet. Please upload resumes first.")

