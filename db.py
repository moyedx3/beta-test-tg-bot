import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    USE_POSTGRES = True
else:
    import sqlite3
    from pathlib import Path
    DB_PATH = Path(__file__).parent / "nutype.db"
    USE_POSTGRES = False


def get_connection():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def get_cursor(conn):
    if USE_POSTGRES:
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        return conn.cursor()


def placeholder():
    return "%s" if USE_POSTGRES else "?"


def init_db():
    conn = get_connection()
    cursor = get_cursor(conn)

    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id),
                user_id BIGINT NOT NULL,
                username TEXT,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
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
    cursor.close()
    conn.close()


def create_project(name: str) -> bool:
    conn = get_connection()
    cursor = get_cursor(conn)
    p = placeholder()
    try:
        cursor.execute(f"INSERT INTO projects (name) VALUES ({p})", (name,))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def close_project(name: str) -> bool:
    conn = get_connection()
    cursor = get_cursor(conn)
    p = placeholder()
    is_active_val = True if USE_POSTGRES else 1
    is_inactive_val = False if USE_POSTGRES else 0
    cursor.execute(
        f"UPDATE projects SET is_active = {p}, closed_at = {p} WHERE name = {p} AND is_active = {p}",
        (is_inactive_val, datetime.now(), name, is_active_val)
    )
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected > 0


def get_active_projects() -> list[dict]:
    conn = get_connection()
    cursor = get_cursor(conn)
    p = placeholder()
    is_active_val = True if USE_POSTGRES else 1
    cursor.execute(
        f"SELECT name, created_at FROM projects WHERE is_active = {p} ORDER BY created_at DESC",
        (is_active_val,)
    )
    rows = cursor.fetchall()
    projects = [dict(row) for row in rows]
    cursor.close()
    conn.close()
    return projects


def get_project_by_name(name: str) -> dict | None:
    conn = get_connection()
    cursor = get_cursor(conn)
    p = placeholder()
    cursor.execute(f"SELECT * FROM projects WHERE name = {p}", (name,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None


def add_feedback(project_name: str, user_id: int, username: str, message: str) -> bool:
    conn = get_connection()
    cursor = get_cursor(conn)
    p = placeholder()
    is_active_val = True if USE_POSTGRES else 1

    cursor.execute(
        f"SELECT id FROM projects WHERE name = {p} AND is_active = {p}",
        (project_name, is_active_val)
    )
    project = cursor.fetchone()

    if not project:
        cursor.close()
        conn.close()
        return False

    project_id = project["id"] if USE_POSTGRES else project["id"]
    cursor.execute(
        f"INSERT INTO feedback (project_id, user_id, username, message) VALUES ({p}, {p}, {p}, {p})",
        (project_id, user_id, username, message)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True


def get_feedback_for_project(project_name: str) -> list[dict]:
    conn = get_connection()
    cursor = get_cursor(conn)
    p = placeholder()

    cursor.execute(f"""
        SELECT f.username, f.message, f.created_at
        FROM feedback f
        JOIN projects p ON f.project_id = p.id
        WHERE p.name = {p}
        ORDER BY f.created_at ASC
    """, (project_name,))

    rows = cursor.fetchall()
    feedback = [dict(row) for row in rows]
    cursor.close()
    conn.close()
    return feedback


init_db()
