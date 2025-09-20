import mysql.connector
from mysql.connector import Error
import pandas as pd

# --- Database Connection ---
def create_connection():
    """
    Create a database connection.
    This function will raise an exception if the connection fails.
    """
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",      # IMPORTANT: Replace with your MySQL username
            password="1155",  # IMPORTANT: Replace with your MySQL password
            database="pms_system"
        )
        return connection
    except Error as e:
        # Re-raise the exception to be caught by the frontend
        raise ConnectionError(f"Failed to connect to the database: {e}") from e

# --- Test Connection ---
def test_db_connection():
    """Tests if a connection to the database can be established."""
    try:
        conn = create_connection()
        conn.close()
        return True, "Connection successful."
    except ConnectionError as e:
        return False, str(e)

# --- User Management ---
def verify_user(email, password):
    """Verify user credentials and return user info."""
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM employees WHERE email = %s AND password = %s"
    cursor.execute(query, (email, password))
    user = cursor.fetchone()
    conn.close()
    return user

def get_employees_by_manager(manager_id):
    """Fetch all employees reporting to a specific manager."""
    conn = create_connection()
    query = "SELECT employee_id, name FROM employees WHERE manager_id = %s"
    df = pd.read_sql(query, conn, params=(manager_id,))
    conn.close()
    return df

# --- Goal Management ---
def get_employee_goals(employee_id):
    """Fetch all goals for a specific employee."""
    conn = create_connection()
    query = "SELECT * FROM goals WHERE employee_id = %s ORDER BY due_date ASC"
    df = pd.read_sql(query, conn, params=(employee_id,))
    conn.close()
    return df

def add_goal(employee_id, title, description, due_date):
    """Add a new goal for an employee."""
    conn = create_connection()
    cursor = conn.cursor()
    query = "INSERT INTO goals (employee_id, title, description, due_date) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (employee_id, title, description, due_date))
    conn.commit()
    conn.close()

def update_goal_status(goal_id, status):
    """Update the status of a goal."""
    conn = create_connection()
    cursor = conn.cursor()
    query = "UPDATE goals SET status = %s WHERE goal_id = %s"
    cursor.execute(query, (status, goal_id))
    conn.commit()
    conn.close()

# --- Task Management ---
def get_tasks_for_goal(goal_id):
    """Fetch all tasks for a specific goal."""
    conn = create_connection()
    query = "SELECT * FROM tasks WHERE goal_id = %s"
    df = pd.read_sql(query, conn, params=(goal_id,))
    conn.close()
    return df

def add_task(goal_id, description):
    """Add a new task for a goal."""
    conn = create_connection()
    cursor = conn.cursor()
    query = "INSERT INTO tasks (goal_id, description) VALUES (%s, %s)"
    cursor.execute(query, (goal_id, description))
    conn.commit()
    conn.close()

def update_task_status(task_id, status):
    """Update the status of a task."""
    conn = create_connection()
    cursor = conn.cursor()
    query = "UPDATE tasks SET status = %s WHERE task_id = %s"
    cursor.execute(query, (status, task_id))
    conn.commit()
    conn.close()

# --- Feedback Management ---
def get_feedback_for_goal(goal_id):
    """Fetch all feedback for a specific goal."""
    conn = create_connection()
    query = """
    SELECT f.feedback_text, f.created_at, e.name as manager_name
    FROM feedback f
    JOIN employees e ON f.manager_id = e.employee_id
    WHERE f.goal_id = %s
    ORDER BY f.created_at DESC
    """
    df = pd.read_sql(query, conn, params=(goal_id,))
    conn.close()
    return df

def add_feedback(goal_id, manager_id, feedback_text):
    """Add new feedback for a goal."""
    conn = create_connection()
    cursor = conn.cursor()
    query = "INSERT INTO feedback (goal_id, manager_id, feedback_text) VALUES (%s, %s, %s)"
    cursor.execute(query, (goal_id, manager_id, feedback_text))
    conn.commit()
    conn.close()
