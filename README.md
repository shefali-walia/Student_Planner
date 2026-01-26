# 🎓 The Student Ledger: Smart Planner & Focus OS

> **"Don't just list your tasks—crush them."**

The Student Ledger is a **focus-first operating system** designed to help college students navigate the chaos of assignments, clubs, and deadlines. Unlike generic to-do lists, this app combines algorithmic prioritization with "Flow State" tools to ensure you aren't just busy, but productive.

---

## 📱 App Overview
College students struggle with **Decision Paralysis** ("What should I do right now?") and **Focus Fragmentation**. This app solves that by:
1.  **Command Center:** Automating decisions using a weighted scoring algorithm.
2.  **Focus Lab:** Enforcing a workflow that breaks big tasks into small, timed steps.
3.  **Visual Analytics:** Gamifying consistency with XP, Levels, and visual charts.

---

## 🧠 Prioritization Logic Explanation
*As required by the problem statement, here is the exact logic used to rank tasks.*

The app assigns every task a **Priority Score**. The higher the score, the higher it sits on your desk.

**The Formula:**
$$\text{Score} = \text{Base Importance} + \text{Urgency Bonus} + \text{Category Weight}$$

1.  **Base Importance:**
    * High: **70 pts**
    * Medium: **45 pts**
    * Low: **20 pts**
2.  **Urgency Bonus:**
    * If the deadline is within **48 hours**, the task receives a **+30 pt** boost.
3.  **Category Weight (Academic Bias):**
    * If the Category is "Academics", it receives a **+15 pt** boost to ensure GPA-critical work is not ignored.

*Example: A "High Importance" (70) Academic task (15) due Tomorrow (30) gets a score of **115**, placing it above a "High Importance" Club task due next week (70).*

---

## ⚠️ Known Limitations
*While fully functional, the current version has the following constraints:*
1.  **Local Storage:** Data is stored in local JSON files. If the server resets (on the free tier of hosting), data must be restored using the "Backup" file.
2.  **Manual Backups:** Data sync is not automatic across devices; users must manually download their backup to transfer data.
3.  **Single-Player Mode:** There is currently no option to share tasks or collaborate with other students.

---

## 🚀 What I'd Improve with More Time
*Given 48 more hours, I would implement:*
1.  **Cloud Database:** I would migrate from JSON to **PostgreSQL** (via Supabase) to enable real-time sync across mobile and desktop without manual backups.
2.  **AI Breakdown:** I would integrate the Gemini API to allow students to type "Study for Bio Exam" and have the AI auto-generate the 5 specific study steps.
3.  **Focus Ambience:** I would embed a "Lofi Beats" player directly into the Focus Timer popup to reduce friction when starting work.

---

## 🛠️ Tech Stack
* **Frontend:** Streamlit (Python)
* **Visualization:** Altair & Custom CSS
* **Persistence:** Local JSON Engine

## 💾 Installation
1.  Clone the repo: `git clone https://github.com/shefaliwalia04-gif/Student_Planner.git`
2.  Install dependencies: `pip install -r requirements.txt`
3.  Run the app: `streamlit run main.py`

---

