import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from schemas import (
    RoleAnalysis, CandidateFitAnalysis, DynamicQuestionRequest,
    DynamicQuestionResponse, FinalPerformanceReport, ReportGenerationRequest
)
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is not set. Check your .env file!")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-2.5-flash"

def analyze_documents(jd_text: str, resume_text: str) -> tuple[RoleAnalysis, CandidateFitAnalysis]:
    # Role Analysis
    role_prompt = f"Analyze the following Job Description thoroughly:\n\n{jd_text}"
    role_res = client.models.generate_content(
        model=MODEL_NAME,
        contents=role_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RoleAnalysis,
            system_instruction="You are an expert HR Talent Acquisition Specialist[cite: 2]. Extract all structural specifications from the Job Description[cite: 2]."
        )
    )
    role_analysis = RoleAnalysis.model_validate_json(role_res.text)

    # Candidate Match Analysis
    candidate_prompt = f"""
    Job Description Analysis:
    {role_analysis.model_dump_json()}

    Candidate Resume:
    {resume_text}
    """
    candidate_res = client.models.generate_content(
        model=MODEL_NAME,
        contents=candidate_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CandidateFitAnalysis,
            system_instruction="You are a technical hiring manager[cite: 2, 3, 5]. Evaluate candidate alignment accurately against the JD[cite: 2, 3]."
        )
    )
    candidate_analysis = CandidateFitAnalysis.model_validate_json(candidate_res.text)
    
    return role_analysis, candidate_analysis

def generate_next_question(req: DynamicQuestionRequest) -> DynamicQuestionResponse:
    history_formatted = "\n".join([f"{item.role.upper()}: {item.text}" for item in req.conversation_history])
    
    system_instruction = f"""
    You are an AI Interviewer running Level {req.current_level} of a job interview[cite: 3, 4, 5].
    Level 1: Screening (Resume verification, motivation, basic understanding)[cite: 3, 4].
    Level 2: Competency (Technical depth, behavioral STAR method, domain knowledge)[cite: 4, 5].
    Level 3: Deep-Dive (Challenge weak answers, probe claims, edge cases, why/how questions)[cite: 5].

    CRITICAL RULES:
    1. Do NOT ask static or generic questions[cite: 4, 5].
    2. Directly reference specific details in the resume[cite: 5].
    3. Dynamically follow up if the candidate's last answer was brief or flawed[cite: 5].
    
    Role Context: {req.jd_analysis.model_dump_json()}
    Candidate Context: {req.candidate_analysis.model_dump_json()}
    Conversation History:
    {history_formatted}
    """

    res = client.models.generate_content(
        model=MODEL_NAME,
        contents=f"Generate question for Level {req.current_level}. Prior response: {req.latest_candidate_response or 'Interview Start'}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DynamicQuestionResponse,
            system_instruction=system_instruction
        )
    )
    return DynamicQuestionResponse.model_validate_json(res.text)

def generate_final_report(req: ReportGenerationRequest) -> FinalPerformanceReport:
    history_formatted = "\n".join([f"{item.role.upper()}: {item.text}" for item in req.conversation_history])
    
    system_instruction = """
    You are a Senior Engineering Director generating a post-interview performance evaluation report[cite: 7, 8].
    Provide granular, highly actionable feedback[cite: 8, 9]. Avoid generic comments[cite: 8].
    Provide structured preparation gaps prioritized by severity[cite: 9, 10].
    """

    prompt = f"""
    JD Analysis: {req.jd_analysis.model_dump_json()}
    Candidate Match: {req.candidate_analysis.model_dump_json()}
    Full Transcript:
    {history_formatted}
    """

    res = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FinalPerformanceReport,
            system_instruction=system_instruction
        )
    )
    return FinalPerformanceReport.model_validate_json(res.text)