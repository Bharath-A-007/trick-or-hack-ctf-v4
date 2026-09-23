import sys
import getpass
from werkzeug.security import generate_password_hash
import db
from db import get_conn

def main():
    if len(sys.argv) != 2:
        print("Usage: python create_admin.py <username>")
        sys.exit(1)
    username = sys.argv[1]
    pw = getpass.getpass("New password for admin '%s': " % username)
    pw2 = getpass.getpass("Confirm password: ")
    if pw != pw2:
        print("Passwords do not match.")
        sys.exit(1)
    if len(pw) < 8:
        print("Password must be at least 8 characters.")
        sys.exit(1)
    db.init_db()
    conn = get_conn()
    try:
        conn.execute("INSERT INTO admins (username, password_hash) VALUES (?,?)",
                     (username, generate_password_hash(pw)))
        conn.commit()
        print(f"Admin '{username}' created.")
    except Exception as e:
        print("Error (username may already exist):", e)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
