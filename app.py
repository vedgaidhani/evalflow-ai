import streamlit as st
import PyPDF2
import google.generativeai as genai

st.set_page_config(page_title="EvalFlow AI", page_icon="⚙️", layout="centered")

# --- SESSION STATE INITIALIZATION ---
# This is crucial. It tells the app to remember these variables even when the page refreshes.
if 'extracted_skills' not in st.session_state:
    st.session_state.extracted_skills = None
if 'exam_evaluation' not in st.session_state:
    st.session_state.exam_evaluation = None

if 'exam_questions' not in st.session_state:
    st.session_state.exam_questions = None
if 'exam_evaluation' not in st.session_state:
    st.session_state.exam_evaluation = None

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
    
    # Extract Skills Button
    if api_key and st.session_state.extracted_skills is None:
        if st.button("Extract Candidate Skills"):
            with st.spinner("AI is analyzing the resume..."):
                model = genai.GenerativeModel('gemini-3.6-flash')
                prompt = f"Extract the top 5 technical skills from this resume. Return ONLY a comma-separated list of the skills. Resume text: {extracted_text}"
                response = model.generate_content(prompt)
                
                # Save the skills to memory!
                st.session_state.extracted_skills = response.text
                st.rerun() # Force the page to refresh and show the next step

    elif not api_key:
        st.warning("⚠️ Please enter your Gemini API Key in the sidebar to proceed.")

# --- PHASE 1: EXAM GENERATION ---
# This section only appears AFTER skills are saved in memory
if st.session_state.extracted_skills:

    st.info(f"**Verified Candidate Skills:** {st.session_state.extracted_skills}")
    st.markdown("---")
    st.markdown("### Step 2: Technical Assessment")
    
    # Generate Exam Button
    if st.session_state.exam_questions is None:

            
        if st.button("Generate Custom Exam"):
            with st.spinner("Compiling technical assessment..."):
                model = genai.GenerativeModel('gemini-3.6-flash')
                # We ask Gemini to format the output with specific separators so we can split it into a Python list
                # The Calibrated Prompt
                prompt = f"""You are an HR technical recruiter for campus placements. 
                Create 3 entry-level, fundamental technical interview questions for a fresh college graduate based on these skills: {st.session_state.extracted_skills}. 
                The questions must be simple, testing basic concepts and definitions only. Do not ask about enterprise architecture.
                Separate each question with a '|||' symbol. Do not include question numbers."""
                response = model.generate_content(prompt)
                
                # Split the text into a list of actual questions and save to memory
                questions_list = response.text.split('|||')
                st.session_state.exam_questions = [q.strip() for q in questions_list if q.strip()]
                st.rerun()
                
# --- PHASE 1 UI: THE EXAM FORM ---
# The 'and not' ensures the form disappears after grading is complete
if st.session_state.exam_questions and not st.session_state.exam_evaluation:
    with st.form("exam_form"):
        st.write("Please answer the following technical questions. (Proctoring will be active during this phase).")
        
        # Create text boxes dynamically
        for i, question in enumerate(st.session_state.exam_questions):
            st.markdown(f"**Q{i+1}: {question}**")
            st.text_area(f"Answer for Q{i+1}", key=f"ans_{i}")
            
        submitted = st.form_submit_button("Submit Exam")
        if submitted:
            with st.spinner("AI is grading your responses..."):
                # Gather the questions and the candidate's typed answers
                qa_pairs = ""
                for i, q in enumerate(st.session_state.exam_questions):
                    user_answer = st.session_state[f"ans_{i}"]
                    qa_pairs += f"Q{i+1}: {q}\nCandidate Answer: {user_answer}\n\n"
                
                # Ask Gemini to grade the answers
                model = genai.GenerativeModel('gemini-2.5-flash')
                grading_prompt = f"""You are a strict technical evaluator. 
                Review the following questions and the candidate's answers. 
                Provide a score out of 10 for each answer, and a brief 1-sentence feedback explaining why.
                At the end, provide a Total Score out of 30.
                
                {qa_pairs}"""
                
                response = model.generate_content(grading_prompt)
                
                # Save the final grade to memory and refresh the UI
                st.session_state.exam_evaluation = response.text
                st.rerun()

# --- PHASE 1 RESULTS ---
if st.session_state.exam_evaluation:
    st.markdown("---")
    st.markdown("### Step 3: AI Evaluation Results")
    st.info(st.session_state.exam_evaluation)