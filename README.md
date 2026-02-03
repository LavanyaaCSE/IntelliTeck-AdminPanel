# IntelliTrain Admin Panel

A Streamlit web app for managing assessment questions in your IntelliTrain app.

## Setup Instructions

### 1. Get Firebase Admin Credentials

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your IntelliTrain project
3. Click the gear icon ⚙️ > **Project Settings**
4. Go to **Service Accounts** tab
5. Click **Generate New Private Key**
6. Save the downloaded JSON file as `firebase-admin-key.json` in this folder

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Locally

```bash
streamlit run app.py
```

The admin panel will open in your browser at `http://localhost:8501`

## Features

- 📋 **View Assessments**: See all your tests and questions
- ➕ **Add Assessment**: Create new tests with questions
- ✏️ **Edit Questions**: Modify existing questions
- 📊 **Upload CSV**: Bulk upload questions from Excel/CSV

## Deploy to Streamlit Cloud (FREE)

1. Push this folder to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click "New app"
5. Select your repository and this folder
6. Add your `firebase-admin-key.json` content to Secrets:
   - Go to app settings > Secrets
   - Paste the entire JSON content
   - Update `app.py` line 16 to use secrets instead of file

### Using Secrets in Streamlit Cloud

Replace line 16-17 in `app.py` with:

```python
import json
cred_dict = json.loads(st.secrets["firebase_admin_key"])
cred = credentials.Certificate(cred_dict)
```

Then in Streamlit Cloud secrets, paste your entire `firebase-admin-key.json` content like:

```toml
firebase_admin_key = '''
{
  "type": "service_account",
  "project_id": "intellitrain-3fc95",
  ...
}
'''
```

## CSV Upload Format

Create a CSV with these columns:

| assessment_id | question_text | option_a | option_b | option_c | option_d | correct_answer | concept | difficulty | section |
|--------------|---------------|----------|----------|----------|----------|----------------|---------|------------|---------|
| 4 | What is 2+2? | 3 | 4 | 5 | 6 | B | Math | Easy | Quant |

## Security

⚠️ **Important**: 
- Never commit `firebase-admin-key.json` to GitHub
- Add it to `.gitignore`
- Use Streamlit Secrets for deployment
- Only share the admin panel URL with trusted admins
