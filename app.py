import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
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
    if not firebase_admin._apps:
        # You'll need to download your service account key from Firebase Console
        # Go to: Project Settings > Service Accounts > Generate New Private Key
        cred = credentials.Certificate("firebase-admin-key.json")
        firebase_admin.initialize_app(cred)
    
    # Use the 'intellitrain' database instead of default
    from google.cloud.firestore import Client
    from google.oauth2 import service_account
    
    # Load credentials from the same file
    creds = service_account.Credentials.from_service_account_file("firebase-admin-key.json")
    return Client(project='intellitrain-3fc95', credentials=creds, database='intellitrain')

db = init_firebase()

# Sidebar
st.sidebar.title("🎓 IntelliTrain Admin")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", ["📋 View Assessments", "➕ Add Assessment", "✏️ Edit Questions", "📊 Upload CSV"])

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

# Footer
st.sidebar.markdown("---")
st.sidebar.info("💡 Tip: Changes are instant and reflect in the app immediately!")
