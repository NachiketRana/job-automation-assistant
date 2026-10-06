# 🚀 Quick Start Guide: Job Application Automation Assistant

Welcome to your **Option A: Job Application Automation Assistant**!  
This tool is built specifically to accelerate your **150-Job Application Campaign** (100 Tech + 50 Social Media).

---

## 🛠️ How to Launch the Assistant

You have two easy ways to start:

1. **Via Command Line**:
   ```powershell
   python main.py
   ```
2. **Via Windows Explorer**:
   * Double click [`run_assistant.bat`](file:///c:/Users/nachi/OneDrive/Desktop/job/run_assistant.bat) in your project folder.

---

## ✨ System Features & Capabilities

### **1. 🚀 Automated Application Browser (Playwright-Powered)**
* Opens a persistent Chrome browser window.
* **Persistent Login**: Once you log into LinkedIn, Wellfound, Instahyre, or Indeed, your logins stay saved!
* **Form Auto-Fill**: Automatically populates Name, Email, Phone, City, LinkedIn URL, GitHub, Portfolio, Years of Experience, and Salary Expectations on job application forms.
* **Cover Letter Paster**: Paste custom cover letters into active form fields instantly with 1 keypress.

### **2. 📝 Tailored Cover Letter Generator**
* Automatically creates customized cover letters targeting specific Companies and Job Titles.
* Selects appropriate highlights based on category:
  * **Tech**: Highlights 30% API throughput improvement, TradingView dashboard experience, MERN stack, PostgreSQL optimization.
  * **Social Media**: Highlights 40% organic engagement growth, multi-account management, 95%+ fast customer response SLA.

### **3. 📊 Automated Application Tracker**
* Every time you finish applying to a job, log it in the app.
* Automatically records: Date, Company, Role, Category (Tech/Social), Platform, and Cover Letter used into [`data/job_tracker.csv`](file:///c:/Users/nachi/OneDrive/Desktop/job/data/job_tracker.csv).
* Shows live progress bar towards your target of **150 Jobs** (100 Tech / 50 Social).

---

## 📁 Key File Locations

* 👤 **Personal Data & Config**: [`config/profile.json`](file:///c:/Users/nachi/OneDrive/Desktop/job/config/profile.json)
* 📄 **Resumes**:
  * Tech Resume: [`resumes/Nachiket_Rana_Resume_Polished.md`](file:///c:/Users/nachi/OneDrive/Desktop/job/resumes/Nachiket_Rana_Resume_Polished.md)
  * Social Media Resume: [`resumes/Nachiket_Rana_Resume_Social_Media.md`](file:///c:/Users/nachi/OneDrive/Desktop/job/resumes/Nachiket_Rana_Resume_Social_Media.md)
  * Hybrid Resume: [`resumes/Nachiket_Rana_Resume_Hybrid.md`](file:///c:/Users/nachi/OneDrive/Desktop/job/resumes/Nachiket_Rana_Resume_Hybrid.md)
* 📊 **Tracker CSV**: [`data/job_tracker.csv`](file:///c:/Users/nachi/OneDrive/Desktop/job/data/job_tracker.csv)
* 📖 **Master Strategy Plan**: [`00_START_HERE_MASTER_INDEX.md`](file:///c:/Users/nachi/OneDrive/Desktop/job/00_START_HERE_MASTER_INDEX.md)

---

## 🎯 Daily Workflow Recommendation

1. Run `python main.py` or double-click `run_assistant.bat`.
2. Select **[1] Launch Automated Browser**.
3. Go to LinkedIn Jobs / Wellfound.
4. For each job posting:
   * Generate a cover letter (Option 2 in main menu).
   * Hit Option 1 in browser command prompt to auto-fill common application fields.
   * Hit Option 2 to paste your custom cover letter.
   * Submit application (or review & click Submit).
   * Log the application in tracker (Option 3).
5. Target: **5–10 applications per day**. You will complete your 150 target in 3 weeks!
