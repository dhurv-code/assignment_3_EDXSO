import json
import streamlit as st
from streamlit_mic_recorder import speech_to_text

from pdf_parser import extract_text_from_pdf
from interview_engine import analyze_documents, generate_next_question, generate_final_report
from schemas import DynamicQuestionRequest, DialogueItem, ReportGenerationRequest

st.set_page_config(page_title="AI Interview Accelerator", page_icon="🎯", layout="wide")

# ---------- Session state ----------
DEFAULTS = {
    "step": 1,
    "role_analysis": None,
    "candidate_analysis": None,
    "level": 1,
    "answer_count": 0,
    "conversation_history": [],
    "current_question": "",
    "report_data": None,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_app():
    for key, value in DEFAULTS.items():
        st.session_state[key] = value


def speak_button(question: str):
    # Speech is triggered by a user click, which is more reliable than browser autoplay.
    safe_question = json.dumps(question).replace("</", "<\\/")
    html = f"""
    <div style="font-family: sans-serif;">
      <button id="speakBtn" style="padding:9px 14px;border:1px solid #888;border-radius:8px;cursor:pointer;">
        🔊 Speak question
      </button>
      <script>
        const questionText = {safe_question};
        document.getElementById('speakBtn').addEventListener('click', () => {{
          if (!('speechSynthesis' in window)) {{ alert('Text-to-speech is not supported by this browser.'); return; }}
          window.speechSynthesis.cancel();
          const utterance = new SpeechSynthesisUtterance(questionText);
          utterance.lang = 'en-IN';
          window.speechSynthesis.speak(utterance);
        }});
      </script>
    </div>
    """
    st.components.v1.html(html, height=48)


st.title("🎯 AI-Powered Interview Accelerator")
st.caption("Personalized interview practice based on your job description and resume.")

with st.sidebar:
    st.markdown("### Interview Accelerator")
    st.write("**Flow**")
    st.write("1. Upload/paste JD and resume")
    st.write("2. Review job-fit analysis")
    st.write("3. Complete a 3-level interview")
    st.write("4. Review your feedback report")
    if st.button("↻ Start over", use_container_width=True):
        reset_app()
        st.rerun()

# ---------- Step 1: inputs ----------
if st.session_state.step == 1:
    st.subheader("Step 1 — Job Description and Resume")
    left, right = st.columns(2)
    with left:
        st.markdown("#### Job description")
        jd_text_input = st.text_area("Paste the job description", height=220, key="jd_text")
        jd_file = st.file_uploader("Or upload JD as PDF", type=["pdf"], key="jd_pdf")
    with right:
        st.markdown("#### Resume")
        resume_text_input = st.text_area("Paste the resume", height=220, key="resume_text")
        resume_file = st.file_uploader("Or upload resume as PDF", type=["pdf"], key="resume_pdf")

    if st.button("Analyze JD and Resume 🚀", type="primary", use_container_width=True):
        try:
            jd_text = extract_text_from_pdf(jd_file.getvalue()) if jd_file else jd_text_input.strip()
            resume_text = extract_text_from_pdf(resume_file.getvalue()) if resume_file else resume_text_input.strip()
            if not jd_text or not resume_text:
                st.error("Please provide both the job description and resume.")
            elif len(jd_text.strip()) < 40 or len(resume_text.strip()) < 40:
                st.error("One of the documents appears too short. Please provide the full text or a text-readable PDF.")
            else:
                with st.spinner("Gemini is analyzing the role and resume…"):
                    role_result, candidate_result = analyze_documents(jd_text, resume_text)
                st.session_state.role_analysis = role_result
                st.session_state.candidate_analysis = candidate_result
                st.session_state.step = 2
                st.rerun()
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
            st.info("Check that GEMINI_API_KEY is set correctly in your .env file and that the API is available.")

# ---------- Step 2: fit dashboard ----------
elif st.session_state.step == 2:
    role = st.session_state.role_analysis
    cand = st.session_state.candidate_analysis
    if not role or not cand:
        st.error("Analysis data is missing. Start over and analyze the documents again.")
        if st.button("Return to input"):
            reset_app()
            st.rerun()
    else:
        st.subheader("Step 2 — Role Fit Analysis")
        a, b = st.columns(2)
        a.metric("Target role", role.role_title)
        b.metric("Job fit score", f"{cand.job_fit_score}%", delta=cand.match_category)

        tab_role, tab_candidate = st.tabs(["Role requirements", "Candidate assessment"])
        with tab_role:
            st.markdown("#### Key responsibilities")
            st.write("\n".join(f"- {item}" for item in role.key_responsibilities) or "Not identified")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Required skills**")
                st.write(", ".join(role.required_skills) or "Not identified")
                st.markdown("**Preferred skills**")
                st.write(", ".join(role.preferred_skills) or "Not identified")
                st.markdown("**Experience expectations**")
                st.write(role.experience_expectations or "Not specified")
            with c2:
                st.markdown("**Technical competencies**")
                st.write(", ".join(role.technical_competencies) or "Not identified")
                st.markdown("**Behavioral competencies**")
                st.write(", ".join(role.behavioral_competencies) or "Not identified")
                st.markdown("**Important keywords / concepts**")
                st.write(", ".join(role.important_keywords + role.important_concepts) or "Not identified")
        with tab_candidate:
            st.markdown("#### Strong matches")
            st.success(", ".join(cand.strong_match_items) or "No strong matches identified")
            st.markdown("#### Partial matches")
            st.warning(", ".join(cand.partial_match_items) or "No partial matches identified")
            st.markdown("#### Missing or weak areas")
            st.error(", ".join(cand.missing_match_items) or "No missing areas identified")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Relevant projects**")
                st.write("\n".join(f"- {x}" for x in cand.relevant_projects) or "Not identified")
                st.markdown("**Relevant experience**")
                st.write("\n".join(f"- {x}" for x in cand.relevant_experience) or "Not identified")
            with c2:
                st.markdown("**Skills identified in resume**")
                st.write(", ".join(cand.candidate_skills) or "Not identified")
                st.markdown("**Claims to probe during interview**")
                st.write("\n".join(f"- {x}" for x in cand.suspicious_claims_to_probe) or "None identified")

        if st.button("Launch personalized interview 🎙️", type="primary", use_container_width=True):
            try:
                request = DynamicQuestionRequest(
                    jd_analysis=role,
                    candidate_analysis=cand,
                    current_level=1,
                    conversation_history=[],
                    latest_candidate_response=None,
                )
                with st.spinner("Preparing your first interview question…"):
                    first_question = generate_next_question(request)
                st.session_state.level = 1
                st.session_state.answer_count = 0
                st.session_state.conversation_history = [
                    DialogueItem(role="interviewer", text=first_question.question)
                ]
                st.session_state.current_question = first_question.question
                st.session_state.report_data = None
                st.session_state.step = 3
                st.rerun()
            except Exception as exc:
                st.error(f"Could not start interview: {exc}")

# ---------- Step 3: adaptive interview ----------
elif st.session_state.step == 3:
    level_names = {1: "Screening", 2: "Competency", 3: "Deep dive"}
    st.subheader(f"Step 3 — Level {st.session_state.level}: {level_names.get(st.session_state.level, 'Interview')}")
    st.progress(min(st.session_state.answer_count / 9, 1.0), text=f"Question {min(st.session_state.answer_count + 1, 9)} of 9")
    st.info(f"**AI interviewer:** {st.session_state.current_question}")
    speak_button(st.session_state.current_question)

    st.markdown("#### Your answer")
    st.caption("Type your answer, or use the microphone transcription control. Microphone transcription depends on browser support and permission.")
    answer_key = f"candidate_answer_{st.session_state.answer_count}"
    try:
        transcript = speech_to_text(
            language="en",
            start_prompt="🎙️ Record answer",
            stop_prompt="⏹️ Stop recording",
            just_once=True,
            key=f"speech_to_text_{st.session_state.answer_count}",
        )
        if transcript and transcript.strip():
            st.session_state[answer_key] = transcript.strip()
    except Exception as exc:
        st.warning(f"Speech input is unavailable in this browser/session. You can still type your answer. Details: {exc}")

    candidate_answer = st.text_area("Answer text", height=150, key=answer_key, label_visibility="collapsed")
    if st.button("Submit answer and continue ➜", type="primary", use_container_width=True):
        if not candidate_answer.strip():
            st.warning("Please record or type an answer before continuing.")
        else:
            st.session_state.conversation_history.append(DialogueItem(role="candidate", text=candidate_answer.strip()))
            st.session_state.answer_count += 1
            count = st.session_state.answer_count

            if count >= 9:
                try:
                    report_request = ReportGenerationRequest(
                        jd_analysis=st.session_state.role_analysis,
                        candidate_analysis=st.session_state.candidate_analysis,
                        conversation_history=st.session_state.conversation_history,
                    )
                    with st.spinner("Generating your performance report…"):
                        st.session_state.report_data = generate_final_report(report_request)
                    st.session_state.step = 4
                    st.rerun()
                except Exception as exc:
                    st.error(f"Report generation failed: {exc}")
            else:
                st.session_state.level = 1 if count < 3 else (2 if count < 6 else 3)
                request = DynamicQuestionRequest(
                    jd_analysis=st.session_state.role_analysis,
                    candidate_analysis=st.session_state.candidate_analysis,
                    current_level=st.session_state.level,
                    conversation_history=st.session_state.conversation_history,
                    latest_candidate_response=candidate_answer.strip(),
                )
                try:
                    with st.spinner("Generating a follow-up based on your answer…"):
                        next_question = generate_next_question(request)
                    st.session_state.current_question = next_question.question
                    st.session_state.conversation_history.append(
                        DialogueItem(role="interviewer", text=next_question.question)
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not generate the next question: {exc}")
                    st.info("Your answer is saved in this session. Retry by clicking the button again after checking your API connection.")

    with st.expander("View interview transcript"):
        for item in st.session_state.conversation_history:
            label = "Interviewer" if item.role == "interviewer" else "You"
            st.markdown(f"**{label}:** {item.text}")

# ---------- Step 4: results ----------
elif st.session_state.step == 4:
    report = st.session_state.report_data
    if not report:
        st.error("No report is available. Please restart the interview.")
    else:
        st.subheader("Step 4 — Interview Performance Report")
        left, right = st.columns(2)
        left.metric("Overall interview score", f"{report.overall_score}/100")
        right.metric("Interview readiness", report.interview_readiness)

        st.markdown("### Competency scores")
        if report.competency_scores:
            st.bar_chart(report.competency_scores)
            for competency, score in report.competency_scores.items():
                st.write(f"**{competency}:** {score}/100")
        else:
            st.info("No competency scores were returned.")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### Strengths")
            for item in report.strengths:
                st.success(item)
            if not report.strengths:
                st.write("No strengths were returned.")
        with c2:
            st.markdown("### Weaknesses")
            for item in report.weaknesses:
                st.warning(item)
            if not report.weaknesses:
                st.write("No weaknesses were returned.")

        st.markdown("### Prioritized preparation plan")
        for gap in report.preparation_gaps:
            with st.expander(f"Priority {gap.priority}: {gap.topic}"):
                for item in gap.review_checklist:
                    st.write(f"- {item}")

        st.markdown("### Question-level feedback")
        for index, feedback in enumerate(report.question_feedback_list, start=1):
            with st.expander(f"Question {index}: {feedback.question}"):
                st.markdown("**Your answer**")
                st.write(feedback.candidate_answer or "No answer recorded")
                st.markdown("**Assessment**")
                st.write(feedback.assessment)
                st.markdown("**What went well**")
                st.write(feedback.what_was_good)
                st.markdown("**What to improve**")
                st.write(feedback.what_could_be_better)
                st.markdown("**Ideal answer direction**")
                st.write(feedback.ideal_direction)

        if st.button("Practice another interview", type="primary", use_container_width=True):
            reset_app()
            st.rerun()
