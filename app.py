import streamlit as st
import json
from pdf_parser import extract_text_from_pdf
from interview_engine import analyze_documents, generate_next_question, generate_final_report
from schemas import (
    RoleAnalysis, CandidateFitAnalysis, DynamicQuestionRequest,
    DialogueItem, ReportGenerationRequest
)

st.set_page_config(page_title="AI Interview Accelerator", page_icon="🎯", layout="wide")

# Initialize Session States
if "step" not in st.session_state:
    st.session_state.step = 1
if "role_analysis" not in st.session_state:
    st.session_state.role_analysis = None
if "candidate_analysis" not in st.session_state:
    st.session_state.candidate_analysis = None
if "level" not in st.session_state:
    st.session_state.level = 1
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "current_question" not in st.session_state:
    st.session_state.current_question = ""
if "report_data" not in st.session_state:
    st.session_state.report_data = None

st.title("🎯 AI-Powered Interview Accelerator")

# -------------------------------------------------------------------
# STEP 1: INPUT JD & RESUME
# -------------------------------------------------------------------
if st.session_state.step == 1:
    st.subheader("Step 1: Input Job Description & Resume")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Job Description")
        jd_text_input = st.text_area("Paste Job Description Text", height=200)
        jd_file_input = st.file_uploader("OR Upload Job Description (PDF)", type=["pdf"])

    with col2:
        st.markdown("### Candidate Resume")
        resume_text_input = st.text_area("Paste Resume Text", height=200)
        resume_file_input = st.file_uploader("OR Upload Resume (PDF)", type=["pdf"])

    if st.button("Start AI Analysis 🚀", use_container_width=True):
        jd_text = ""
        resume_text = ""

        if jd_file_input:
            jd_text = extract_text_from_pdf(jd_file_input.read())
        elif jd_text_input:
            jd_text = jd_text_input

        if resume_file_input:
            resume_text = extract_text_from_pdf(resume_file_input.read())
        elif resume_text_input:
            resume_text = resume_text_input

        if not jd_text or not resume_text:
            st.error("Please provide both Job Description and Resume.")
        else:
            with st.spinner("Analyzing alignment..."):
                role_res, candidate_res = analyze_documents(jd_text, resume_text)
                st.session_state.role_analysis = role_res
                st.session_state.candidate_analysis = candidate_res
                st.session_state.step = 2
                st.rerun()

# -------------------------------------------------------------------
# STEP 2: DASHBOARD & FIT BREAKDOWN
# -------------------------------------------------------------------
elif st.session_state.step == 2:
    st.subheader("Step 2: Role Fit Analysis & Breakdown")
    
    role = st.session_state.role_analysis
    cand = st.session_state.candidate_analysis

    # Metrics
    m1, m2 = st.columns(2)
    m1.metric("Target Role", role.role_title)
    m2.metric("Job Fit Score", f"{cand.job_fit_score}%", delta=cand.match_category)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Required Skills & Competencies")
        st.write("**Required:**", ", ".join(role.required_skills))
        st.write("**Technical Competencies:**", ", ".join(role.technical_competencies))
        st.write("**Behavioral Competencies:**", ", ".join(role.behavioral_competencies))

    with c2:
        st.markdown("### Match Assessment")
        st.success(f"**Strong Match:** {', '.join(cand.strong_match_items)}")
        st.warning(f"**Partial Match:** {', '.join(cand.partial_match_items)}")
        st.error(f"**Missing / Weak:** {', '.join(cand.missing_match_items)}")

    if st.button("Launch AI Interview Simulator 🎙️", use_container_width=True):
        req = DynamicQuestionRequest(
            jd_analysis=role,
            candidate_analysis=cand,
            current_level=1,
            conversation_history=[],
            latest_candidate_response=None
        )
        first_q = generate_next_question(req)
        st.session_state.current_question = first_q.question
        st.session_state.conversation_history.append(DialogueItem(role="interviewer", text=first_q.question))
        st.session_state.step = 3
        st.rerun()

# -------------------------------------------------------------------
# STEP 3: VOICE & TEXT INTERVIEW SIMULATOR
# -------------------------------------------------------------------
elif st.session_state.step == 3:
    st.subheader(f"Step 3: Level {st.session_state.level} AI Interview Simulator")

    # Browser TTS via JS
    tts_js = f"""
    <script>
        var msg = new SpeechSynthesisUtterance("{st.session_state.current_question}");
        window.speechSynthesis.speak(msg);
    </script>
    """
    st.components.v1.html(tts_js, height=0)

    st.info(f"**AI Interviewer:** {st.session_state.current_question}")

    st.markdown("---")
    candidate_answer = st.text_area("Your Response (Type or Use Dictation):", height=120)

    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("Submit Response ➔", use_container_width=True):
            if candidate_answer.strip():
                st.session_state.conversation_history.append(
                    DialogueItem(role="candidate", text=candidate_answer)
                )

                hist_len = len(st.session_state.conversation_history)
                if hist_len >= 6 and st.session_state.level == 1:
                    st.session_state.level = 2
                elif hist_len >= 12 and st.session_state.level == 2:
                    st.session_state.level = 3

                if hist_len >= 18:
                    with st.spinner("Compiling Final Evaluation Report..."):
                        rep_req = ReportGenerationRequest(
                            jd_analysis=st.session_state.role_analysis,
                            candidate_analysis=st.session_state.candidate_analysis,
                            conversation_history=st.session_state.conversation_history
                        )
                        st.session_state.report_data = generate_final_report(rep_req)
                        st.session_state.step = 4
                        st.rerun()

                with st.spinner("Generating next dynamic response..."):
                    req = DynamicQuestionRequest(
                        jd_analysis=st.session_state.role_analysis,
                        candidate_analysis=st.session_state.candidate_analysis,
                        current_level=st.session_state.level,
                        conversation_history=st.session_state.conversation_history,
                        latest_candidate_response=candidate_answer
                    )
                    next_q = generate_next_question(req)
                    st.session_state.current_question = next_q.question
                    st.session_state.conversation_history.append(
                        DialogueItem(role="interviewer", text=next_q.question)
                    )
                    st.rerun()

# -------------------------------------------------------------------
# STEP 4: PERFORMANCE & READINESS REPORT
# -------------------------------------------------------------------
elif st.session_state.step == 4:
    st.subheader("Step 4: Interview Performance Report")
    rep = st.session_state.report_data

    m1, m2 = st.columns(2)
    m1.metric("Interview Readiness Assessment", rep.interview_readiness)
    m2.metric("Overall Performance Score", f"{rep.overall_score}/100")

    st.markdown("### Prioritized Preparation Plan")
    for gap in rep.preparation_gaps:
        with st.expander(f"Priority {gap.priority}: {gap.topic}"):
            for item in gap.review_checklist:
                st.write(f"- {item}")

    st.markdown("### Detailed Question Feedback")
    for fb in rep.question_feedback_list:
        with st.container():
            st.write(f"**Q:** {fb.question}")
            st.caption(f"**Your Answer:** {fb.candidate_answer}")
            st.success(f"**Strengths:** {fb.what_was_good}")
            st.warning(f"**Areas to Improve:** {fb.what_could_be_better}")
            st.info(f"**Ideal Direction:** {fb.ideal_direction}")
            st.markdown("---")