import streamlit as st
import PyPDF2
import google.generativeai as genai
import streamlit.components.v1 as components
import sys
import os

# Link our new security module
sys.path.append(os.path.abspath('.'))
from modules.vision_proctor import VisionProctor
from modules.audio_proctor import AudioProctor
from modules.voice_interview import VoiceInterview

st.set_page_config(page_title="EvalFlow AI", page_icon="⚙️", layout="centered")
# --- UI TWEAKS: REMOVE DEFAULT PADDING ---
st.markdown(
    """
    <style>
    /* 1. Shrink top padding completely and hide Streamlit watermarks */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    header { visibility: hidden; }
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }

    /* 2. Cyber-Blue Animated Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid #00d2ff;
        background-color: transparent;
        color: #00d2ff;
        transition: all 0.3s ease;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    /* Button Hover Glowing Effect */
    .stButton > button:hover {
        background-color: #00d2ff;
        color: #040b14;
        box-shadow: 0 0 15px rgba(0, 210, 255, 0.4);
        border-color: #00d2ff;
    }

    /* 3. Sleek Input Boxes and Text Areas */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 8px;
        border: 1px solid #2a3f5f;
        background-color: #0a192f;
        color: #e6f1ff;
    }
    
    /* Neon Glow when typing in a box */
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #00d2ff;
        box-shadow: 0 0 8px rgba(0, 210, 255, 0.5);
    }

    /* 4. Custom File Uploader Dashboard */
    .stFileUploader>div>div {
        border: 1px dashed #00d2ff !important;
        border-radius: 8px;
        background-color: #0a192f;
        transition: all 0.3s ease;
    }
    .stFileUploader>div>div:hover {
        background-color: #0f2444;
        border: 1px solid #00d2ff !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

import os
if os.path.exists("logo.png"):
    # The columns help center the logo nicely
    col1, col2, col3 = st.columns([2, 1.5, 2])
    with col2:
        st.image("logo.png", use_container_width=True)
else:
    st.title("⚙️ EvalFlow AI")

# --- SESSION STATE INITIALIZATION ---
if 'extracted_skills' not in st.session_state:
    st.session_state.extracted_skills = None
if 'exam_questions' not in st.session_state:
    st.session_state.exam_questions = None
if 'exam_evaluation' not in st.session_state:
    st.session_state.exam_evaluation = None
if 'proctor' not in st.session_state:
    st.session_state.proctor = VisionProctor()
if 'audio_proctor' not in st.session_state:     
    st.session_state.audio_proctor = AudioProctor()
if 'tab_strikes' not in st.session_state:
    st.session_state.tab_strikes = 0
if 'vision_penalty' not in st.session_state:
    st.session_state.vision_penalty = 0
if 'audio_penalty' not in st.session_state:
    st.session_state.audio_penalty = 0
if 'interviewer' not in st.session_state:         #(For interview )
    st.session_state.interviewer = VoiceInterview()
if 'interview_question' not in st.session_state:
    st.session_state.interview_question = ""
if 'interview_transcript' not in st.session_state:
    st.session_state.interview_transcript = ""
if 'interview_evaluation' not in st.session_state:
    st.session_state.interview_evaluation = ""
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""

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
    st.session_state.resume_text = extracted_text
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
                st.session_state.audio_proctor.start_proctoring()
                st.rerun()
                
# --- PHASE 1 UI: THE EXAM FORM ---
if st.session_state.exam_questions and not st.session_state.exam_evaluation:
    with st.form("exam_form"):
        st.write("⚠️ **WARNING: PROCTORING ACTIVE.** Your camera and browser activity are being monitored.")
        
        # --- THE 10X JAVASCRIPT INJECTION ---
        # This hidden script listens to the browser's DOM events. 
        # If the tab loses focus (visibilitychange), it fires an inescapable alert.
        # --- THE 10X JAVASCRIPT INJECTION (AUTO-WIPE) ---
        # --- THE 10X JAVASCRIPT INJECTION (VISUAL NUKE) ---
        # --- THE 10X JAVASCRIPT INJECTION (VISUAL NUKE - FIXED) ---
        # --- THE 10X JAVASCRIPT INJECTION (VISUAL NUKE - FIXED) ---
        components.html(
            """
            <script>
            // Only add the listener once to prevent Streamlit from duplicating it
            if (!window.parent.examNukeListenerAdded) {
                window.parent.examNukeListenerAdded = true;
                
                window.parent.document.addEventListener('visibilitychange', function() {
                    if (window.parent.document.hidden) {
                        const overlay = window.parent.document.createElement('div');
                        overlay.style.cssText = 'background-color: #ff4b4b; color: white; height: 100vh; width: 100vw; display: flex; flex-direction: column; justify-content: center; align-items: center; font-family: sans-serif; z-index: 999999; position: fixed; top: 0; left: 0;';
                        overlay.innerHTML = `
                            <h1 style="font-size: 4rem; margin-bottom: 10px;">🚨 CHEATING DETECTED</h1>
                            <h3 style="font-size: 1.5rem;">Tab switching is strictly prohibited.</h3>
                            <p style="font-size: 1rem; margin-top: 30px;">Terminating exam and wiping data in 3 seconds...</p>
                        `;
                        
                        window.parent.document.body.appendChild(overlay);
                        
                        // Attach setTimeout to the PARENT window so Streamlit cannot destroy it
                        window.parent.setTimeout(function() {
                            window.parent.location.reload();
                        }, 3000);
                    }
                });
            }
            </script>
            """,
            height=0,
            width=0,
        )
        
        for i, question in enumerate(st.session_state.exam_questions):
            st.markdown(f"**Q{i+1}: {question}**")
            st.text_area(f"Answer for Q{i+1}", key=f"ans_{i}")
            
        submitted = st.form_submit_button("Submit Exam")
        if submitted:
            # TURN OFF CAMERAS/MICS AND GET PENALTIES
            vision_penalty_seconds = st.session_state.proctor.stop_proctoring()
            audio_penalty_seconds = st.session_state.audio_proctor.stop_proctoring()
            
            # Save to memory so we can show the user
            st.session_state.vision_penalty = vision_penalty_seconds
            st.session_state.audio_penalty = audio_penalty_seconds
            
            total_penalty_seconds = vision_penalty_seconds + audio_penalty_seconds
            
            with st.spinner("AI is grading your responses and analyzing security logs..."):
                qa_pairs = ""
                for i, q in enumerate(st.session_state.exam_questions):
                    user_answer = st.session_state[f"ans_{i}"]
                    qa_pairs += f"Q{i+1}: {q}\nCandidate Answer: {user_answer}\n\n"
                
                model = genai.GenerativeModel('gemini-3.6-flash')
                grading_prompt = f"""You are a strict technical evaluator. 
                Review the following questions and the candidate's answers. Provide a score out of 10 for each.
                
                CRITICAL SECURITY ALERT: The candidate received {total_penalty_seconds} seconds of cheating penalties from the vision and audio proctors. 
                Deduct 1 point from the Total Score for every 5 seconds of cheating. Note this deduction at the bottom of the evaluation.
                
                {qa_pairs}"""
                
                response = model.generate_content(grading_prompt)
                st.session_state.exam_evaluation = response.text
                st.rerun()

# --- PHASE 1 RESULTS ---
if st.session_state.exam_evaluation:
    st.markdown("---")
    st.markdown("### Step 3: AI Evaluation & Security Results")
    
    # Expose the background audio/vision logic to the UI
    col1, col2 = st.columns(2)
    with col1:
        st.error(f"👁️ **Vision Penalty:** {st.session_state.vision_penalty} seconds")
    with col2:
        st.error(f"🎤 **Audio Penalty:** {st.session_state.audio_penalty} seconds")
        
    st.info(st.session_state.exam_evaluation)

    # --- PHASE 2: LIVE VOICE INTERVIEW ---
if st.session_state.exam_evaluation and not st.session_state.interview_evaluation:
    st.markdown("---")
    st.markdown("### Step 4: Live AI Voice Interview")
    st.warning("Ensure your speakers are on and your microphone is ready. The AI will speak a question, and you will have 10 seconds to answer out loud.")
    
    if st.button("Start Live Interview"):
        with st.spinner("AI is generating your technical interview question..."):
            model = genai.GenerativeModel('gemini-3.6-flash')
            
            # 1. Generate a tough question based on the resume
            prompt = f"Based on this resume: {st.session_state.resume_text}. Generate ONE highly technical, challenging interview question to test their actual knowledge. Do not include any formatting, just the question text."
            question_response = model.generate_content(prompt)
            st.session_state.interview_question = question_response.text
            
            st.info(f"**AI Asks:** {st.session_state.interview_question}")
            
            # 2. Speak the question out loud!
            st.session_state.interviewer.speak(st.session_state.interview_question)
            
            # 3. Record the user's verbal answer
            st.write("🎤 **RECORDING YOUR ANSWER NOW... (10 Seconds)**")
            # Force the UI to update so the user sees the recording message
            st.empty() 
            
            audio_file = st.session_state.interviewer.record_audio_to_file(duration=10)
            
            # 4. Transcribe the audio
            st.write("🧠 Transcribing your answer...")
            transcript = st.session_state.interviewer.transcribe_audio(audio_file)
            st.session_state.interview_transcript = transcript
            st.rerun()

# --- PHASE 2 RESULTS ---
if st.session_state.interview_transcript and not st.session_state.interview_evaluation:
    st.markdown("---")
    st.success(f"**Your Transcribed Answer:** {st.session_state.interview_transcript}")
    
    # --- THE UX UPGRADE: AUTO-GRADING ---
    # No more clicking a button! It grades instantly.
    with st.spinner("AI is analyzing your voice response and making the final Hire / No Hire decision..."):
        model = genai.GenerativeModel('gemini-1.5-flash')
        eval_prompt = f"""You are the final Hiring Manager. 
        The candidate was asked: "{st.session_state.interview_question}"
        Their verbal answer was transcribed as: "{st.session_state.interview_transcript}"
        
        Evaluate their answer for technical accuracy. Give a final score out of 10 for the interview.
        End your evaluation with a bolded FINAL DECISION: [HIRE or NO HIRE]."""
        
        final_eval = model.generate_content(eval_prompt)
        st.session_state.interview_evaluation = final_eval.text
        st.rerun()

if st.session_state.interview_evaluation:
    st.markdown("---")
    st.markdown("### 🏆 FINAL VERDICT")
    st.info(st.session_state.interview_evaluation)
    
    # Give them a button to restart the whole app and test again
    if st.button("End Session & Restart Pipeline"):
        st.session_state.clear()
        st.rerun()