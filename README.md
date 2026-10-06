# 🎯 Job Application Automation Assistant & 150-Job Campaign System

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Automation-green.svg)](https://playwright.dev/)
[![Campaign Goal](https://img.shields.io/badge/Campaign%20Target-150%20Jobs-orange.svg)](#-campaign-overview)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent, end-to-end job application automation assistant and campaign management system. Built with **Python** and **Playwright**, this system streamlines and accelerates high-volume targeted job searches across major portals (**LinkedIn**, **Wellfound**, **Instahyre**, and **Indeed**).

---

## 📌 Campaign Overview

This repository powers a targeted **150-Job Application Strategy**:
* 💻 **Track 1: Full-Stack Developer** (100 Applications) — Highlighting React, Node.js, MERN Stack, PostgreSQL, and TradingView API integrations.
* 📱 **Track 2: Social Media & Growth Specialist** (50 Applications) — Highlighting organic growth strategies, community management, and 40%+ engagement boosts.

---

## ✨ Features

### 🌐 1. Persistent Playwright Browser Assistant
* **Persistent Login State**: Keeps you logged into LinkedIn, Wellfound, Instahyre, and Indeed—no need to log in repeatedly.
* **Form Auto-Fill**: Intelligently scans active application pages and populates fields like `Name`, `Email`, `Phone`, `City`, `LinkedIn URL`, `GitHub`, `Portfolio`, `Years of Experience`, and `Salary Expectations`.
* **Cover Letter Injector**: Instantly injects dynamic cover letters directly into active text areas or content-editable fields.
* **Direct Portal Shortcuts**: Pre-configured filters for **LinkedIn Easy Apply**, **Instahyre 1-Click**, and **Wellfound Startups**.

### 📝 2. Tailored Cover Letter Generator
* Generates customized cover letters targeted specifically by Company Name, Role Title, and Category (Tech vs. Social Media).
* Dynamically injects proven achievement metrics:
  * **Tech**: *30% API response time optimization, TradingView financial dashboards, scalable MERN architecture.*
  * **Social Media**: *40% organic engagement growth, 95%+ customer response SLA, multi-channel strategy.*

### 📊 3. Automated Application Tracker & Dashboard
* Real-time progress tracking dashboard built directly into the CLI.
* Automatically records logs (`Date`, `Company`, `Role`, `Category`, `Platform`, `Job URL`) into [`data/job_tracker.csv`](data/job_tracker.csv).
* Visual progress bar monitoring completion toward the **150-Job target**.

### 📑 4. Multi-Track Resume & Strategy Suite
* Includes multi-track Markdown resumes ready for conversion or export:
  * [`Nachiket_Rana_Resume_Polished.md`](resumes/Nachiket_Rana_Resume_Polished.md) (Tech / Developer)
  * [`Nachiket_Rana_Resume_Social_Media.md`](resumes/Nachiket_Rana_Resume_Social_Media.md) (Marketing / Social)
  * [`Nachiket_Rana_Resume_Hybrid.md`](resumes/Nachiket_Rana_Resume_Hybrid.md) (Growth / Product)
* 3-4 week execution roadmap mapped out in [`00_START_HERE_MASTER_INDEX.md`](00_START_HERE_MASTER_INDEX.md).

---

## 📂 Project Architecture

```
job-automation-assistant/
├── 📄 main.py                      # Main CLI Application & Interactive Dashboard
├── 📄 run_assistant.bat            # 1-Click Windows Batch Launcher
├── 📄 requirements.txt             # Project Dependencies
├── 📄 00_START_HERE_MASTER_INDEX.md # Master Campaign Index & Execution Plan
├── 📄 QUICK_START_AUTOMATION.md   # Step-by-Step Automation Guide
│
├── 📁 automation/                 # Core Python Automation Modules
│   ├── form_assistant.py           # Playwright Browser Automation & Auto-fill logic
│   ├── cover_letter_generator.py  # Dynamic Cover Letter Builder
│   ├── tracker_manager.py         # CSV Tracking Manager & Analytics
│   └── batch_auto_apply.py        # Portal Batch Application Handlers
│
├── 📁 config/
│   └── profile.json                # User Candidate Profile & Personal Defaults
│
├── 📁 data/
│   └── job_tracker.csv             # Application History Database
│
├── 📁 resumes/                    # Targeted Markdown Resumes
│   ├── Nachiket_Rana_Resume_Polished.md
│   ├── Nachiket_Rana_Resume_Social_Media.md
│   └── Nachiket_Rana_Resume_Hybrid.md
│
└── 📁 templates/                  # Cover Letter JSON Templates
    ├── cover_letters_tech.json
    └── cover_letters_social.json
```

---

## 🚀 Quick Start

### 1. Prerequisites
Ensure you have **Python 3.10+** installed.

### 2. Installation
Clone the repository and install dependencies:

```bash
# Clone the repository
git clone https://github.com/NachiketRana/job-automation-assistant.git
cd job-automation-assistant

# Install Python requirements
pip install -r requirements.txt

# Install Playwright browser binaries
playwright install chromium
```

### 3. Configure Your Profile
Edit [`config/profile.json`](config/profile.json) with your personal contact info, profile links, skills, and form default preferences:

```json
{
  "personal": {
    "full_name": "Your Name",
    "email": "your.email@example.com",
    "phone": "+91 9876543210",
    "city": "Mumbai",
    "linkedin": "https://linkedin.com/in/yourprofile",
    "github": "https://github.com/yourusername",
    "portfolio": "https://yourportfolio.dev"
  }
}
```

### 4. Run the Assistant

**Option A (Terminal):**
```bash
python main.py
```

**Option B (Windows Explorer):**
Double-click `run_assistant.bat`.

---

## 🕹️ Interactive CLI Menu Options

```
=================================================================
      🎯 150-JOB APPLICATION AUTOMATION ASSISTANT
             Candidate: Nachiket Rana | Target: 150 Offers
=================================================================

📊 APPLICATION CAMPAIGN STATUS:
   • Total Applied:  [0 / 150] (0.0%)
   • Tech Jobs:       [0 / 100]
   • Social Media:    [0 / 50]
-----------------------------------------------------------
Choose an action:
  [1] 🚀 Launch Automated Application Browser (LinkedIn / Wellfound / Indeed)
  [2] 📝 Generate Tailored Cover Letter
  [3] ➕ Log a Submitted Job Application
  [4] 📋 View All Submitted Applications
  [5] 📖 Open Master Strategy Guide
  [0] ❌ Exit Assistant
```

1. **[1] Launch Automated Browser**: Opens persistent Playwright Chromium browser loaded with 1-click apply search filters. Use in-terminal hotkeys (`1` for Auto-fill, `2` for Cover Letter Paste).
2. **[2] Generate Tailored Cover Letter**: Prompts for Company & Role, then outputs a custom email body ready to send.
3. **[3] Log Application**: Quickly records applied job entries into `data/job_tracker.csv`.
4. **[4] View Submitted Applications**: Displays recent application history table right in the CLI.

---

## 👤 Author

* **Nachiket Rana** — [GitHub](https://github.com/NachiketRana) • [LinkedIn](https://linkedin.com/in/nachiket-rana)

---

## 📜 License

This project is open-source and available under the [MIT License](LICENSE).
