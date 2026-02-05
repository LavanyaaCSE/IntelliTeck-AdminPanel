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

---

## Deploy to Streamlit Cloud (FREE)

### Step 1: Push to GitHub
1. Create a new repository on GitHub.
2. Push this code to the repository (excluding `firebase-admin-key.json`).

### Step 2: Connect to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io).
2. Click **New app** and select your GitHub repo.
3. Click **Deploy!**

### Step 3: Configure Secrets (CRITICAL)
Once the app is deploying:
1. Go to your App Dashboard on Streamlit Cloud.
2. Click the **three dots** ⋮ next to your app and select **Settings**.
3. Go to the **Secrets** tab.
4. Copy the entire contents of your `firebase-admin-key.json` file.
5. Paste it into the Secrets box using this exact format:

```toml
[firebase]
type = "service_account"
project_id = "intellitrain-3fc95"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
```

*Note: Streamlit understands the flat JSON structure if you paste it correctly under the `[firebase]` header.*

---

## Features

- 📋 **View Assessments**: See all your tests and questions.
- ➕ **Add Assessment**: Create new tests with questions.
- ✏️ **Edit Questions**: Modify existing questions.
- 📊 **Upload CSV**: Bulk upload questions from Excel/CSV.

## CSV Upload Format

Create a CSV with these columns:

| assessment_id | question_text | option_a | option_b | option_c | option_d | correct_answer | concept | difficulty | section |
|--------------|---------------|----------|----------|----------|----------|----------------|---------|------------|---------|
| 4 | What is 2+2? | 3 | 4 | 5 | 6 | B | Math | Easy | Quant |

## Security

⚠️ **Important**: 
- **Never** commit `firebase-admin-key.json` to GitHub.
- Ensure `.gitignore` includes `firebase-admin-key.json`.
- Only share the admin panel URL with authorized staff.
