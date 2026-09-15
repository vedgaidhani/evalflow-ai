import streamlit as st
import PyPDF2
import google.generativeai as genai

st.set_page_config(page_title="EvalFlow AI", page_icon="⚙️", layout="centered")

# 1. Secure API Configuration in Sidebar
with st.sidebar:
    st.header("⚙️ Admin Configuration")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)

# 2. Main UI Header
st.title("⚙️ EvalFlow AI")
st.subheader("The Automated Pre-Placement Screening Pipeline")
st.markdown("---")

# 3. Phase 0: Resume Upload
st.markdown("### Step 1: Candidate Authentication")
uploaded_file = st.file_uploader("Upload Technical Resume (PDF)", type=["pdf"])

if uploaded_file is not None:
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    extracted_text = "".join(page.extract_text() for page in pdf_reader.pages)
    
    st.success("Resume uploaded successfully!")
    
    # 4. Phase 1: Skill Extraction via Gemini
    if api_key:
        if st.button("Extract Candidate Skills"):
            with st.spinner("AI is analyzing the resume..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"Extract the top 5 technical skills from this resume. Return ONLY a comma-separated list of the skills. Resume text: {extracted_text}"
                response = model.generate_content(prompt)
                st.info(f"**Detected Skills:** {response.text}")
    else:
        st.warning("⚠️ Please enter your Gemini API Key in the sidebar to proceed.")