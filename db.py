import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "nutype.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)

    conn.commit()
    conn.close()


def create_project(name: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO projects (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def close_project(name: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE projects SET is_active = 0, closed_at = ? WHERE name = ? AND is_active = 1",
        (datetime.now(), name)
    )
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def get_active_projects() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, created_at FROM projects WHERE is_active = 1 ORDER BY created_at DESC")
    projects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return projects


def get_project_by_name(name: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def add_feedback(project_name: str, user_id: int, username: str, message: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM projects WHERE name = ? AND is_active = 1", (project_name,))
    project = cursor.fetchone()

    if not project:
        conn.close()
        return False

    cursor.execute(
        "INSERT INTO feedback (project_id, user_id, username, message) VALUES (?, ?, ?, ?)",
        (project["id"], user_id, username, message)
    )
    conn.commit()
    conn.close()
    return True


def get_feedback_for_project(project_name: str) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT f.username, f.message, f.created_at
        FROM feedback f
        JOIN projects p ON f.project_id = p.id
        WHERE p.name = ?
        ORDER BY f.created_at ASC
    """, (project_name,))

    feedback = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return feedback


init_db()
