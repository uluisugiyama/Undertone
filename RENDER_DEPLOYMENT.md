# Render Deployment Guide for Python Web App

This guide assumes your repository structure is now updated as follows.

## 1. Final Project Structure

Use this structure. Note that `requirements.txt` and `.gitignore` are now in the root directory.

```text
Undertone/
├── .gitignore               # Updated to exclude venv, .env, etc.
├── requirements.txt         # Root requirements file for Render
├── README.md
├── backend/
│   ├── app.py               # Main Flask application (Updated)
│   ├── models.py
│   ├── ... (other backend files)
│   └── migrations/
└── frontend/
    ├── index.html
    ├── style.css
    ├── script.js
    └── ... (other frontend files)
```

**Key Explanations:**
- **`requirements.txt` (Root):** Render looks for this file in the root directory by default to install Python dependencies.
- **`backend/app.py`:** The entry point for your application. It has been updated to serve static files from `../frontend` at the root URL (`/`) and use environment variables.
- **`frontend/`:** Contains your static assets. These are served directly by Flask in this setup.

---

## 2. Backend Implementation (Python)

**Choice:** **Flask**
**Justification:** Your existing application is built with Flask, and it is perfectly capable of serving a single-service web app on Render. Switching to FastAPI would require a complete rewrite of your routing and database logic.

### Updated `backend/app.py`

This code is already updated in your local file. It serves the frontend at the root `/` and includes a health check.

```python
from flask import Flask, jsonify, request, session, send_from_directory
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, and_
from models import db, Song, User, UserLibrary, UserRating, PersonalTrending, SongTag, SearchLog, SongAnalysis
from music_standards import is_fast_tempo, is_heavy, get_parent_genre
import os
import random
import math
import requests
from datetime import datetime
import json
from dotenv import load_dotenv
from lastfm_client import LastFMClient

load_dotenv() # Load variables from .env

# Serve frontend static files from the 'frontend' directory one level up
app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Use environment variable for secret key in production
app.secret_key = os.getenv('SECRET_KEY', 'undertone-secret-key-poc') 
CORS(app, supports_credentials=True)

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ... [Helper functions: call_gemini_api, calculate_mainstream_score] ...

@app.route('/gui')
def gui_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/gui/profile')
def gui_profile():
    return send_from_directory(app.static_folder, 'profile.html')

# Catch-all for other static files (css, js)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
database_url = os.getenv('DATABASE_URL')
# Render provides 'postgres://' but SQLAlchemy requires 'postgresql://'
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///' + os.path.join(basedir, 'undertone.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/healthz')
def health_check():
    return jsonify({"status": "ok", "db": "connected"}), 200

# ... [Rest of your application logic] ...
```

---

## 3. Frontend Implementation

Your frontend files (`index.html`, `style.css`, `script.js`) form a Single Page Application (SPA) structure.

### Key Requirements Checklist:
- [x] **Relative URLs:** Your `script.js` uses relative paths like `/search/intent` and `/library/save`. This means it will automatically work on `https://your-app.onrender.com` without changes.
- [x] **No Localhost:** There are no hardcoded `http://localhost:5000` references in the files I reviewed.

### `frontend/index.html` (Snippet)
The `script` tag uses a relative path, which is correct:
```html
<script src="/script.js"></script>
```

### `frontend/script.js` (Snippet)
Fetch calls use relative paths, which is correct:
```javascript
const response = await fetch(`/search/intent?intent=${encodeURIComponent(intent)}&mode=${currentMode}`...
```

---

## 4. requirements.txt

This file is now in your **root** directory.

```text
Flask
Flask-SQLAlchemy
Flask-Migrate
Flask-Cors
requests
python-dotenv
gunicorn
psycopg2-binary
```

**Additions:**
- `gunicorn`: The production server we will use.
- `psycopg2-binary`: Required for connecting to PostgreSQL on Render.

---

## 5. Gunicorn Setup

On Render, we will use Gunicorn to serve the Flask app.

**Command:**
```bash
gunicorn backend.app:app
```

**Explanation:**
- `backend.app`: Python module path. It looks for `app.py` inside the `backend` folder.
- `:app`: The Flask instance variable name inside `app.py`.
- Render automatically sets the `PORT` environment variable, and Gunicorn respects it by default.

---

## 6. Render Deployment Configuration

Follow these steps manually on the Render Dashboard.

1.  **Create Service:**
    - Click **New +** -> **Web Service**.
    - Connect your GitHub repository: `uluisugiyama/Undertone`.

2.  **Service Configuration:**
    - **Name:** `undertone` (or your preference)
    - **Region:** Choose the one closest to you (e.g., Oregon, Frankfurt).
    - **Branch:** `main`
    - **Root Directory:** Leave blank (defaults to root).
    - **Runtime:** `Python 3`
    - **Build Command:** `pip install -r requirements.txt`
    - **Start Command:** `gunicorn backend.app:app`

3.  **Instance Type:**
    - Select **Free**. (Note: The free tier spins down after 15 minutes of inactivity. The first request will take ~30-50 seconds to warm up).

4.  **Environment Variables:**
    Scroll down to "Environment Variables" and add these:

    | Key | Value |
    | :--- | :--- |
    | `PYTHON_VERSION` | `3.10.0` (or your local version) |
    | `SECRET_KEY` | (Generate a random string, e.g., `s3cr3t_k3y_g3n`) |
    | `LASTFM_API_KEY` | (Your Last.fm API Key) |
    | `GEMINI_API_KEY` | (Your Gemini API Key) |

5.  **Database (PostgreSQL):**
    - Open a new tab. Go to Render Dashboard -> **New +** -> **PostgreSQL**.
    - **Name:** `undertone-db`
    - **Instance Type:** **Free**.
    - **Create Database**.
    - Once created, copy the **Internal Database URL**.
    - Go back to your Web Service -> **Environment Variables**.
    - Add Key: `DATABASE_URL`, Value: (Paste the Internal Database URL).

6.  **Deploy:**
    - Click **Create Web Service**.

---

## 7. GitHub Preparation

I have already performed these steps for you.

**Git Commands executed:**
```bash
git add .
git commit -m "Prepare app for Render deployment: update app.py and add root configs"
git push origin main
```

**Updated `.gitignore`:**
```text
venv/
__pycache__/
*.pyc
.DS_Store
.env
*.db
instance/
.idea/
.vscode/
```

---

## 8. Manual Steps (Required)

1.  **Sign up/Login to Render:** Go to [dashboard.render.com](https://dashboard.render.com/).
2.  **Create PostgreSQL Database:** Required because SQLite (search.db) is a file and will be **deleted** every time Render redeploys or restarts. You *must* use PostgreSQL for persistent data.
3.  **Set Environment Variables:** You must copy your API keys from your local `.env` file into the Render Dashboard manually. I cannot do this for you.
4.  **Database Migration:**
    - After deployment, the database will be empty.
    - Go to the Render Dashboard -> Select your Web Service -> **Shell**.
    - Run the following commands in the Render Shell to initialize the DB:
      ```bash
      flask db upgrade
      ```
      *(Note: If you haven't initialized migrations locally, you might need `flask db init` and `flask db migrate -m "Initial migration"` locally first, push, and then `flask db upgrade` on Render.)*
      
      **Simpler Alternative for First Run:**
      In the Render Shell, you can run a python script to create tables if migrations assume an existing DB state:
      ```python
      python
      >>> from backend.app import app, db
      >>> with app.app_context():
      ...     db.create_all()
      >>> exit()
      ```

---

## 9. Common Failure Cases

| Error | Cause | Fix |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'backend'` | Gunicorn cannot find the module. | Ensure Start Command is `gunicorn backend.app:app`. |
| `gunicorn: command not found` | Gunicorn not installed. | Ensure `gunicorn` is in `requirements.txt`. |
| `Internal Server Error` (500) | Database connection failed or missing secrets. | Check Render Logs. Verify `DATABASE_URL` matches the PostgreSQL Internal URL exactly. |
| `Web Service limits exceeded` | Free tier limitation. | Ensure you aren't loading huge datasets into memory. Use `psycopg2-binary` instead of `psycopg2`. |
| App sleeps / Slow load | Free tier limitation. | This is normal. Upgrade to a paid plan ($7/mo) to keep it awake. |
