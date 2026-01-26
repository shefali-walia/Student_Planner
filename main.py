import streamlit as st
import pandas as pd
import json
import os
import time
import calendar
import altair as alt
from datetime import date, datetime, timedelta

# --- 1. DATA ENGINE ---
def load_data(username):
    filename = f"{username}_planner_v22.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
            # Safe date conversion
            for task in data.get("tasks", []):
                if task.get("deadline"):
                    try:
                        task["deadline"] = datetime.strptime(task["deadline"], "%Y-%m-%d").date()
                    except:
                        task["deadline"] = None
            
            # Legacy Support for old step formats
            for task in data.get("tasks", []):
                if "chunks" in task and task["chunks"] and isinstance(task["chunks"][0], str):
                    new_chunks = [{"name": c, "minutes": 25, "status": "pending"} for c in task["chunks"]]
                    task["chunks"] = new_chunks

            return data
    else:
        return {
            "tasks": [],     
            "history": [],   
            "subcategories": ["General"],
            "cat_styles": {
                "Academics": {"color": "#FDF5E6", "text": "#1A1110"},
                "Clubs": {"color": "#F0EAD6", "text": "#1A1110"},
                "Personal": {"color": "#FFF8DC", "text": "#1A1110"}
            },
            "common_steps": ["Read Material", "Make Notes", "Drafting", "Review", "Practice Problems"]
        }

def save_data(username, data):
    filename = f"{username}_planner_v22.json"
    data_to_save = json.loads(json.dumps(data, default=str))
    with open(filename, "w") as f:
        json.dump(data_to_save, f, indent=4)

def mark_task_complete(username, task_id):
    data = load_data(username)
    idx = -1
    for i, t in enumerate(data["tasks"]):
        if t["id"] == task_id:
            idx = i
            break
    
    if idx != -1:
        completed_task = data["tasks"].pop(idx)
        completed_task["completed_date"] = str(date.today())
        if "history" not in data: data["history"] = []
        data["history"].append(completed_task)
        save_data(username, data)
        return True
    return False

# --- 2. LOGIC ---
def get_priority_score(deadline, importance, category):
    today = date.today()
    is_urgent = False
    if deadline:
        days_left = (deadline - today).days
        if days_left <= 2: is_urgent = True
    
    imp_map = {"Low": 20, "Medium": 45, "High": 70}
    base_score = imp_map.get(importance, 20)
    if is_urgent: base_score += 30
    if category == "Academics": base_score += 15
    return base_score

# --- 3. UI THEME ---
st.set_page_config(page_title="Student Ledger", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #BDB196 !important; }
    [data-testid="stSidebar"] { background-color: #3E2723 !important; }
    [data-testid="stSidebar"] * { color: #FDF5E6 !important; }
    h1, h3, p, div, button, li, span { font-family: 'Georgia', serif; }
    
    /* Header Fix */
    h2 { font-size: 1.0rem !important; color: #1A1110 !important; font-weight: bold; }
    
    /* Global Buttons */
    div.stButton > button {
        background-color: #FDF5E6 !important;
        color: #3E2723 !important;
        border: 1px solid #3E2723 !important;
        border-radius: 5px !important;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #3E2723 !important;
        color: #FDF5E6 !important;
    }

    /* SIDEBAR BUTTONS (Logout & Download) - Unified Style */
    section[data-testid="stSidebar"] div.stButton > button, 
    section[data-testid="stSidebar"] div.stDownloadButton > button {
        background-color: #3E2723 !important;
        color: #FDF5E6 !important;
        border: 1px solid #FDF5E6 !important;
        margin-top: 10px !important;
        width: 100%;
    }
    
    section[data-testid="stSidebar"] div.stButton > button:hover,
    section[data-testid="stSidebar"] div.stDownloadButton > button:hover {
        background-color: #5D4037 !important;
        color: #FFFFFF !important;
        border-color: #FFFFFF !important;
    }

    .big-timer {
        font-size: 3.5rem !important;
        font-weight: bold;
        color: #3E2723;
        text-align: center;
        background-color: #FDF5E6;
        border: 2px solid #3E2723;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }
    
    .step-card {
        background-color: rgba(255,255,255,0.4);
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 5px;
        border-left: 3px solid #3E2723;
    }
    
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input { 
        background-color: #FDF5E6 !important; 
        color: #1A1110 !important; 
    }
    </style>
    """, unsafe_allow_html=True)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
    
# --- STATE INITIALIZATION ---
if "timer_active" not in st.session_state: st.session_state.timer_active = False
if "timer_paused" not in st.session_state: st.session_state.timer_paused = False
if "time_left" not in st.session_state: st.session_state.time_left = 0
if "current_task_title" not in st.session_state: st.session_state.current_task_title = ""
if "current_step_index" not in st.session_state: st.session_state.current_step_index = 0
if "active_step_name" not in st.session_state: st.session_state.active_step_name = ""
if "timer_mode" not in st.session_state: st.session_state.timer_mode = "running"
if "planner_active" not in st.session_state: st.session_state.planner_active = False
if "planner_task_id" not in st.session_state: st.session_state.planner_task_id = None

# CALENDAR STATE
if "cal_year" not in st.session_state: st.session_state.cal_year = date.today().year
if "cal_month" not in st.session_state: st.session_state.cal_month = date.today().month

# --- 4. LOGIN ---
if not st.session_state.logged_in:
    st.title("🔐 Welcome to Your Planner")
    st.caption("Enter a username to load your saved data.")
    user_input = st.text_input("Username:")
    if st.button("Login / Register"):
        if user_input.strip():
            st.session_state.username = user_input.strip()
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# LOAD DATA
user_data = load_data(st.session_state.username)

# --- 5. NAVIGATION ---
with st.sidebar:
    st.title("📖 Navigation")
    view = st.radio("Go to:", ["Command Center", "Reflection", "Calendar"])
    st.divider()
    
    if st.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.planner_active = False
        st.session_state.timer_active = False
        st.rerun()
    
    st.divider()
    
    # BACKUP BUTTON
    json_str = json.dumps(user_data, indent=4, default=str)
    
    st.download_button(
        label="💾 Download Backup",
        data=json_str,
        file_name=f"{st.session_state.username}_backup.json",
        mime="application/json"
    )

# --- 6. DIALOGS ---

@st.dialog("⏱️ Focus Timer")
def show_timer_popup():
    if st.session_state.timer_mode == "flow_check":
        st.subheader("Step Complete! 🎉")
        st.write("Take a breath. How are you feeling?")
        
        task = next((t for t in user_data["tasks"] if t["id"] == st.session_state.planner_task_id), None)
        next_idx = st.session_state.current_step_index + 1
        
        if task and next_idx < len(task["chunks"]):
            next_step = task["chunks"][next_idx]
            st.info(f"Ready for the next step: **{next_step['name']}**?")
            st.write(f"⏱️ Duration: {next_step['minutes']} mins")
            
            col_next, col_stop = st.columns(2)
            with col_next:
                if st.button("🚀 Start Next Step", use_container_width=True):
                    st.session_state.current_step_index = next_idx
                    st.session_state.active_step_name = next_step['name']
                    st.session_state.time_left = next_step['minutes'] * 60
                    st.session_state.timer_mode = "running"
                    st.rerun()
            with col_stop:
                if st.button("⏹ Stop Session", use_container_width=True):
                    st.session_state.timer_active = False
                    st.rerun()
        else:
            st.balloons()
            st.success("Hurray! You completed the entire task!")
            st.write("Marking task as complete...")
            if st.button("Finish & Archive Task", use_container_width=True):
                mark_task_complete(st.session_state.username, st.session_state.planner_task_id)
                st.session_state.timer_active = False
                st.session_state.planner_active = False
                st.session_state.planner_task_id = None
                st.rerun()

    else:
        st.subheader(f"Step {st.session_state.current_step_index + 1}: {st.session_state.active_step_name}")
        
        mins, secs = divmod(st.session_state.time_left, 60)
        st.markdown(f'<div class="big-timer">{mins:02d}:{secs:02d}</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.session_state.timer_paused:
                if st.button("▶ Resume", use_container_width=True):
                    st.session_state.timer_paused = False
                    st.rerun()
            else:
                if st.button("⏸ Pause", use_container_width=True):
                    st.session_state.timer_paused = True
                    st.rerun()      
        with col2:
            if st.button("⏹ Stop", use_container_width=True):
                st.session_state.timer_active = False 
                st.rerun()
        with col3:
            if st.button("✅ Done Early", use_container_width=True):
                st.session_state.time_left = 0
                st.rerun()

        if st.session_state.timer_active and not st.session_state.timer_paused and st.session_state.timer_mode == "running":
            if st.session_state.time_left > 0:
                time.sleep(1) 
                st.session_state.time_left -= 1
                st.rerun() 
            else:
                st.session_state.timer_mode = "flow_check"
                st.rerun()

@st.dialog("📝 Plan Your Session")
def open_planner_popup(task_id):
    task = next((t for t in user_data["tasks"] if t["id"] == task_id), None)
    if not task: 
        st.error("Task not found.")
        st.session_state.planner_active = False
        st.rerun()

    st.title(f"📍 {task['title']}")
    
    if "chunks" not in task: task["chunks"] = []
    
    if task["chunks"]:
        st.caption("Your planned steps:")
        for i, chunk in enumerate(task["chunks"]):
            name = chunk["name"] if isinstance(chunk, dict) else str(chunk)
            mins = chunk.get("minutes", 25) if isinstance(chunk, dict) else 25
            st.markdown(
                f'<div class="step-card"><b>Step {i+1}:</b> {name} <span style="float:right;">⏱️ {mins}m</span></div>', 
                unsafe_allow_html=True
            )
    else:
        st.info("You can break your task into manageable chunks here to work on it one step at a time OR just launch to tackle the whole task in one session.")

    st.write("---")
    
    with st.form("new_step_form", clear_on_submit=True):
        st.subheader("Add a Step")
        col_name, col_time = st.columns([3, 1])
        with col_name:
            new_step_name = st.text_input("Name (e.g., Read Intro)")
        with col_time:
            new_step_time = st.number_input("Mins", min_value=1, value=15, step=5)
            
        if st.form_submit_button("➕ Add Step"):
            new_chunk = {"name": new_step_name, "minutes": int(new_step_time), "status": "pending"}
            task["chunks"].append(new_chunk)
            save_data(st.session_state.username, user_data)
            st.rerun()

    st.write("---")
    
    col_go, col_close = st.columns([2, 1])
    with col_go:
        if st.button("🚀 Launch Sequence", use_container_width=True):
            
            if not task["chunks"]:
                default_mins = int(task.get("effort", 0.5) * 60)
                if default_mins < 1: default_mins = 25
                
                single_chunk = {"name": "Focus Session", "minutes": default_mins, "status": "pending"}
                task["chunks"].append(single_chunk)
                save_data(st.session_state.username, user_data)
                
            first_step = task["chunks"][0]
            st.session_state.current_step_index = 0
            st.session_state.active_step_name = first_step["name"]
            st.session_state.time_left = first_step["minutes"] * 60
            
            st.session_state.timer_active = True 
            st.session_state.timer_paused = False
            st.session_state.timer_mode = "running"
            st.session_state.current_task_title = task['title']
            
            st.session_state.planner_active = False 
            st.rerun()
            
    with col_close:
        if st.button("❌ Exit", use_container_width=True):
            st.session_state.planner_active = False
            st.session_state.planner_task_id = None
            st.rerun()

@st.dialog("✒️ New Entry")
def add_task_dialog():
    title = st.text_input("Task Title")
    cat_choice = st.selectbox("Category", options=list(user_data["cat_styles"].keys()) + ["+ New Category"])
    
    if cat_choice == "+ New Category":
        new_cat = st.text_input("Name")
        new_color = st.color_picker("Note Color", "#FDF5E6")
        if st.button("Register"):
            user_data["cat_styles"][new_cat] = {"color": new_color, "text": "#1A1110"}
            save_data(st.session_state.username, user_data)
            st.rerun()
        final_cat = new_cat
    else:
        final_cat = cat_choice

    sub_choice = st.selectbox("Subcategory", options=user_data["subcategories"] + ["+ Add New"])
    final_sub = st.text_input("Enter Subcategory") if sub_choice == "+ Add New" else sub_choice

    st.divider()
    has_deadline = st.checkbox("Deadline?")
    dline = st.date_input("Date") if has_deadline else None
    imp = st.radio("Importance", ["Low", "Medium", "High"], horizontal=True)
    effort = st.number_input("Effort (Hours)", min_value=0.5, step=0.5)

    if st.button("Place on Desk"):
        if title:
            if final_sub not in user_data["subcategories"]: user_data["subcategories"].append(final_sub)
            new_task = {
                "id": str(datetime.now()), "title": title, "category": final_cat,
                "subcategory": final_sub, "deadline": dline, "importance": imp,
                "effort": effort, "score": get_priority_score(dline, imp, final_cat),
                "chunks": [],
                "completed": False
            }
            user_data["tasks"].append(new_task)
            save_data(st.session_state.username, user_data)
            st.rerun()

# --- 7. STATE MANAGER ---
if st.session_state.timer_active:
    show_timer_popup()
elif st.session_state.planner_active and st.session_state.planner_task_id:
    open_planner_popup(st.session_state.planner_task_id)

# --- 8. MAIN VIEW ---
if view == "Command Center":
    col_t1, col_t2 = st.columns([8, 2])
    with col_t1: st.title("🏛️ The Command Center")
    with col_t2: 
        if st.button("➕ Add Task"): add_task_dialog()

    if not user_data["tasks"]:
        st.markdown("""
            <div style="background-color: #FDF5E6; padding: 20px; border: 1px solid #3E2723; border-radius: 5px; text-align: center;">
                <h3 style="margin:0; color: #3E2723;">Your desk is clear.</h3>
                <p style="margin:0; color: #5D4037;">Add a task to begin.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        active_cats = list(set(t["category"] for t in user_data["tasks"]))
        num_cols = 4 
        rows = [active_cats[i:i + num_cols] for i in range(0, len(active_cats), num_cols)]

        for row in rows:
            cols = st.columns(num_cols)
            for i, cat_name in enumerate(row):
                with cols[i]:
                    style = user_data["cat_styles"].get(cat_name, {"color": "#FDF5E6", "text": "#1A1110"})
                    st.header(cat_name)
                    cat_tasks = [t for t in user_data["tasks"] if t["category"] == cat_name]
                    sorted_tasks = sorted(cat_tasks, key=lambda x: x['score'], reverse=True)

                    for t in sorted_tasks:
                        with st.container():
                            deadline_text = f"📅 Due: {t['deadline']}" if t['deadline'] else "No Deadline"
                            
                            st.markdown(f"""
                                <div style="background-color: {style['color']}; 
                                            width: 100%;
                                            padding: 15px; 
                                            border: 1px solid #3E2723;
                                            border-radius: 5px;
                                            margin-bottom: 5px;
                                            font-family: 'Georgia', serif;
                                            color: #1A1110;">
                                    <div style="border-bottom: 1px solid rgba(0,0,0,0.2); margin-bottom: 8px;">
                                        <span style="font-size: 0.7em; text-transform: uppercase;">{t['subcategory']}</span>
                                    </div>
                                    <div style="font-weight: bold; font-size: 1.1em; line-height: 1.2; margin-bottom: 15px;">
                                        {t['title']}
                                    </div>
                                    <div style="font-size: 0.7em; font-style: italic; color: #444;">
                                        {deadline_text}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("▶ Plan & Focus", key=f"btn_{t['id']}", use_container_width=True):
                                st.session_state.planner_active = True
                                st.session_state.planner_task_id = t['id']
                                st.rerun()

elif view == "Calendar":
    def change_month(amount):
        st.session_state.cal_month += amount
        if st.session_state.cal_month > 12:
            st.session_state.cal_month = 1
            st.session_state.cal_year += 1
        elif st.session_state.cal_month < 1:
            st.session_state.cal_month = 12
            st.session_state.cal_year -= 1

    year = st.session_state.cal_year
    month = st.session_state.cal_month
    month_name = calendar.month_name[month]

    col_prev, col_title, col_next = st.columns([1, 6, 1], vertical_alignment="center")
    
    with col_prev:
        if st.button("◀", key="cal_prev"):
            change_month(-1)
            st.rerun()
            
    with col_title:
        st.markdown(f"""<h1 style='text-align: center; font-size: 3.5rem; margin-bottom: 0px; color: #3E2723;'>{month_name} {year}</h1>""", unsafe_allow_html=True)
        
    with col_next:
        if st.button("▶", key="cal_next"):
            change_month(1)
            st.rerun()

    st.write("")

    deadline_map = {}
    for t in user_data["tasks"]:
        if t["deadline"]:
            d_str = t["deadline"].strftime("%Y-%m-%d") if isinstance(t["deadline"], date) else str(t["deadline"])
            if d_str not in deadline_map: deadline_map[d_str] = []
            cat_color = user_data["cat_styles"].get(t["category"], {}).get("color", "#FDF5E6")
            deadline_map[d_str].append({"title": t["title"], "color": cat_color, "cat": t["category"]})

    cal = calendar.Calendar(firstweekday=0) 
    month_days = cal.monthdayscalendar(year, month)
    
    cols = st.columns(7)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, d in enumerate(days):
        cols[i].markdown(f"<div style='text-align:center; font-weight:bold; color:#3E2723; margin-bottom:10px;'>{d}</div>", unsafe_allow_html=True)
    
    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown('<div style="height: 120px; background-color: rgba(255,255,255,0.1); border-radius: 5px; border: 1px dashed #D7CCC8;"></div>', unsafe_allow_html=True)
                else:
                    current_date_str = f"{year}-{month:02d}-{day:02d}"
                    today_obj = date.today()
                    is_today = (day == today_obj.day and month == today_obj.month and year == today_obj.year)
                    
                    bg_color = "#FDF5E6"
                    border = "1px solid #D7CCC8"
                    header_bg = "rgba(0,0,0,0.05)"
                    
                    if is_today:
                        bg_color = "#EFEBE9"
                        border = "2px solid #3E2723"
                        header_bg = "#D7CCC8"
                    
                    html_content = f"""<div style="height: 120px; background-color: {bg_color}; border: {border}; border-radius: 5px; padding: 0px; overflow-y: auto; overflow-x: hidden; display: flex; flex-direction: column;">"""
                    html_content += f"""<div style="background-color: {header_bg}; padding: 2px 5px; font-weight:bold; color:#3E2723; font-size: 0.9em; border-bottom: 1px solid rgba(0,0,0,0.1);">{day}</div><div style="padding: 2px;">"""
                    
                    if current_date_str in deadline_map:
                        for task in deadline_map[current_date_str]:
                            html_content += f"""<div style="background-color: {task['color']}; border: 1px solid rgba(0,0,0,0.1); border-left: 3px solid #3E2723; border-radius: 3px; padding: 3px; margin-bottom: 3px; font-size: 0.65em; line-height: 1.1; color: #1A1110; box-shadow: 1px 1px 2px rgba(0,0,0,0.1); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{task['title']}">{task['title']}</div>"""
                            
                    html_content += "</div></div>"
                    st.markdown(html_content, unsafe_allow_html=True)

elif view == "Reflection":
    st.title("🪞 Reflections & Analytics")
    
    history = user_data.get("history", [])
    
    total_minutes = 0
    mins_week = 0
    mins_month = 0
    
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    graph_data = []

    for t in history:
        t_mins = 0
        if "chunks" in t:
            for c in t["chunks"]:
                if isinstance(c, dict):
                    t_mins += c.get("minutes", 0)
                else:
                    t_mins += 25
        
        total_minutes += t_mins
        
        c_date_str = t.get("completed_date", str(today))
        try:
            c_date = datetime.strptime(c_date_str, "%Y-%m-%d").date()
        except:
            c_date = today

        if c_date >= start_of_week:
            mins_week += t_mins
        if c_date >= start_of_month:
            mins_month += t_mins
            
        graph_data.append({
            "Task": t['title'],
            "Category": t['category'],
            "Date": str(c_date),
            "Minutes": t_mins
        })

    # GAMIFICATION
    total_tasks = len(history)
    xp = (total_tasks * 50) + total_minutes
    level = int(xp / 500) + 1
    current_level_progress = (xp % 500) / 500

    col_profile, col_metrics = st.columns([1, 2], vertical_alignment="center")
    
    with col_profile:
        st.markdown(f"""
            <div style="background-color: #3E2723; color: #FDF5E6; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #D7CCC8; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);">
                <h1 style="margin:0; font-size: 3.5rem; color: #FDF5E6;">{level}</h1>
                <p style="margin:0; font-weight:bold; text-transform:uppercase; letter-spacing:1px;">Scholar Level</p>
                <hr style="border-color: #FDF5E6; opacity: 0.3; margin: 10px 0;">
                <h3 style="margin:0; color: #F0EAD6;">{xp} XP</h3>
            </div>
        """, unsafe_allow_html=True)
        
    with col_metrics:
        st.subheader("⏱️ Time Analysis")
        m1, m2, m3 = st.columns(3)
        
        def fmt_time(m):
            h = m // 60
            mn = m % 60
            return f"{h}h {mn}m"

        m1.metric("Lifetime", fmt_time(total_minutes), f"{total_tasks} Tasks")
        m2.metric("This Month", fmt_time(mins_month), "Total Focus")
        m3.metric("This Week", fmt_time(mins_week), "Since Mon")
        
        st.write("")
        st.caption(f"Progress to Level {level + 1}:")
        st.progress(current_level_progress)

    st.divider()

    # CHARTS (ALTAIR)
    if graph_data:
        st.subheader("📊 Visual Breakdown")
        df = pd.DataFrame(graph_data)
        
        tab_bar, tab_scatter = st.tabs(["Category Distribution", "Consistency Graph"])
        
        with tab_bar:
            st.caption("Total Minutes per Category")
            bar_chart = alt.Chart(df).mark_bar(color='#3E2723').encode(
                x=alt.X('Category', axis=alt.Axis(labelAngle=0)),
                y=alt.Y('sum(Minutes)', title='Total Minutes', axis=alt.Axis(titlePadding=15)),
                tooltip=['Category', 'sum(Minutes)']
            ).properties(height=320).configure_axis(grid=False, labelFont='Georgia', titleFont='Georgia').configure_view(strokeWidth=0)
            st.altair_chart(bar_chart, use_container_width=True)
            
        with tab_scatter:
            st.caption("Study Sessions over Time")
            scatter_chart = alt.Chart(df).mark_circle(size=100, opacity=0.8).encode(
                x=alt.X('Date', title='Date Completed'),
                y=alt.Y('Minutes', title='Minutes Focused', axis=alt.Axis(titlePadding=15)),
                color=alt.Color('Category', scale=alt.Scale(range=['#3E2723', '#5D4037', '#8D6E63', '#A1887F', '#D7CCC8'])),
                tooltip=['Task', 'Minutes', 'Category', 'Date']
            ).properties(height=320).configure_axis(labelFont='Georgia', titleFont='Georgia')
            st.altair_chart(scatter_chart, use_container_width=True)
            
    else:
        st.info("Complete some tasks to unlock your analytics graphs!")

    st.divider()

    st.subheader("🏆 The Archives")
    if not history:
        st.info("Your archives are empty.")
    else:
        for t in reversed(history):
            with st.container():
                st.markdown(f"""
                    <div style="background-color: #FDF5E6; border: 1px solid #D7CCC8; border-left: 5px solid #3E2723; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h3 style="margin:0; font-size:1.2rem; color:#3E2723;">{t['title']}</h3>
                            <span style="font-size:0.8em; font-weight:bold; color:#5D4037;">{t.get('completed_date', 'Unknown')}</span>
                        </div>
                        <div style="margin-top:8px; font-size:0.9em;">
                            <span style="background-color: rgba(62, 39, 35, 0.1); padding: 2px 8px; border-radius: 4px; color: #3E2723; font-weight: bold;">{t['category']}</span>
                            <span style="color: #3E2723;"> • {t['subcategory']}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                with st.expander("📜 Details"):
                    if "chunks" in t and t["chunks"]:
                        for c in t["chunks"]:
                            c_name = c["name"] if isinstance(c, dict) else str(c)
                            c_min = c.get("minutes", 25) if isinstance(c, dict) else 25
                            st.write(f"✅ {c_name} ({c_min}m)")
    
    st.divider()
    with st.expander("⚠️ Danger Zone"):
        if st.button("🗑️ Clear History"):
            user_data["history"] = []
            save_data(st.session_state.username, user_data)

            st.rerun()
