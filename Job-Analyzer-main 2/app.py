import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx  # For reading .docx files
import json  # To handle JSON parsing
import time
from nlp_utils import (preprocess_text, extract_skills, calculate_similarity, 
                      get_missing_skills, TECHNICAL_SKILLS, SOFT_SKILLS)
from visualizations import (create_skill_match_chart, create_skills_radar_chart, 
                           create_missing_skills_chart)

# Replace this with your actual API key
GEMINI_API_KEY = "AIzaSyB9FSP3kO4w1y2Ao-nzK6DzrgSqjDrjXdc"

# Configure the Gemini API directly with the API key
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.0-flash")

# Helper function to extract text from a PDF
def pdf_to_text(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text()
    return text

# Helper function to extract text from a Word (.docx) file
def docx_to_text(docx_file):
    doc = docx.Document(docx_file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

# Helper function to extract text from a TXT file
def txt_to_text(txt_file):
    return txt_file.read().decode("utf-8")

# Helper function to clean the response and ensure it's valid JSON
def clean_json_response(response_text):
    # Strip backticks and any other non-JSON formatting
    cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned_text)  # Parse the cleaned text as JSON
    except json.JSONDecodeError:
        st.error("Failed to parse JSON response. The output was not valid JSON.")
        return None

# Step 1: Job description parsing using Gemini API
def parse_job_description(job_description):
    response = model.generate_content(
        f"""Extract the following information from the job description and return it in JSON format:
        1. Industry
        2. Experience (in years and level)
        3. Skills (separated into technical and soft skills)
        4. Educational requirements
        5. Job title
        6. Key responsibilities
        
        Job description:
        {job_description}
        
        Return in the following JSON format:
        {{
            "industry": "",
            "experience": {{"years": "", "level": ""}},
            "skills": {{"technical": [], "soft": []}},
            "education": "",
            "title": "",
            "responsibilities": []
        }}
        """
    )
    return clean_json_response(response.text)

# Step 2: Resume parsing using Gemini API
def parse_resume_text(resume_text):
    response = model.generate_content(
        f"""Extract the following information from the candidate's resume and return it in JSON format:
        1. Industry experience
        2. Total experience (in years and level)
        3. Skills (separated into technical and soft skills)
        4. Education
        5. Previous job titles
        6. Key achievements
        
        Resume text:
        {resume_text}
        
        Return in the following JSON format:
        {{
            "industry": "",
            "experience": {{"years": "", "level": ""}},
            "skills": {{"technical": [], "soft": []}},
            "education": "",
            "titles": [],
            "achievements": []
        }}
        """
    )
    return clean_json_response(response.text)

# Step 3: Compare job description and resume using Gemini API and enhanced NLP
def compare_job_and_resume(job_desc_json, resume_json):
    # Calculate overall similarity score using our NLP functions
    job_text = json.dumps(job_desc_json)
    resume_text = json.dumps(resume_json)
    
    # Extract skills for comparison
    job_technical_skills = job_desc_json.get('skills', {}).get('technical', [])
    job_soft_skills = job_desc_json.get('skills', {}).get('soft', [])
    resume_technical_skills = resume_json.get('skills', {}).get('technical', [])
    resume_soft_skills = resume_json.get('skills', {}).get('soft', [])
    
    # Find missing skills
    missing_technical = get_missing_skills(job_technical_skills, resume_technical_skills)
    missing_soft = get_missing_skills(job_soft_skills, resume_soft_skills)
    
    # Calculate skill match percentages
    tech_match = 0 if not job_technical_skills else (1 - len(missing_technical) / len(job_technical_skills)) * 100
    soft_match = 0 if not job_soft_skills else (1 - len(missing_soft) / len(job_soft_skills)) * 100
    
    # Overall similarity using our NLP function
    overall_similarity = calculate_similarity(job_text, resume_text)
    
    # Combine the data for the AI to use
    analysis_data = {
        "job": job_desc_json,
        "resume": resume_json,
        "similarity_scores": {
            "overall": overall_similarity,
            "technical_skills": tech_match,
            "soft_skills": soft_match
        },
        "missing_skills": {
            "technical": missing_technical,
            "soft": missing_soft
        }
    }
    
    # Get AI insights using this combined data
    response = model.generate_content(
        f"""
        Analyze the following job match data and provide:
        1. An overall FIT or NOT FIT assessment as a heading
        2. A rating out of 10 for the overall match
        3. Specific feedback on Industry match, Experience match, and Skills match
        4. 3-5 specific suggestions for improving the resume
        5. For skills, indicate which missing skills are most critical to add
        
        Analysis Data:
        {json.dumps(analysis_data, indent=2)}
        
        Format your response with clear headings and bullet points where appropriate.
        """
    )
    
    return {
        "ai_analysis": response.text,
        "similarity_data": {
            "overall": overall_similarity,
            "technical_skills": tech_match,
            "soft_skills": soft_match,
            "missing_technical": missing_technical,
            "missing_soft": missing_soft
        }
    }

# Generate resume improvement suggestions
def generate_resume_improvements(job_json, resume_json, comparison_data):
    response = model.generate_content(
        f"""
        Based on the job requirements and resume analysis, provide 5 specific, actionable improvements 
        the candidate could make to their resume to better match this job. For each suggestion:
        
        1. Explain the gap or issue
        2. Provide a specific example of how to address it
        3. If relevant, include a sample bullet point that could be added to the resume
        
        Job data: {json.dumps(job_json)}
        Resume data: {json.dumps(resume_json)}
        Comparison data: {json.dumps(comparison_data)}
        
        Format as a numbered list with clear, direct advice.
        """
    )
    return response.text

# Streamlit app with UI improvements
def main():
    st.set_page_config(page_title="Job Fit Analyzer", layout="wide")
    
    # Custom CSS
    st.markdown("""
    <style>
    .main {
        background-color: #f5f7fa;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .stButton>button {
        background-color: #3498db;
        color: white;
        border-radius: 5px;
        padding: 10px 24px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #2980b9;
    }
    .highlight {
        background-color: #e8f4f8;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    # App header with improved styling
    st.title("🎯 Job Fit Analyzer")
    st.markdown("### Analyze how well your resume matches a job description using AI")
    
    # Create tabs for a better user experience
    tab1, tab2, tab3 = st.tabs(["Input", "Analysis", "Improvement Suggestions"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📝 Job Description")
            job_description = st.text_area("Enter the job description here", height=300)
            
        with col2:
            st.markdown("### 📄 Your Resume")
            resume_file = st.file_uploader("Upload your resume (PDF, DOCX, or TXT)", 
                                         type=["pdf", "docx", "txt"])
            
        analyze_btn = st.button("Analyze Job Fit", use_container_width=True)
    
    # Store session state
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'job_json' not in st.session_state:
        st.session_state.job_json = None
    if 'resume_json' not in st.session_state:
        st.session_state.resume_json = None
    if 'comparison_result' not in st.session_state:
        st.session_state.comparison_result = None
    if 'improvements' not in st.session_state:
        st.session_state.improvements = None
    
    if analyze_btn:
        if not job_description:
            st.error("Please enter a job description.")
        if not resume_file:
            st.error("Please upload your resume.")
        
        if job_description and resume_file:
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Detect file type and extract text accordingly
            file_type = resume_file.type
            resume_text = ""
            
            status_text.text("Processing resume...")
            if file_type == "application/pdf":
                resume_text = pdf_to_text(resume_file)
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                resume_text = docx_to_text(resume_file)
            elif file_type == "text/plain":
                resume_text = txt_to_text(resume_file)
            else:
                st.error("Unsupported file format. Please upload a PDF, DOCX, or TXT file.")
                return
            
            progress_bar.progress(20)
            
            # Step 1: Parse Job Description
            status_text.text("Analyzing job description...")
            job_desc_json = parse_job_description(job_description)
            progress_bar.progress(40)
            
            # Step 2: Parse the resume
            status_text.text("Analyzing your resume...")
            resume_json = parse_resume_text(resume_text)
            progress_bar.progress(60)
            
            # Step 3: Compare Job Description and Resume
            if job_desc_json and resume_json:
                status_text.text("Comparing job requirements with your qualifications...")
                comparison_result = compare_job_and_resume(job_desc_json, resume_json)
                progress_bar.progress(80)
                
                # Step 4: Generate improvement suggestions
                status_text.text("Generating personalized suggestions...")
                improvements = generate_resume_improvements(
                    job_desc_json, resume_json, comparison_result["similarity_data"])
                progress_bar.progress(100)
                
                # Store results in session state
                st.session_state.job_json = job_desc_json
                st.session_state.resume_json = resume_json
                st.session_state.comparison_result = comparison_result
                st.session_state.improvements = improvements
                st.session_state.analysis_complete = True
                
                # Clear status
                status_text.empty()
                time.sleep(0.5)  # Slight delay before showing results
                st.rerun()  # Switch to analysis tab
    
    # Display analysis results
    if st.session_state.analysis_complete:
        with tab2:
            st.markdown("## 📊 Job Fit Analysis Results")
            
            # Display AI analysis
            if st.session_state.comparison_result:
                st.markdown("### AI Analysis")
                with st.expander("View Detailed Analysis", expanded=True):
                    st.markdown(st.session_state.comparison_result["ai_analysis"])
            
            # Display visualizations
            if st.session_state.job_json and st.session_state.resume_json and st.session_state.comparison_result:
                st.markdown("### Skills Match Visualization")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Overall match score
                    similarity_data = st.session_state.comparison_result["similarity_data"]
                    overall_score = similarity_data["overall"]
                    st.metric("Overall Match Score", f"{overall_score:.1f}%")
                    
                    # Create a skill match chart
                    job_skills = (st.session_state.job_json.get('skills', {}).get('technical', []) + 
                                 st.session_state.job_json.get('skills', {}).get('soft', []))
                    resume_skills = (st.session_state.resume_json.get('skills', {}).get('technical', []) + 
                                    st.session_state.resume_json.get('skills', {}).get('soft', []))
                    
                    match_chart = create_skill_match_chart(job_skills, resume_skills)
                    if match_chart:
                        st.plotly_chart(match_chart, use_container_width=True)
                    
                with col2:
                    # Radar chart comparing different skill categories
                    categories = ['Technical Skills', 'Soft Skills', 'Experience', 'Education']
                    
                    # Generate some sample scores for the radar chart
                    job_scores = [10, 10, 10, 10]  # Job requirements (perfect 10)
                    
                    # Resume scores based on our analysis
                    resume_scores = [
                        similarity_data["technical_skills"] / 10,
                        similarity_data["soft_skills"] / 10,
                        8,  # Placeholder for experience match
                        7   # Placeholder for education match
                    ]
                    
                    radar_chart = create_skills_radar_chart(categories, job_scores, resume_scores)
                    st.plotly_chart(radar_chart, use_container_width=True)
                
                # Missing skills analysis
                st.markdown("### Missing Skills Analysis")
                missing_technical = similarity_data["missing_technical"]
                missing_soft = similarity_data["missing_soft"]
                
                col3, col4 = st.columns(2)
                
                with col3:
                    st.markdown("#### Missing Technical Skills")
                    if missing_technical:
                        for skill in missing_technical:
                            st.markdown(f"- {skill}")
                    else:
                        st.markdown("Great job! No missing technical skills identified.")
                
                with col4:
                    st.markdown("#### Missing Soft Skills")
                    if missing_soft:
                        for skill in missing_soft:
                            st.markdown(f"- {skill}")
                    else:
                        st.markdown("Great job! No missing soft skills identified.")
        
        with tab3:
            st.markdown("## 🚀 Resume Improvement Suggestions")
            
            if st.session_state.improvements:
                st.markdown(st.session_state.improvements)
                
                st.markdown("### 📋 Action Plan")
                st.info("""
                1. Update your resume with the suggested improvements
                2. Focus on adding the missing critical skills
                3. Tailor your experience descriptions to match job requirements
                4. Reanalyze with the updated resume to check your progress
                """)

if __name__ == "__main__":
    main()
