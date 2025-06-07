# 🩺 Patient History Chatbot

An AI-powered chatbot that records a patient's full history before an initial consultation. Built for the AI Futures Hackathon.

---

## 🚀 How to Run the Project (Full Stack Setup)

### ✅ Prerequisites
Make sure you have these installed:
- [Node.js & npm](https://nodejs.org)
- Python 3.10+ (Anaconda okay)
- [Ollama](https://ollama.com) installed locally
- DeepSeek model installed:
  ```bash
  ollama pull deepseek-r1:8b
  ```

---

### ▶️ 1. Start Ollama (LLM Server)

In **Terminal 1**:
```bash
ollama serve
```
> 🧠 This starts the local LLM server the chatbot uses to generate responses.

---

### ▶️ 2. Start FastAPI Backend

In **Terminal 2**:
```bash
cd /Users/vishal/Career/AI-Futures-Hackathon
uvicorn main:app --reload
```
> 📡 Runs backend server at http://localhost:8000

If you get an “Address already in use” error:
```bash
lsof -i :8000
kill -9 <PID>
```

---

### ▶️ 3. Start React Frontend (Chat UI)

In **Terminal 3**:
```bash
cd /Users/vishal/Career/AI-Futures-Hackathon/AI-futures-hackathon
npm install      # Only needed once
npm run dev
```
> 🌐 Access the frontend at http://localhost:5173

---

### 🧠 What Each Terminal Does

| Terminal | Command                        | Purpose                         |
|----------|--------------------------------|---------------------------------|
| #1       | `ollama serve`                 | Start LLM model server          |
| #2       | `uvicorn main:app --reload`    | Start FastAPI backend           |
| #3       | `npm run dev` (in React folder)| Start React chat UI             |

---

### ✅ Shut Down
Press `Ctrl + C` in each terminal to stop.

---

## 📁 Folder Structure Overview

```bash
AI-Futures-Hackathon/
├── AI-futures-hackathon/       # Frontend React App
├── main.py                     # FastAPI backend
├── offload/                    # Ollama offload folder (auto-managed)
├── Resources/                  # Patient intake PDFs and docs
├── index.html                  # Legacy HTML if needed
├── package.json                # Node config
└── README.md                   # You are here 📄
```

---

Built by Vishal Vasanthakumar Poornima and team for AI Futures Hackathon ✨
