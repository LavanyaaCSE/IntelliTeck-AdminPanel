import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from datetime import datetime, timedelta
import os
import json

# Page config
st.set_page_config(
    page_title="IntelliTrain Admin Panel",
    page_icon="📚",
    layout="wide"
)

# Initialize Firebase Admin (only once)
@st.cache_resource
def init_firebase():
    cred_dict = None
    
    # 1. Check for Local File FIRST (Avoids Streamlit Secrets warning when running locally)
    if os.path.exists("firebase-admin-key.json"):
        with open("firebase-admin-key.json") as f:
            cred_dict = json.load(f)
            
    # 2. Try Env Var
    elif "FIREBASE_SERVICE_ACCOUNT" in os.environ:
        cred_dict = json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])

    # 3. Try Streamlit Secrets (for Cloud deployment only)
    else:
        try:
            if "firebase" in st.secrets:
                cred_dict = dict(st.secrets["firebase"])
        except:
            pass

    if not cred_dict:
        st.error("❌ Firebase credentials missing!")
        st.info("Please ensure `firebase-admin-key.json` exists in this folder.")
        st.stop()

    # Initialize Firebase Admin (only once)
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)

    # Use the specific database name 'intellitrain'
    from google.cloud import firestore as google_firestore
    from google.oauth2 import service_account
    
    google_creds = service_account.Credentials.from_service_account_info(cred_dict)
    return google_firestore.Client(
        credentials=google_creds, 
        project=google_creds.project_id, 
        database='intellitrain'
    )

db = init_firebase()

# Sidebar
st.sidebar.title("🎓 IntelliTrain Admin")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", ["📋 View Assessments", "➕ Add Assessment", "⏰ Upcoming Tests", "✏️ Edit Questions", "📊 Upload CSV", "💼 Manage Jobs"])

# Main content
st.title("IntelliTrain Assessment Manager")

if page == "📋 View Assessments":
    st.header("All Assessments")
    
    # Fetch assessments from Firestore
    assessments_ref = db.collection('assessments')
    docs = assessments_ref.stream()
    
    assessments = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        assessments.append(data)
    
    if assessments:
        for assessment in assessments:
            with st.expander(f"📝 {assessment['title']} ({len(assessment.get('questions', []))} questions)"):
                col1, col2, col3 = st.columns(3)
                col1.metric("Category", assessment['category'])
                col2.metric("Duration", f"{assessment['durationMinutes']} mins")
                col3.metric("Questions", len(assessment.get('questions', [])))
                
                st.subheader("Questions:")
                for i, q in enumerate(assessment.get('questions', []), 1):
                    st.markdown(f"**Q{i}:** {q['text']}")
                    st.write(f"Options: {', '.join(q['options'])}")
                    st.write(f"✅ Correct: {q['options'][q['correctOptionIndex']]}")
                    st.write(f"📌 Concept: {q['concept']} | Difficulty: {q['difficulty']}")
                    st.markdown("---")
    else:
        st.info("No assessments found. Add one using the sidebar!")

elif page == "➕ Add Assessment":
    st.header("Create New Assessment")
    
    with st.form("new_assessment"):
        assessment_id = st.text_input("Assessment ID", placeholder="e.g., 4")
        title = st.text_input("Title", placeholder="e.g., Python Programming Test")
        category = st.selectbox("Category", ["Technical", "Aptitude", "Reasoning", "Verbal"])
        duration = st.number_input("Duration (minutes)", min_value=10, max_value=180, value=60)
        
        st.subheader("Add Questions")
        num_questions = st.number_input("Number of questions to add", min_value=1, max_value=20, value=3)
        
        questions = []
        for i in range(num_questions):
            st.markdown(f"### Question {i+1}")
            q_text = st.text_area(f"Question {i+1} Text", key=f"q_text_{i}")
            
            col1, col2 = st.columns(2)
            opt1 = col1.text_input(f"Option A", key=f"opt1_{i}")
            opt2 = col2.text_input(f"Option B", key=f"opt2_{i}")
            opt3 = col1.text_input(f"Option C", key=f"opt3_{i}")
            opt4 = col2.text_input(f"Option D", key=f"opt4_{i}")
            
            correct = st.selectbox(f"Correct Answer", ["A", "B", "C", "D"], key=f"correct_{i}")
            concept = st.text_input(f"Concept", key=f"concept_{i}")
            difficulty = st.selectbox(f"Difficulty", ["Easy", "Medium", "Hard"], key=f"diff_{i}")
            section = st.text_input(f"Section", value=category, key=f"section_{i}")
            
            questions.append({
                'id': f'q_{assessment_id}_{i+1}',
                'text': q_text,
                'options': [opt1, opt2, opt3, opt4],
                'correctOptionIndex': ord(correct) - ord('A'),
                'concept': concept,
                'difficulty': difficulty,
                'section': section
            })
        
        submitted = st.form_submit_button("Create Assessment")
        
        if submitted:
            if assessment_id and title:
                assessment_data = {
                    'title': title,
                    'category': category,
                    'durationMinutes': duration,
                    'questions': questions
                }
                
                db.collection('assessments').document(assessment_id).set(assessment_data)
                st.success(f"✅ Assessment '{title}' created successfully!")
                st.balloons()
            else:
                st.error("Please fill in Assessment ID and Title")

elif page == "⏰ Upcoming Tests":
    st.header("Schedule Upcoming Tests")
    
    tab1, tab2 = st.tabs(["📅 View Scheduled", "➕ Schedule New"])
    
    with tab1:
        st.subheader("Currently Scheduled Tests")
        upcoming_ref = db.collection('upcoming_tests')
        docs = upcoming_ref.stream()
        
        upcoming_tests = []
        for doc in docs:
            t_data = doc.to_dict()
            t_data['id'] = doc.id
            upcoming_tests.append(t_data)
        
        if upcoming_tests:
            # Sort by startTime for view
            upcoming_tests.sort(key=lambda x: x.get('startTime', datetime.now()))
            
            for test in upcoming_tests:
                start = test.get('startTime')
                end = test.get('endTime')
                
                # Format times for display if they are datetime objects and convert to local
                start_str = start.astimezone().strftime("%d %b, %H:%M") if hasattr(start, 'astimezone') else str(start)
                end_str = end.astimezone().strftime("%d %b, %H:%M") if hasattr(end, 'astimezone') else str(end)
                
                with st.expander(f"📌 {test['title']} ({start_str})"):
                    col1, col2 = st.columns(2)
                    col1.write(f"**Category:** {test.get('category')}")
                    col1.write(f"**Duration:** {test.get('durationMinutes')} mins")
                    col1.write(f"**Status:** {'🟢 Published' if test.get('isPublished') else '🔴 Draft'}")
                    
                    col2.write(f"**Starts:** {start_str}")
                    col2.write(f"**Ends:** {end_str}")
                    
                    st.divider()
                    st.write(f"**Questions ({len(test.get('questions', []))})**")
                    for i, q in enumerate(test.get('questions', []), 1):
                        st.write(f"{i}. {q['text']}")
                    
                    if st.button(f"🗑️ Delete {test['title']}", key=f"del_test_{test['id']}"):
                        db.collection('upcoming_tests').document(test['id']).delete()
                        st.success("Test deleted!")
                        st.rerun()
        else:
            st.info("No tests scheduled yet.")

    with tab2:
        st.subheader("Schedule a New Test")
        
        with st.form("schedule_test"):
            t_title = st.text_input("Test Title", placeholder="e.g., Weekly Technical Sprint")
            t_cat = st.selectbox("Category", ["Technical", "General"])
            t_desc = st.text_area("Description", placeholder="What is this test about?")
            
            c1, c2 = st.columns(2)
            s_date = c1.date_input("Start Date", value=datetime.now().date())
            s_time = c1.time_input("Start Time", value=datetime.now().time())
            
            e_date = c2.date_input("End Date", value=datetime.now().date())
            e_time = c2.time_input("End Time", value=(datetime.now() + timedelta(hours=2)).time())
            
            t_dur = st.number_input("Duration (Minutes)", min_value=1, value=30)
            t_topics = st.text_input("Topics (comma separated)", placeholder="Python, SQL, Logic")
            t_pub = st.checkbox("Publish Immediately", value=True)
            
            st.divider()
            st.subheader("Add Questions")
            num_q = st.number_input("Number of questions", min_value=1, max_value=20, value=3, key="upcoming_num_q")
            
            upcoming_questions = []
            for i in range(num_q):
                st.markdown(f"**Question {i+1}**")
                uq_text = st.text_area(f"Text", key=f"upcoming_q_text_{i}")
                
                c1, c2 = st.columns(2)
                uo1 = c1.text_input(f"Option A", key=f"upcoming_opt1_{i}")
                uo2 = c2.text_input(f"Option B", key=f"upcoming_opt2_{i}")
                uo3 = c1.text_input(f"Option C", key=f"upcoming_opt3_{i}")
                uo4 = c2.text_input(f"Option D", key=f"upcoming_opt4_{i}")
                
                ucorrect = st.selectbox(f"Correct", ["A", "B", "C", "D"], key=f"upcoming_correct_{i}")
                uconcept = st.text_input(f"Concept", key=f"upcoming_concept_{i}")
                udiff = st.selectbox(f"Difficulty", ["Easy", "Medium", "Hard"], key=f"upcoming_diff_{i}")
                
                upcoming_questions.append({
                    'id': f'uq_{i+1}_{datetime.now().strftime("%Y%m%d%H%M")}',
                    'text': uq_text,
                    'options': [uo1, uo2, uo3, uo4],
                    'correctOptionIndex': ord(ucorrect) - ord('A'),
                    'concept': uconcept,
                    'difficulty': udiff,
                    'section': t_cat
                })
            
            t_submit = st.form_submit_button("Schedule Test & Add Questions")
            
            if t_submit:
                if t_title:
                    # Combine into datetime objects and attach local timezone
                    start_dt = datetime.combine(s_date, s_time).astimezone()
                    end_dt = datetime.combine(e_date, e_time).astimezone()
                    
                    new_test_data = {
                        "title": t_title,
                        "category": t_cat,
                        "description": t_desc,
                        "startTime": start_dt,
                        "endTime": end_dt,
                        "durationMinutes": int(t_dur),
                        "topics": [t.strip() for t in t_topics.split(",") if t.strip()],
                        "questions": upcoming_questions,
                        "isPublished": t_pub
                    }
                    
                    db.collection('upcoming_tests').add(new_test_data)
                    st.success(f"✅ Test '{t_title}' has been scheduled!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Title is required!")

elif page == "✏️ Edit Questions":
    st.header("Edit Existing Questions")
    
    # Fetch assessments
    assessments_ref = db.collection('assessments')
    docs = assessments_ref.stream()
    
    assessment_titles = {}
    for doc in docs:
        data = doc.to_dict()
        assessment_titles[doc.id] = data['title']
    
    if assessment_titles:
        selected_id = st.selectbox("Select Assessment", list(assessment_titles.keys()), 
                                   format_func=lambda x: f"{x}: {assessment_titles[x]}")
        
        if selected_id:
            doc = db.collection('assessments').document(selected_id).get()
            assessment = doc.to_dict()
            
            st.subheader(f"Editing: {assessment['title']}")
            
            questions = assessment.get('questions', [])
            
            for i, q in enumerate(questions):
                with st.expander(f"Question {i+1}: {q['text'][:50]}..."):
                    new_text = st.text_area("Question Text", value=q['text'], key=f"edit_text_{i}")
                    
                    col1, col2 = st.columns(2)
                    new_opts = []
                    new_opts.append(col1.text_input("Option A", value=q['options'][0], key=f"edit_opt1_{i}"))
                    new_opts.append(col2.text_input("Option B", value=q['options'][1], key=f"edit_opt2_{i}"))
                    new_opts.append(col1.text_input("Option C", value=q['options'][2], key=f"edit_opt3_{i}"))
                    new_opts.append(col2.text_input("Option D", value=q['options'][3], key=f"edit_opt4_{i}"))
                    
                    correct_idx = st.selectbox("Correct Answer", [0, 1, 2, 3], 
                                              index=q['correctOptionIndex'],
                                              format_func=lambda x: f"{chr(65+x)}: {new_opts[x]}",
                                              key=f"edit_correct_{i}")
                    
                    new_concept = st.text_input("Concept", value=q['concept'], key=f"edit_concept_{i}")
                    new_diff = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], 
                                           index=["Easy", "Medium", "Hard"].index(q['difficulty']),
                                           key=f"edit_diff_{i}")
                    
                    col_update, col_delete = st.columns(2)
                    if col_update.button(f"Update Question {i+1}", key=f"update_{i}"):
                        questions[i] = {
                            'id': q['id'],
                            'text': new_text,
                            'options': new_opts,
                            'correctOptionIndex': correct_idx,
                            'concept': new_concept,
                            'difficulty': new_diff,
                            'section': q['section']
                        }
                        
                        db.collection('assessments').document(selected_id).update({'questions': questions})
                        st.success(f"✅ Question {i+1} updated!")
                        st.rerun()
                    
                    if col_delete.button(f"🗑️ Delete", key=f"delete_{i}"):
                        questions.pop(i)
                        db.collection('assessments').document(selected_id).update({'questions': questions})
                        st.success(f"✅ Question {i+1} deleted!")
                        st.rerun()
            
            # Add New Question Section
            st.markdown("---")
            st.subheader("➕ Add New Question")
            
            with st.form(f"add_question_{selected_id}"):
                new_q_text = st.text_area("Question Text", placeholder="Enter your question here...")
                
                col1, col2 = st.columns(2)
                new_opt1 = col1.text_input("Option A")
                new_opt2 = col2.text_input("Option B")
                new_opt3 = col1.text_input("Option C")
                new_opt4 = col2.text_input("Option D")
                
                new_correct = st.selectbox("Correct Answer", ["A", "B", "C", "D"])
                new_concept = st.text_input("Concept")
                new_difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
                new_section = st.text_input("Section", value=assessment['category'])
                
                add_submitted = st.form_submit_button("Add Question")
                
                if add_submitted:
                    if new_q_text and new_opt1 and new_opt2 and new_opt3 and new_opt4:
                        new_question = {
                            'id': f'q_{selected_id}_{len(questions)+1}',
                            'text': new_q_text,
                            'options': [new_opt1, new_opt2, new_opt3, new_opt4],
                            'correctOptionIndex': ord(new_correct) - ord('A'),
                            'concept': new_concept,
                            'difficulty': new_difficulty,
                            'section': new_section
                        }
                        
                        questions.append(new_question)
                        db.collection('assessments').document(selected_id).update({'questions': questions})
                        st.success(f"✅ New question added! Total questions: {len(questions)}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Please fill in all fields!")
    else:
        st.info("No assessments found.")

elif page == "📊 Upload CSV":
    st.header("Bulk Upload via CSV")
    
    st.markdown("""
    ### CSV Format
    Your CSV should have these columns:
    - `assessment_id`: ID of the assessment
    - `question_text`: The question
    - `option_a`, `option_b`, `option_c`, `option_d`: The four options
    - `correct_answer`: Letter of correct answer (A, B, C, or D)
    - `concept`: Topic/concept
    - `difficulty`: Easy, Medium, or Hard
    - `section`: Section name
    """)
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df)
        
        if st.button("Upload to Firebase"):
            # Group by assessment_id
            for assessment_id in df['assessment_id'].unique():
                assessment_df = df[df['assessment_id'] == assessment_id]
                
                questions = []
                for idx, row in assessment_df.iterrows():
                    questions.append({
                        'id': f'q_{assessment_id}_{idx}',
                        'text': row['question_text'],
                        'options': [row['option_a'], row['option_b'], row['option_c'], row['option_d']],
                        'correctOptionIndex': ord(row['correct_answer'].upper()) - ord('A'),
                        'concept': row['concept'],
                        'difficulty': row['difficulty'],
                        'section': row['section']
                    })
                
                # Check if assessment exists
                doc_ref = db.collection('assessments').document(str(assessment_id))
                doc = doc_ref.get()
                
                if doc.exists:
                    # Update questions
                    doc_ref.update({'questions': questions})
                    st.success(f"✅ Updated assessment {assessment_id}")
                else:
                    st.warning(f"⚠️ Assessment {assessment_id} doesn't exist. Create it first in 'Add Assessment' page.")
            
            st.balloons()

elif page == "💼 Manage Jobs":
    st.header("Job Postings Manager")
    
    tab1, tab2 = st.tabs(["📋 View Jobs", "➕ Add Job"])
    
    with tab1:
        st.subheader("Current Job Openings")
        jobs_ref = db.collection('jobs')
        docs = jobs_ref.stream()
        
        jobs = []
        for doc in docs:
            j_data = doc.to_dict()
            j_data['id'] = doc.id
            jobs.append(j_data)
        
        if jobs:
            # Sort by timestamp if available
            jobs.sort(key=lambda x: x.get('timestamp', datetime.now()), reverse=True)
            
            for job in jobs:
                with st.expander(f"🏢 {job.get('title')} at {job.get('company')}"):
                    col1, col2 = st.columns(2)
                    col1.write(f"**Location:** {job.get('location')}")
                    col1.write(f"**Type:** {job.get('type')}")
                    col1.write(f"**Mode:** {job.get('mode')}")
                    
                    col2.write(f"**Posted On:** {job.get('postedDate')}")
                    if job.get('link'):
                        col2.write(f"**Link:** [Apply Now]({job.get('link')})")
                    
                    st.divider()
                    st.write("**Description:**")
                    st.write(job.get('description'))
                    
                    if st.button(f"🗑️ Delete Job", key=f"del_job_{job['id']}"):
                        db.collection('jobs').document(job['id']).delete()
                        st.success("Job deleted!")
                        st.rerun()
        else:
            st.info("No jobs found. Add one using the 'Add Job' tab!")

    with tab2:
        st.subheader("Add a New Job Posting")
        
        # Link to prompt user for LinkedIn URL
        st.info("💡 You can manually enter details or paste a LinkedIn Job URL to try and auto-fill.")
        
        li_url_input = st.text_input("LinkedIn Job URL (for reference or auto-fill)")
        
        if st.button("Attempt Auto-fill"):
            if li_url_input:
                st.warning("LinkedIn often blocks direct fetching. I'll attempt to extract basic info from the URL.")
                # Basic parsing from URL slugs if possible
                # Example: https://www.linkedin.com/jobs/view/software-engineer-at-company-12345/
                if "linkedin.com/jobs/view/" in li_url_input:
                    try:
                        slug = li_url_input.split("/view/")[1].split("/")[0]
                        parts = slug.split("-at-")
                        if len(parts) > 1:
                            st.session_state['auto_title'] = parts[0].replace("-", " ").title()
                            st.session_state['auto_company'] = parts[1].replace("-", " ").title()
                            st.success(f"Extracted: {st.session_state['auto_title']} at {st.session_state['auto_company']}")
                        else:
                            # Try other format: software-engineer-company-12345
                            title_parts = parts[0].split("-")
                            st.session_state['auto_title'] = " ".join(title_parts[:-1]).title()
                            st.success(f"Extracted: {st.session_state['auto_title']}")
                    except Exception as e:
                        st.error(f"Error parsing URL: {str(e)}")
                else:
                    st.error("Could not auto-fill. Please enter manually.")
            else:
                st.error("Please enter a URL first!")

        with st.form("add_job_form"):
            default_title = st.session_state.get('auto_title', "")
            default_company = st.session_state.get('auto_company', "")
            
            j_title = st.text_input("Job Title", value=default_title, placeholder="e.g., Software Engineer")
            j_company = st.text_input("Company Name", value=default_company, placeholder="e.g., Google")
            j_location = st.text_input("Location", placeholder="e.g., Mountain View, CA")
            
            c1, c2 = st.columns(2)
            j_type = c1.selectbox("Job Type", ["Full-time", "Part-time", "Contract", "Internship"])
            j_mode = c2.selectbox("Work Mode", ["Remote", "On-site", "Hybrid"])
            
            j_link = st.text_input("Application Link", value=li_url_input)
            j_desc = st.text_area("Job Description", height=200, placeholder="Paste the job description or highlights here...")
            
            j_submit = st.form_submit_button("Post Job")
            
            if j_submit:
                if j_title and j_company:
                    new_job = {
                        "title": j_title,
                        "company": j_company,
                        "location": j_location,
                        "type": j_type,
                        "mode": j_mode,
                        "link": j_link,
                        "description": j_desc,
                        "postedDate": datetime.now().strftime("%d %b %Y"),
                        "timestamp": datetime.now()
                    }
                    db.collection('jobs').add(new_job)
                    st.success(f"✅ Job '{j_title}' at '{j_company}' added!")
                    # Clear session state
                    if 'auto_title' in st.session_state: del st.session_state['auto_title']
                    if 'auto_company' in st.session_state: del st.session_state['auto_company']
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Title and Company are required!")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("💡 Tip: Changes are instant and reflect in the app immediately!")
