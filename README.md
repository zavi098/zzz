//resume ranking sytstem


Resume Ranking System
This Resume Ranking System is a web application built using Streamlit, Google Generative AI (Gemini), and MongoDB. It allows users to upload resumes (in PDF format), provide a job description, and automatically rank the resumes based on the match percentage. The ranking is determined by evaluating the resume's skills and experience relative to the job description.

Key Features:
Resume Upload: Users can upload multiple PDF resumes.
Job Description Input: Users can input a job description to match with the uploaded resumes.
Skill Extraction: The system extracts relevant skills from both the resumes and the job description using a Generative AI model (Google Gemini).
Experience Extraction: The system automatically extracts experience data from the resumes.
Candidate Evaluation: The system uses Generative AI to evaluate how well a candidate fits the job description based on their resume.
Ranking Resumes: Resumes are ranked based on a calculated match score (skills and experience), with the highest-ranked resumes being shown first.
MongoDB Integration: Resumes and ranking data are stored in a MongoDB database for easy management.
Downloadable Results: After ranking the resumes, users can download the results as a CSV file.


Requirements:
Python 3.x
Streamlit
PyMongo (for MongoDB integration)
Google Generative AI (Gemini)
PyPDF2 (for reading PDFs)
Pandas (for managing and exporting data)
dotenv (for environment variable management)

Setup:Clone the repository:

git clone https://github.com/yourusername/resume-ranking-system.git
cd resume-ranking-system

Install the required dependencies:
pip install -r requirements.txt


Set up environment variables:
GOOGLE_API_KEY: Obtain your Google Generative AI API key and set it in a .env file.
MONGODB_URI: Set your MongoDB connection URI in the .env file.

Run the Streamlit app:streamlit run app.py
Access the web application at http://localhost:8501.

