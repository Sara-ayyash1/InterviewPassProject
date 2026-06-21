import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
import json
import time
from google.genai.errors import ServerError


BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=BASE_DIR / '.env')

api_key = os.environ.get('GEMINI_API_KEY')
client = genai.Client(api_key=api_key)

MODEL = 'models/gemini-2.5-flash'

def _call_gemini_with_retry(prompt, retries=3):
    """دالة مساعدة لإعادة المحاولة عند حدوث خطأ 503"""
    for i in range(retries):
        try:
            return client.models.generate_content(model=MODEL, contents=prompt)
        except ServerError as e:
            if e.code == 503 and i < retries - 1:
                time.sleep(2 ** i)
                continue
            raise e

def _ask_json(prompt):
    response = _call_gemini_with_retry(prompt)
    text = response.text.strip()
    text = text.replace('```json', '').replace('```', '').strip()
    return json.loads(text)

def analyze_cv(resume_text, job):
    skills = ', '.join([s.name for s in job.skills.all()])
    prompt = f"""
    You are a recruiting assistant. Evaluate the candidate's resume against the job requirements.
    Job title: {job.title}
    Job description: {job.description}
    Required experience level: {job.get_experience_level_display()}
    Required skills: {skills}
    Candidate's resume: {resume_text}
    Respond with ONLY a JSON object, no extra text, in this exact shape:
    {{"match_score": number, "strengths": [], "gaps": [], "summary": "string"}}
    """
    try:
        return _ask_json(prompt)
    except (json.JSONDecodeError, Exception):
        return {'error': 'Could not analyze the resume. Please try again later.'}

def generate_questions(title, skills, experience_level):
    prompt = f"""
    Suggest 5 technical interview questions for a candidate applying to this job:
    Title: {title}
    Skills: {skills}
    Experience level: {experience_level}
    Respond with ONLY a JSON object in this exact shape: {{"questions": ["q1", "q2", ...]}}
    """
    try:
        return _ask_json(prompt)
    except (json.JSONDecodeError, Exception):
        return {'error': 'Could not generate questions. Please try again later.'}

def generate_description(title, skills, experience_level):
    prompt = f"""
    Write a professional job description (3 to 4 paragraphs) for this position:
    Title: {title}
    Required skills: {skills}
    Experience level: {experience_level}
    Respond with ONLY the description text, no introduction, no quotation marks.
    """
    try:
        response = _call_gemini_with_retry(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error in generate_description: {e}")
        return "Could not generate description at this time. Please try again."