from app import app
import db
db.init_db()

if __name__ == "__main__":
    app.run()
