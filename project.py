import streamlit as st
import pandas as pd
import os
import datetime
import time

# --- 1. Enhanced UI Configuration ---
st.set_page_config(page_title="Academic Performance Hub", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; color: #333; }
    .stMetric { background: #f8f9fa; padding: 15px; border-radius: 10px; border-bottom: 3px solid #007bff; }
    .admin-box { background: #fff3cd; padding: 15px; border-radius: 10px; border: 1px solid #ffeeba; margin-bottom: 20px; }
    .timer-card { background: #e9ecef; padding: 25px; border-radius: 15px; text-align: center; border: 2px solid #007bff; }
    .timer-text { font-size: 55px; font-weight: bold; color: #007bff; }
    </style>
    """, unsafe_allow_html=True)

# Database Files
SUB_FILE = "subjects_v11.csv"
LOG_FILE = "logs_v11.csv"
USER_FILE = "users_v11.csv"

def load_data(file, cols):
    if os.path.exists(file):
        df = pd.read_csv(file)
        return df.fillna("")
    return pd.DataFrame(columns=cols)

def save_data(df, file):
    df.to_csv(file, index=False)

# --- 2. Authentication ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("📚 Student Hub Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Sign In"):
        users = load_data(USER_FILE, ["username", "password"])
        if u == "somwshamsddin" or ((users['username'] == u) & (users['password'] == p)).any():
            st.session_state.logged_in, st.session_state.username = True, u
            st.rerun()
    if st.button("Create Account"):
        users = load_data(USER_FILE, ["username", "password"])
        if u and u not in users['username'].values:
            save_data(pd.concat([users, pd.DataFrame([{"username": u, "password": p}])]), USER_FILE)
            st.success("Account created! Please login.")
else:
    # Load Data
    subs_df = load_data(SUB_FILE, ["user", "subject", "code", "doctor", "units", "p1_s", "p1_t", "p2_s", "p2_t", "fin_s", "fin_t", "difficulty"])
    logs_df = load_data(LOG_FILE, ["user", "subject", "date", "text", "duration"])
    
    # --- 3. Admin Functionality (For somwshamsddin) ---
    if st.session_state.username == "somwshamsddin":
        with st.container():
            st.markdown('<div class="admin-box">👑 <b>Admin Dashboard (somwshamsddin)</b></div>', unsafe_allow_html=True)
            users_list = load_data(USER_FILE, ["username"])
            st.write(f"Registered Students ({len(users_list)}):")
            st.info(", ".join(users_list['username'].tolist()))
            st.divider()

    # User Context
    user_subs = subs_df[subs_df['user'] == st.session_state.username]
    user_logs = logs_df[logs_df['user'] == st.session_state.username]

    # --- 4. Dashboard Header ---
    col_h1, col_h2 = st.columns([2, 1])
    with col_h1: st.title(f"🚀 Academic Dashboard")
    with col_h2: 
        if st.button("Logout"): 
            st.session_state.logged_in = False
            st.rerun()

    m1, m2, m3 = st.columns(3)
    total_units = pd.to_numeric(user_subs['units'], errors='coerce').sum()
    m1.metric("Total Credits", int(total_units))
    today_time = pd.to_numeric(user_logs[user_logs['date'] == str(datetime.date.today())]['duration'], errors='coerce').sum()
    m2.metric("Study Today", f"{today_time:.1f} m")
    m3.metric("My Subjects", len(user_subs))

    st.divider()

    # --- 5. Add & Manage Subjects (The Organized Way) ---
    t1, t2 = st.tabs(["📊 View & Edit Subjects", "➕ Add New Subject"])

    with t2:
        with st.form("add_subject_form"):
            st.subheader("Add a New Course")
            c1, c2, c3 = st.columns(3)
            sub_name = c1.text_input("Subject Name")
            sub_code = c2.text_input("Code")
            sub_doc = c3.text_input("Doctor")
            
            c4, c5 = st.columns(2)
            sub_units = c4.number_input("Units", 1, 10, 3)
            sub_diff = c5.select_slider("Difficulty Level", options=["Easy", "Medium", "Hard"])
            if st.form_submit_button("Add to System"):
                if sub_name:
                    new_sub = pd.DataFrame([{
                        "user": st.session_state.username, "subject": sub_name, "code": sub_code, 
                        "doctor": sub_doc, "units": sub_units, "difficulty": sub_diff,
                        "p1_s": 0.0, "p1_t": 30.0, "p2_s": 0.0, "p2_t": 30.0, "fin_s": 0.0, "fin_t": 40.0
                    }])
                    save_data(pd.concat([subs_df, new_sub]), SUB_FILE)
                    st.rerun()

    with t1:
        if not user_subs.empty:
            st.subheader("Your Enrolled Courses")
            for idx, row in user_subs.iterrows():
                # Color Coding for Difficulty
                diff_color = "🟢" if row['difficulty'] == "Easy" else "🟡" if row['difficulty'] == "Medium" else "🔴"
                
                with st.expander(f"{diff_color} {row['subject']} ({row['code']}) - Click to Adjust"):
                    with st.form(f"edit_form_{idx}"):
                        st.write("📝 **General Info**")
                        e1, e2, e3 = st.columns(3)
                        en = e1.text_input("Name", row['subject'])
                        ec = e2.text_input("Code", row['code'])
                        ed = e3.text_input("Doctor", row['doctor'])
                        
                        st.write("🎯 **Grades & Predictions**")
                        g1, g2, g3 = st.columns(3)
                        p1_val = g1.number_input("Mid 1 Score", value=float(row['p1_s']))
                        p2_val = g2.number_input("Mid 2 Score", value=float(row['p2_s']))
                        fn_val = g3.number_input("Final Score", value=float(row['fin_s']))
                        
                        st.write("⚖️ **Assessment**")
                        diff_val = st.selectbox("Update Difficulty", ["Easy", "Medium", "Hard"], index=["Easy", "Medium", "Hard"].index(row['difficulty'] if row['difficulty'] else "Medium"))
                        
                        btn_c1, btn_c2 = st.columns(2)
                        if btn_c1.form_submit_button("💾 Save Changes"):
                            subs_df.loc[idx, ['subject', 'code', 'doctor', 'p1_s', 'p2_s', 'fin_s', 'difficulty']] = [en, ec, ed, p1_val, p2_val, fn_val, diff_val]
                            save_data(subs_df, SUB_FILE)
                            st.rerun()
                        if btn_c2.form_submit_button("🗑️ Remove"):
                            subs_df = subs_df.drop(idx)
                            save_data(subs_df, SUB_FILE)
                            st.rerun()
        else:
            st.info("Start by adding a subject in the 'Add New Subject' tab.")

    st.divider()

    # --- 6. Predictions & Stopwatch ---
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.subheader("🔮 Grade Archive")
        if not user_subs.empty:
            st.table(user_subs[["subject", "p1_s", "p2_s", "fin_s", "difficulty"]].rename(columns={"subject":"Subject", "difficulty":"Level"}))

    with c_right:
        st.subheader("⏱️ Focus Timer")
        if 'tm_on' not in st.session_state: st.session_state.tm_on = False
        if 'tm_sec' not in st.session_state: st.session_state.tm_sec = 0

        target_sub = st.selectbox("Focus on:", user_subs['subject'].tolist() if not user_subs.empty else ["None"])
        
        col_t1, col_t2, col_t3 = st.columns(3)
        if col_t1.button("▶️ Start"): st.session_state.tm_on = True
        if col_t2.button("⏸️ Pause"): st.session_state.tm_on = False
        if col_t3.button("⏹️ Save"):
            dur = round(st.session_state.tm_sec / 60, 2)
            new_log = pd.DataFrame([{"user": st.session_state.username, "subject": target_sub, "date": str(datetime.date.today()), "text": "Session", "duration": dur}])
            save_data(pd.concat([logs_df, new_log]), LOG_FILE)
            st.session_state.tm_on = False
            st.session_state.tm_sec = 0
            st.rerun()

        # Timer Display
        timer_box = st.empty()
        while st.session_state.tm_on:
            st.session_state.tm_sec += 1
            timer_box.markdown(f'<div class="timer-card"><div class="timer-text">{str(datetime.timedelta(seconds=st.session_state.tm_sec))}</div><div>Focusing... 🎯</div></div>', unsafe_allow_html=True)
            time.sleep(1)
        if not st.session_state.tm_on:
            timer_box.markdown(f'<div class="timer-card"><div class="timer-text" style="color: #6c757d;">{str(datetime.timedelta(seconds=st.session_state.tm_sec))}</div><div>Paused</div></div>', unsafe_allow_html=True)

    st.divider()

    # --- 7. Weekly Table ---
    st.subheader("📅 Weekly Status Updates")
    if not user_subs.empty:
        with st.expander("Write a new update"):
            with st.form("up_form"):
                u_sub = st.selectbox("Subject", user_subs['subject'].tolist())
                u_txt = st.text_area("Note")
                if st.form_submit_button("Post Update"):
                    new_ent = pd.DataFrame([{"user": st.session_state.username, "subject": u_sub, "date": str(datetime.date.today()), "text": u_txt, "duration": 0}])
                    save_data(pd.concat([logs_df, new_ent]), LOG_FILE)
                    st.rerun()
        
        view_logs = user_logs[user_logs['text'] != "Session"].iloc[::-1]
        if not view_logs.empty:
            st.table(view_logs[["date", "subject", "text"]])