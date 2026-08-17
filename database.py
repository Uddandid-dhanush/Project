import sqlite3


DATABASE_NAME = "users.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE_NAME)

    # Allows us to access columns by name
    connection.row_factory = sqlite3.Row

    return connection


def create_table():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()