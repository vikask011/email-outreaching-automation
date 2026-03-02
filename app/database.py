import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse, parse_qs
from app.config import DATABASE_URL


def get_connection():
    url = DATABASE_URL.strip()

    # Fix common prefix issue
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # Parse URL manually to extract clean components psycopg2 can handle
    parsed = urlparse(url)
    conn_params = {
        "host":     parsed.hostname,
        "port":     parsed.port or 5432,
        "dbname":   parsed.path.lstrip("/"),
        "user":     parsed.username,
        "password": parsed.password,
        "sslmode":  "require",
    }

    return psycopg2.connect(**conn_params)


def init_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS email_logs (
                    id SERIAL PRIMARY KEY,
                    recipient_name TEXT,
                    recipient_email TEXT NOT NULL,
                    subject TEXT,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    sent_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
        conn.commit()
    finally:
        conn.close()


def log_email(recipient_name: str, recipient_email: str, subject: str, status: str, error_message: str = None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO email_logs (recipient_name, recipient_email, subject, status, error_message)
                VALUES (%s, %s, %s, %s, %s)
            """, (recipient_name, recipient_email, subject, status, error_message))
        conn.commit()
    finally:
        conn.close()


def get_all_logs(limit: int = 200):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, recipient_name, recipient_email, subject, status, error_message,
                       TO_CHAR(sent_at AT TIME ZONE 'Asia/Kolkata', 'DD Mon YYYY, HH12:MI AM') AS sent_at
                FROM email_logs
                ORDER BY sent_at DESC
                LIMIT %s
            """, (limit,))
            return cur.fetchall()
    finally:
        conn.close()


def get_stats():
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'sent')   AS total_sent,
                    COUNT(*) FILTER (WHERE status = 'failed') AS total_failed,
                    COUNT(*) AS total
                FROM email_logs
            """)
            return cur.fetchone()
    finally:
        conn.close()