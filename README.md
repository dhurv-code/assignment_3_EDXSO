AI-Powered Interview Accelerator 🎯

An AI-driven job interview simulator built with Streamlit and Google Gemini 1.5. The app analyzes a Job Description and Candidate Resume, computes a Job Fit Score, conducts an adaptive multi-level interview using voice synthesis, and generates a post-interview performance evaluation report.

---

## 🛠️ Prerequisites

* Python 3.10 or higher
* A Google Gemini API Key

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd ai-interview-accelerator
2. Create and Activate Virtual Environment
Windows:
python -m venv venv
venv\Scripts\activate

3. Install Dependencies
Bash
pip install -r requirements.txt

4. Configure Environment Variables
Create a .env file in the root directory and add your Gemini API key:
GEMINI_API_KEY=your_actual_gemini_api_key_here

5. Run the Application
Bash
streamlit run app.py