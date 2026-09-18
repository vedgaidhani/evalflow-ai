import streamlit as st
import PyPDF2
import google.generativeai as genai
import sys
import os

# Link our new security module
sys.path.append(os.path.abspath('.'))
from modules.vision_proctor import VisionProctor

st.set_page_config(page_title="EvalFlow AI", page_icon="⚙️", layout="centered")

# --- SESSION STATE INITIALIZATION ---
if 'extracted_skills' not in st.session_state:
    st.session_state.extracted_skills = None
if 'exam_questions' not in st.session_state:
    st.session_state.exam_questions = None
if 'exam_evaluation' not in st.session_state:
    st.session_state.exam_evaluation = None
if 'proctor' not in st.session_state:
    st.session_state.proctor = VisionProctor()

# --- SIDEBAR: API CONFIGURATION ---
with st.sidebar:
    st.header("⚙️ Admin Configuration")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)

# --- MAIN UI ---
st.title("⚙️ EvalFlow AI")
st.subheader("The Automated Pre-Placement Screening Pipeline")
st.markdown("---")

# --- PHASE 0: RESUME UPLOAD ---
st.markdown("### Step 1: Candidate Authentication")
uploaded_file = st.file_uploader("Upload Technical Resume (PDF)", type=["pdf"])

if uploaded_file is not None:
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    extracted_text = "".join(page.extract_text() for page in pdf_reader.pages)
    st.success("Resume uploaded successfully!")
    
    if api_key and st.session_state.extracted_skills is None:
        if st.button("Extract Candidate Skills"):
            with st.spinner("AI is analyzing the resume..."):
                model = genai.GenerativeModel('gemini-3.6-flash')
                prompt = f"Extract the top 5 technical skills from this resume. Return ONLY a comma-separated list of the skills. Resume text: {extracted_text}"
                response = model.generate_content(prompt)
                st.session_state.extracted_skills = response.text
                st.rerun()
    elif not api_key:
        st.warning("⚠️ Please enter your Gemini API Key in the sidebar to proceed.")

# --- PHASE 1: EXAM GENERATION ---
if st.session_state.extracted_skills:
    st.info(f"**Verified Candidate Skills:** {st.session_state.extracted_skills}")
    st.markdown("---")
    st.markdown("### Step 2: Technical Assessment")
    
    if st.session_state.exam_questions is None:
        if st.button("Generate Custom Exam"):
            with st.spinner("Compiling technical assessment..."):
                model = genai.GenerativeModel('gemini-3.6-flash')
                prompt = f"""You are an HR technical recruiter for campus placements. 
                Create 3 entry-level technical interview questions for a fresh graduate based on these skills: {st.session_state.extracted_skills}. 
                Separate each question with a '|||' symbol. Do not include question numbers."""
                response = model.generate_content(prompt)
                
                questions_list = response.text.split('|||')
                st.session_state.exam_questions = [q.strip() for q in questions_list if q.strip()]
                
                # TURN ON THE SECURITY CAMERA
                st.session_state.proctor.start_proctoring()
                st.rerun()
                
# --- PHASE 1 UI: THE EXAM FORM ---
if st.session_state.exam_questions and not st.session_state.exam_evaluation:
    with st.form("exam_form"):
        st.write("⚠️ **WARNING: PROCTORING ACTIVE.** Your camera is monitoring your head movements and environment.")
        
        for i, question in enumerate(st.session_state.exam_questions):
            st.markdown(f"**Q{i+1}: {question}**")
            st.text_area(f"Answer for Q{i+1}", key=f"ans_{i}")
            
        submitted = st.form_submit_button("Submit Exam")
        if submitted:
            # TURN OFF THE CAMERA AND GET STRIKES
            penalty_seconds = st.session_state.proctor.stop_proctoring()
            
            with st.spinner("AI is grading your responses and analyzing security logs..."):
                qa_pairs = ""
                for i, q in enumerate(st.session_state.exam_questions):
                    user_answer = st.session_state[f"ans_{i}"]
                    qa_pairs += f"Q{i+1}: {q}\nCandidate Answer: {user_answer}\n\n"
                
                model = genai.GenerativeModel('gemini-3.6-flash')
                # Passing the penalty data to the AI grader
                grading_prompt = f"""You are a strict technical evaluator. 
                Review the following questions and the candidate's answers. Provide a score out of 10 for each.
                
                CRITICAL SECURITY ALERT: The candidate received {penalty_seconds} seconds of cheating penalties from the vision proctor. 
                Deduct 1 point from the Total Score for every 5 seconds of cheating. Note this deduction at the bottom of the evaluation.
                
                {qa_pairs}"""
                
                response = model.generate_content(grading_prompt)
                st.session_state.exam_evaluation = response.text
                st.rerun()

# --- PHASE 1 RESULTS ---
if st.session_state.exam_evaluation:
    st.markdown("---")
    st.markdown("### Step 3: AI Evaluation & Security Results")
    st.info(st.session_state.exam_evaluation)