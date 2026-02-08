<div align="center">
  <br />
  <h1>🌊 U N D E R T O N E</h1>
  <h3>Intent-Driven Music Discovery Engine</h3>
  
  <p>
    <a href="https://www.python.org"><img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" /></a>
    <a href="https://flask.palletsprojects.com"><img src="https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" /></a>
    <a href="https://www.sqlite.org"><img src="https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" /></a>
    <a href="https://librosa.org"><img src="https://img.shields.io/badge/Librosa-Audio-orange?style=for-the-badge" alt="Librosa" /></a>
    <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License" /></a>
  </p>

  <p><i>Prioritizing user intent over listening history through objective analysis and shared taste.</i></p>
  
  <br />
</div>

<hr />

## 📖 Table of Contents

- [🌌 The Vision](#-the-vision)
- [🏗️ System Architecture](#️-system-architecture)
- [📂 Project Structure](#-project-structure)
- [🛠️ The Arsenal (Tech Stack)](#-the-arsenal-tech-stack)
- [🧩 core Intelligence Pipeline](#-core-intelligence-pipeline)
- [📊 Data Sovereignty: Objective vs Subjective](#-data-sovereignty-objective-vs-subjective)
- [🔊 Advanced Audio Analysis](#-advanced-audio-analysis)
- [🚀 Local Development](#-local-development)
  - [Prerequisites](#prerequisites)
  - [Environment Setup](#environment-setup)
  - [Running the App](#running-the-app)
- [🤝 Contributing](#-contributing)
- [🛣️ Roadmap](#️-roadmap)

---

## 🌌 The Vision

Most music recommendation systems rely on "Collaborative Filtering" that traps users in an echo chamber of their own past behavior. If you listen to one Jazz track, you get Jazz forever.

**Undertone** breaks this loop.

It is an **Intent Engine**. It treats music not just as a set of tags, but as a collection of objective physical properties (BPM, Loudness, Frequencies) and subjective community context. By strictly separating "Mainstream" and "Niche" discovery, Undertone allows users to search for music based on how they *want* to feel, rather than what they've already heard.

---

## 🏗️ System Architecture

Undertone uses a **Decoupled Monolith Architecture** focused on algorithmic precision and data integrity.

### **Backend Layer (The Intelligence)**
- **Flask Framework**: A lightweight Python core for rapid algorithmic iteration.
- **SQLAlchemy ORM**: Managing structured relationships between Songs, User Libraries, and Subjective Tags.
- **Signal Processing**: Integration with `librosa` for real-time validation of musical attributes (Screaming logic, Bass intensity).

### **Frontend Layer (The Interface)**
- **Vanilla JS & Navy Blue Design**: A minimalist, high-performance UI using CSS variables for a premium, dark-mode aesthetic.
- **Dynamic Filter Chips**: Real-time query construction for complex intent matching.

---

## 📂 Project Structure

```bash
/
├── backend/
│   ├── app.py              # Main Flask Entry Point
│   ├── models.py           # Database Schema (Songs, Users, Feedback)
│   ├── music_standards.py  # Academic Music Theory Definitions
│   ├── requirements.txt    # Backend Dependencies
│   └── undertone.db        # local SQLite Database
├── venv/                   # Python Virtual Environment
├── README.md               # Project Documentation
└── .gitignore              # Dependency & DB Exclusions
```

---

## 🛠️ The Arsenal (Tech Stack)

<div align="center">

| **Logic Core** | **Audio Analysis** | **Storage & Infra** |
| :---: | :---: | :---: |
| <img src="https://img.shields.io/badge/Python%203-3776AB?style=for-the-badge&logo=python&logoColor=white" /> | <img src="https://img.shields.io/badge/Librosa-FF9900?style=for-the-badge&logo=scipy&logoColor=white" /> | <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" /> |
| <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" /> | <img src="https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white" /> | <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge" /> |
| <img src="https://img.shields.io/badge/Vanilla%20JS-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" /> | <img src="https://img.shields.io/badge/Music%20Theory-Academic-blue?style=for-the-badge" /> | <img src="https://img.shields.io/badge/CSS3-Navy%20Blue-1572B6?style=for-the-badge" /> |

</div>

---

## 🧩 Core Intelligence Pipeline

Undertone operates on a two-stage filtering process:

### 1. Objective Filtering (Music Theory)
We categorize music based on physical attributes defined by academic standards (Harvard/Stanford Music Theory references).
- **Tempo Logic**: BPM thresholds for Fast/Slow categorization.
- **Energy Mapping**: Frequency analysis for "Heavy" vs "Mellow" detection.

### 2. Subjective Harmonization (User Feedback)
A "Shared Taste" algorithm that refines global tags based on human confirmation.
- **Search Success Logic**: Tracking which songs users actually find for specific intents.
- **Anomaly Filter**: Requiring consensus before official tag updates.

---

## 📊 Data Sovereignty: Objective vs Subjective

| Attribute | Type | Source |
| :--- | :--- | :--- |
| **BPM** | Objective | Extracted Metadata |
| **BPM Category** | Objective | Academic Thresholds |
| **Genre** | Objective | Taxonomy Dictionary |
| **Mood (Sad/Happy)** | Subjective | User Confirmation Consensus |
| **Energy (High/Low)** | Hybrid | Audio Peak Analysis + User Tags |

---

## 🔊 Advanced Audio Analysis

Phase 10 integration uses `librosa` to handle complex queries:
- **"Screaming" Detection**: Sustained high-decibel frequency analysis.
- **Heavy Bass**: Sub-woofer frequency intensity checks.

---

## 🚀 Local Development

### Prerequisites
- **Python 3.8+**
- **pip** (v20+)

### Environment Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/uluisugiyama/Undertone.git
   cd Undertone
   ```
2. **Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

### Running the App
```bash
python backend/app.py
```
Access the API at `http://127.0.0.1:5001`.

---

## 🛣️ Roadmap

- [x] **Phase 1: Skeleton**: Flask setup & Song Schema.
- [/] **Phase 2: Logic**: Music standards & Genre taxonomy.
- [x] **Phase 3: Data**: Ingestion & Objective filtering.
- [x] **Phase 4: Frontend**: POC UI.
- [x] **Phase 5: Profiles**: User Authentication & Libraries.
- [x] **Phase 6: Feedback**: Search success collection.
- [x] **Phase 7: CF Engine**: Shared taste logic.
- [x] **Phase 8: Toggles**: Mainstream vs Niche modes.
- [ ] **Phase 9: UI Overhaul**: Navy Blue premium design.
- [ ] **Phase 10: Audio**: Librosa integration.
- [ ] **Phase 11: Loops**: Algorithm refinement cron jobs.
- [ ] **Phase 12: Polish**: Optimization & kontradiction flagging.

---

<div align="center">
  <p><b>Undertone</b> is open-source software licensed under the <a href="./LICENSE">MIT License</a>.</p>
</div>