import sqlite3
import json
from pathlib import Path

# ============================================================
# NEXT BEST DOLLAR
# LOCAL PERSISTENT STORAGE
#
# Prototype storage using SQLite.
# Data remains available after the app closes.
# ============================================================

DB_PATH = Path(__file__).with_name("next_best_dollar.db")


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS app_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            state_json TEXT NOT NULL
        )
    """)
    return connection


def default_state():
    return {
        "onboarding_complete": False,
        "personal_complete": False,
        "behavioral_complete": False,
        "financial_complete": False,

        "personal": {},
        "personal_scores": {},

        "behavioral": {},
        "behavior_scores": {},

        "financial": {},
        "financial_metrics": {},

        "goals": [],
        "next_best_actions": [],
    }


def load_state():
    connection = get_connection()

    row = connection.execute(
        "SELECT state_json FROM app_state WHERE id = 1"
    ).fetchone()

    if row is None:
        state = default_state()
        save_state(state)
        connection.close()
        return state

    try:
        stored = json.loads(row[0])
    except Exception:
        stored = {}

    state = default_state()
    state.update(stored)

    connection.close()
    return state


def save_state(state):
    connection = get_connection()

    payload = json.dumps(state)

    connection.execute(
        """
        INSERT INTO app_state (id, state_json)
        VALUES (1, ?)
        ON CONFLICT(id) DO UPDATE SET state_json = excluded.state_json
        """,
        (payload,)
    )

    connection.commit()
    connection.close()


def reset_state():
    state = default_state()
    save_state(state)
    return state
