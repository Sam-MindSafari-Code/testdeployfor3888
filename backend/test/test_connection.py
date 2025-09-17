# test_connection.py
from data.db_connection import get_conn

def main():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print("Connected successfully!")
            print("PostgreSQL version:", version["version"])
    finally:
        conn.close()

if __name__ == "__main__":
    main()
