from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db_connection, create_table


app = Flask(__name__)


# =========================================================
# CREATE DATABASE TABLE
# =========================================================

create_table()


# =========================================================
# HOME API
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "message": "Flask User API is running successfully"
    }), 200


# =========================================================
# REGISTER API
# =========================================================

@app.route("/api/register", methods=["POST"])
def register():

    # Get JSON data
    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    # Get user details
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")
    confirm_password = data.get("confirm_password")

    # Check required fields
    if not email or not phone or not password or not confirm_password:

        return jsonify({
            "message": "Email, phone, password and confirm_password are required"
        }), 400

    # Check password confirmation
    if password != confirm_password:

        return jsonify({
            "message": "Passwords do not match"
        }), 400

    # Basic phone validation
    if not phone.isdigit() or len(phone) != 10:

        return jsonify({
            "message": "Phone number must contain exactly 10 digits"
        }), 400

    # Password length validation
    if len(password) < 8:

        return jsonify({
            "message": "Password must contain at least 8 characters"
        }), 400

    connection = get_db_connection()

    try:

        # Check whether email already exists
        existing_email = connection.execute("""
            SELECT id
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        if existing_email:

            connection.close()

            return jsonify({
                "message": "Email already exists"
            }), 409

        # Check whether phone already exists
        existing_phone = connection.execute("""
            SELECT id
            FROM users
            WHERE phone = ?
        """, (phone,)).fetchone()

        if existing_phone:

            connection.close()

            return jsonify({
                "message": "Phone number already exists"
            }), 409

        # Hash password
        hashed_password = generate_password_hash(password)

        # Insert user into database
        connection.execute("""
            INSERT INTO users (email, phone, password)
            VALUES (?, ?, ?)
        """, (
            email,
            phone,
            hashed_password
        ))

        connection.commit()

        connection.close()

        return jsonify({
            "message": "User registered successfully"
        }), 201

    except Exception as error:

        connection.close()

        return jsonify({
            "message": "Registration failed",
            "error": str(error)
        }), 500


# =========================================================
# LOGIN API
# =========================================================

@app.route("/api/login", methods=["POST"])
def login():

    # Get JSON data
    data = request.get_json()

    if not data:

        return jsonify({
            "message": "Request body is required"
        }), 400

    # Get login details
    email = data.get("email")
    password = data.get("password")

    # Check required fields
    if not email or not password:

        return jsonify({
            "message": "Email and password are required"
        }), 400

    connection = get_db_connection()

    # Find user by email
    user = connection.execute("""
        SELECT id, email, phone, password
        FROM users
        WHERE email = ?
    """, (email,)).fetchone()

    connection.close()

    # Email does not exist
    if user is None:

        return jsonify({
            "message": "Invalid email or password"
        }), 401

    # Verify password against stored hash
    if not check_password_hash(user["password"], password):

        return jsonify({
            "message": "Invalid email or password"
        }), 401

    # Login successful
    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "phone": user["phone"]
        }
    }), 200


# =========================================================
# GET ALL USERS
# =========================================================

@app.route("/api/users", methods=["GET"])
def get_users():

    connection = get_db_connection()

    users = connection.execute("""
        SELECT id, email, phone
        FROM users
    """).fetchall()

    connection.close()

    user_list = []

    for user in users:

        user_list.append({
            "id": user["id"],
            "email": user["email"],
            "phone": user["phone"]
        })

    return jsonify({
        "users": user_list
    }), 200


# =========================================================
# GET USER BY ID
# =========================================================

@app.route("/api/user/<int:user_id>", methods=["GET"])
def get_user(user_id):

    connection = get_db_connection()

    user = connection.execute("""
        SELECT id, email, phone
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    connection.close()

    if user is None:

        return jsonify({
            "message": "User not found"
        }), 404

    return jsonify({
        "id": user["id"],
        "email": user["email"],
        "phone": user["phone"]
    }), 200


# =========================================================
# UPDATE USER
# =========================================================

@app.route("/api/user/<int:user_id>", methods=["PUT"])
def update_user(user_id):

    data = request.get_json()

    if not data:

        return jsonify({
            "message": "Request body is required"
        }), 400

    email = data.get("email")
    phone = data.get("phone")

    # Check required fields
    if not email or not phone:

        return jsonify({
            "message": "Email and phone are required"
        }), 400

    # Validate phone
    if not phone.isdigit() or len(phone) != 10:

        return jsonify({
            "message": "Phone number must contain exactly 10 digits"
        }), 400

    connection = get_db_connection()

    # Check whether user exists
    user = connection.execute("""
        SELECT id
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if user is None:

        connection.close()

        return jsonify({
            "message": "User not found"
        }), 404

    # Check whether another user already has this email
    existing_email = connection.execute("""
        SELECT id
        FROM users
        WHERE email = ?
        AND id != ?
    """, (email, user_id)).fetchone()

    if existing_email:

        connection.close()

        return jsonify({
            "message": "Email already exists"
        }), 409

    # Check whether another user already has this phone
    existing_phone = connection.execute("""
        SELECT id
        FROM users
        WHERE phone = ?
        AND id != ?
    """, (phone, user_id)).fetchone()

    if existing_phone:

        connection.close()

        return jsonify({
            "message": "Phone number already exists"
        }), 409

    # Update user
    connection.execute("""
        UPDATE users
        SET email = ?, phone = ?
        WHERE id = ?
    """, (
        email,
        phone,
        user_id
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "message": "User updated successfully"
    }), 200


# =========================================================
# DELETE USER
# =========================================================

@app.route("/api/user/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):

    connection = get_db_connection()

    # Check whether user exists
    user = connection.execute("""
        SELECT id
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if user is None:

        connection.close()

        return jsonify({
            "message": "User not found"
        }), 404

    # Delete user
    connection.execute("""
        DELETE FROM users
        WHERE id = ?
    """, (user_id,))

    connection.commit()
    connection.close()

    return jsonify({
        "message": "User deleted successfully"
    }), 200


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )