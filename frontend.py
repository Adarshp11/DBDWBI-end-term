import streamlit as st
import pandas as pd
import importlib

# --- Step 1: Basic App Setup ---
st.set_page_config(layout="wide", page_title="Performance Management System")
st.title("System Startup Diagnostics")

# --- Step 2: Attempt to Import Backend ---
st.write("🔄 **Step 1:** Initializing frontend...")
backend_module = None
try:
    import backend as be
    backend_module = be
    st.success("✅ **Step 1:** Frontend initialized successfully.")
except ImportError as e:
    st.error(f"❌ **CRITICAL ERROR:** Could not import the `backend.py` file. Make sure it's in the same folder as `frontend.py`. Details: {e}")
    st.stop()
except Exception as e:
    st.error(f"❌ **CRITICAL ERROR:** An error occurred when importing `backend.py`. Check the file for syntax errors. Details: {e}")
    st.stop()

# --- Step 3: Test Database Connection ---
st.write("🔄 **Step 2:** Checking database connection...")
if backend_module:
    can_connect, error_message = backend_module.test_db_connection()

    if not can_connect:
        st.error(f"❌ **Step 2 FAILED:** Could not connect to the database.")
        st.subheader("Error Details:")
        st.code(error_message, language='text')

        st.subheader("🚨 How to Fix This 🚨")
        st.warning("""
        This is the most common issue. Please follow these steps carefully:

        1.  **Is your MySQL Server Running?**
            * Open MySQL Workbench, XAMPP, or whichever tool you use.
            * Ensure the database server is **ON** and active.

        2.  **Check Your Credentials in `backend.py`:**
            * Open the `backend.py` file.
            * Verify that `user="your_username"` and `password="your_password"` are **exactly** correct for your MySQL setup.
            * A common username for local setups is `root`.

        3.  **Confirm Database and Tables Exist:**
            * In MySQL Workbench, check that the `pms_system` database exists.
            * Run the `pms_system.sql` script again if you are unsure.
        """)
        st.stop() # Stop the app from running further.
    else:
        st.success("✅ **Step 2:** Database connection successful!")
else:
    st.error("Cannot test database connection because backend failed to load.")
    st.stop()


# --- If all checks pass, clear the diagnostics and run the app ---
st.empty() # Clears the diagnostic messages
# We use st.session_state to ensure the main app logic runs only after checks are passed.
if 'checks_passed' not in st.session_state:
    st.session_state.checks_passed = True
    st.rerun()


# ===================================================================================
# MAIN APPLICATION LOGIC (Only runs if the checks above are successful)
# ===================================================================================

# --- User Authentication ---
if 'user' not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("Performance Management System Login")
    col1, col2 = st.columns([1, 2])
    with col1:
        email = st.text_input("Email", "alice@example.com")
        password = st.text_input("Password", type="password", value="password")
        if st.button("Login", use_container_width=True):
            try:
                user = be.verify_user(email, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Invalid email or password")
            except Exception as e:
                st.error(f"An error occurred during login: {e}")
    st.stop()

# --- Main Application UI ---
user = st.session_state.user
st.sidebar.title(f"Welcome, {user['name']}!")
st.sidebar.write(f"**Role:** {user['role'].capitalize()}")
if st.sidebar.button("Logout"):
    st.session_state.user = None
    del st.session_state.checks_passed # Reset checks on logout
    st.rerun()

# --- Manager View ---
if user['role'] == 'manager':
    st.title("Manager Dashboard")
    team = be.get_employees_by_manager(user['employee_id'])
    
    if team.empty:
        st.warning("You have no employees assigned to you.")
        st.stop()
    
    selected_employee_name = st.sidebar.selectbox("Select Employee", team['name'])
    selected_employee_id = team[team['name'] == selected_employee_name]['employee_id'].iloc[0]
    
    st.sidebar.markdown("---")
    menu = ["View Performance", "Add New Goal", "Performance Report"]
    choice = st.sidebar.radio("Menu", menu)

    st.header(f"Managing: {selected_employee_name}")

    if choice == "View Performance":
        # ... (Rest of the manager view code is identical to the previous version) ...
        goals = be.get_employee_goals(selected_employee_id)
        if goals.empty:
            st.info(f"{selected_employee_name} has no goals assigned yet.")
        else:
            for _, goal in goals.iterrows():
                with st.expander(f"Goal: {goal['title']} (Due: {goal['due_date']}) | Status: {goal['status']}", expanded=True):
                    st.write(f"**Description:** {goal['description']}")
                    
                    status_options = ['Not Started', 'In Progress', 'Completed', 'On Hold']
                    current_status_index = status_options.index(goal['status'])
                    new_status = st.selectbox("Update Status", options=status_options, index=current_status_index, key=f"status_{goal['goal_id']}")
                    if st.button("Save Status", key=f"save_{goal['goal_id']}"):
                        be.update_goal_status(goal['goal_id'], new_status)
                        st.success("Status updated!")
                        st.rerun()

                    st.subheader("Tasks Logged by Employee")
                    tasks = be.get_tasks_for_goal(goal['goal_id'])
                    if not tasks.empty:
                        for _, task in tasks.iterrows():
                            task_col, btn_col1, btn_col2 = st.columns([4, 1, 1])
                            with task_col:
                                st.write(f"- {task['description']} (Status: **{task['status']}**)")
                            if task['status'] == 'Pending':
                                with btn_col1:
                                    if st.button("Approve", key=f"approve_{task['task_id']}", use_container_width=True):
                                        be.update_task_status(task['task_id'], "Approved")
                                        st.rerun()
                                with btn_col2:
                                    if st.button("Reject", key=f"reject_{task['task_id']}", use_container_width=True):
                                        be.update_task_status(task['task_id'], "Rejected")
                                        st.rerun()
                    else:
                        st.write("No tasks logged for this goal yet.")

                    st.subheader("Provide & View Feedback")
                    with st.form(f"feedback_form_{goal['goal_id']}"):
                        feedback_text = st.text_area("Your Feedback", key=f"fb_text_{goal['goal_id']}")
                        if st.form_submit_button("Submit Feedback"):
                            if feedback_text:
                                be.add_feedback(goal['goal_id'], user['employee_id'], feedback_text)
                                st.success("Feedback submitted!")
                                st.rerun()
                    
                    feedback = be.get_feedback_for_goal(goal['goal_id'])
                    if not feedback.empty:
                        for _, fb in feedback.iterrows():
                            st.info(f"**{fb['manager_name']}** ({fb['created_at'].strftime('%Y-%m-%d %H:%M')}): {fb['feedback_text']}")
    # ... (Add New Goal and Performance Report sections are also identical) ...
    elif choice == "Add New Goal":
        with st.form("new_goal_form"):
            st.subheader(f"Add a New Goal for {selected_employee_name}")
            title = st.text_input("Goal Title")
            description = st.text_area("Description")
            due_date = st.date_input("Due Date")
            if st.form
