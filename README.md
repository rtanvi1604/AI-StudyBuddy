# 🎓 AI Study Buddy

An AI-powered study assistant built for the **IBM SkillsBuild Internship Capstone Project**.

Upload your PDF notes and interact with them using **IBM Granite** — get instant answers,
AI summaries, quizzes, and flashcards strictly from your own uploaded study material.

---

## 🚀 Features

| Feature | Description |
|---|---|
| 📤 Upload PDF | Upload study notes (PDF format, up to 20MB) |
| 💬 Chat with Notes | Ask questions — answered only from your notes |
| 📝 AI Summary | Generate a concise summary of your notes |
| 🧠 Quiz Generator | Get 5 AI-generated MCQ questions from your notes |
| 🃏 Flashcard Generator | Generate Q&A flashcards for quick revision |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python Flask |
| PDF Processing | PyMuPDF |
| Embeddings | Sentence-Transformers (all-MiniLM-L6-v2) |
| Vector Database | FAISS |
| Generative AI | IBM Granite (via Ollama) |

---

## ⚙️ How to Run Locally

### Step 1 — Clone the repository
```bash
git clone https://github.com/YourUsername/AI-StudyBuddy.git
cd AI-StudyBuddy
```

### Step 2 — Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Install and set up Ollama


Download Ollama from https://ollama.com
Pull the IBM Granite model:

ollama pull granite4:micro
Ollama starts automatically — verify at http://localhost:11434

### Step 5 — Configure environment
```bash
# Create a .env file with:
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=granite4:micro
FLASK_DEBUG=True
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE_MB=20
```

### Step 6 — Run the app
```bash
python app.py
```

### Step 7 — Open in browser
http://localhost:5000

---

## 📁 Project Structure
AI-StudyBuddy/

├── app.py                 ← Main Flask application

├── requirements.txt       ← Python dependencies

├── .env                   ← Environment variables (not uploaded)

├── README.md              ← Project documentation

│

├── uploads/               ← PDF uploads (auto-created)

├── vectorstore/           ← FAISS index (auto-created)

│

├── templates/

│   └── index.html         ← Frontend UI

│

├── static/

│   ├── style.css          ← Stylesheet

│   └── script.js          ← Frontend logic

│

└── utils/

├── pdf_reader.py      ← PDF text extraction

├── rag.py             ← RAG pipeline + IBM Granite

├── summary.py         ← AI summary generation

├── quiz.py            ← Quiz generation + JSON parsing

└── flashcards.py      ← Flashcard generation

---

## 🤖 AI Pipeline

PDF Upload

↓

Text Extraction (PyMuPDF)

↓

Chunking (500 words, 50-word overlap)

↓

Embedding Generation (Sentence-Transformers)

↓

FAISS Vector Store

↓

User Question

↓

Similarity Search (top-4 chunks)

↓

RAG Prompt → IBM Granite

↓

Grounded Answer

---

## 📸 Application Snapshots

### AI Study Buddy - Dashboard
![Dashboard](https://github.com/rtanvi1604/AI-StudyBuddy/blob/main/1_DASHBOARD.png)

### ChatBot for Interactive session
![Chatbot](https://github.com/rtanvi1604/AI-StudyBuddy/blob/main/2_CHATBOT.png)

### Overall Summary of the Uploaded Notes
![Summary](https://github.com/rtanvi1604/AI-StudyBuddy/blob/main/3_SUMMARY.png)

### Quiz Section
![Quiz_1](https://github.com/rtanvi1604/AI-StudyBuddy/blob/main/4_QUIZ1.png)

![Quiz_2](https://github.com/rtanvi1604/AI-StudyBuddy/blob/main/4_QUIZ2.png)

![Quiz_3](https://github.com/rtanvi1604/AI-StudyBuddy/blob/main/4_QUIZ3.png)

### Flashcards
![Flashcard_1](https://github.com/rtanvi1604/AI-StudyBuddy/blob/main/5_FLASHCARDS1.png)

![Flashcard_2](https://github.com/rtanvi1604/AI-StudyBuddy/blob/main/5_FLASHCARDS2.png)

---

## 👩‍💻 Developed By

**Tanvi R**
Panimalar Engineering College — AI & DS
