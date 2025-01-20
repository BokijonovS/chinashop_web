import sqlite3
import os

def get_user(username):
    try:
        # Connect to the database
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../db.sqlite3')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute the SQL query to fetch the user
        cursor.execute("SELECT id, username, email, first_name, last_name FROM auth_user WHERE username = ?;", (username,))
        user = cursor.fetchone()

        # Close the connection
        conn.close()

        # Return a dictionary if the user exists
        if user:
            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "first_name": user[3],
                "last_name": user[4],
            }
        else:
            return None  # User not found
    except Exception as e:
        return {"error": str(e)}


def create_user(username, email=None, password=None, first_name=None, last_name=None):
    try:
        # Connect to the database
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../db.sqlite3')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insert the user into the database
        cursor.execute("""
            INSERT INTO auth_user (username, email, password, first_name, last_name, is_active, is_staff, is_superuser, date_joined)
            VALUES (?, ?, ?, ?, ?, 1, 0, 0, datetime('now'));
        """, (
            username,
            email or "",  # Convert None to ""
            password or "",  # Convert None to ""
            first_name or "",  # Convert None to ""
            last_name or ""  # Convert None to ""
        ))

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        return {"status": "success", "message": f"User '{username}' created successfully."}
    except sqlite3.IntegrityError as e:
        return {"status": "error", "message": "Username already exists."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def update_user(username, field, new_value):
    try:
        # Define the list of fields allowed to be updated
        allowed_fields = ["email", "password", "first_name", "last_name", "is_active", "is_staff", "is_superuser"]

        if field not in allowed_fields:
            return {"status": "error", "message": f"Field '{field}' cannot be updated."}

        # Connect to the database
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../db.sqlite3')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute the SQL update query
        query = f"UPDATE auth_user SET {field} = ? WHERE username = ?;"
        cursor.execute(query, (new_value, username))

        # Check if any row was affected
        if cursor.rowcount == 0:
            conn.close()
            return {"status": "error", "message": f"No user found with username '{username}'."}

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        return {"status": "success",
                "message": f"User '{username}' updated successfully. Field '{field}' set to '{new_value}'."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_user(user_id):
    user = get_user(username=user_id)
    if user['username'] and user['first_name'] and user['last_name'] and user['email']:
        return True
    else:
        return False

letters = "abcdefghijklmnopqrstuvwxyz '`"


def name_checker(name):
    name1 = str(name)
    for i in name1:
        if i.lower() not in letters:
            return False
    if name1.istitle() and len(name1) >= 4:
        return True
    else:
        return False