from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# --- STEP 1: ROLE ANALYSIS ---
class RoleAnalysis(BaseModel):
    role_title: str
    key_responsibilities: List[str]
    required_skills: List[str]
    preferred_skills: List[str]
    technical_competencies: List[str]
    behavioral_competencies: List[str]
    experience_expectations: str
    important_keywords: List[str]
    important_concepts: List[str]

# --- STEP 2: CANDIDATE ANALYSIS & FIT ---
class CandidateFitAnalysis(BaseModel):
    candidate_skills: List[str]
    relevant_experience: List[str]
    relevant_projects: List[str]
    strengths_against_jd: List[str]
    missing_skills: List[str]
    weak_areas: List[str]
    suspicious_claims_to_probe: List[str]
    job_fit_score: int = Field(ge=0, le=100)
    match_category: str
    strong_match_items: List[str]
    partial_match_items: List[str]
    missing_match_items: List[str]

# --- STEP 3: DYNAMIC INTERVIEW TYPES ---
class DialogueItem(BaseModel):
    role: str  # "interviewer" or "candidate"
    text: str

class DynamicQuestionRequest(BaseModel):
    jd_analysis: RoleAnalysis
    candidate_analysis: CandidateFitAnalysis
    current_level: int
    conversation_history: List[DialogueItem]
    latest_candidate_response: Optional[str] = None

class DynamicQuestionResponse(BaseModel):
    question: str
    target_competency: str
    rationale_for_asking: str
    is_follow_up: bool
    perceived_answer_quality: Optional[str] = None
    next_level_transition: bool = False

# --- STEP 4: REPORT & EVALUATION ---
class QuestionFeedback(BaseModel):
    question: str
    candidate_answer: str
    assessment: str
    what_was_good: str
    what_could_be_better: str
    ideal_direction: str

class PreparationGapItem(BaseModel):
    priority: int
    topic: str
    review_checklist: List[str]

class FinalPerformanceReport(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    competency_scores: Dict[str, int]
    question_feedback_list: List[QuestionFeedback]
    strengths: List[str]
    weaknesses: List[str]
    preparation_gaps: List[PreparationGapItem]
    interview_readiness: str

class ReportGenerationRequest(BaseModel):
    jd_analysis: RoleAnalysis
    candidate_analysis: CandidateFitAnalysis
    conversation_history: List[DialogueItem]