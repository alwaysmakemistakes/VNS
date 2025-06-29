import psycopg2
import os

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD", "")
    )
    return conn

def create_audit_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_events (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            event_type TEXT NOT NULL,
            payload JSONB
        )
    """)
    conn.commit()
    cur.close()
    conn.close()