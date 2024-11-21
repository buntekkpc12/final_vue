import os
import base64
import uuid
import logging
from flask import request, jsonify, render_template, send_from_directory
import mysql.connector
from app import app  # Import app from your main app file

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='pos_final'
    )

# Route to display user page
@app.route('/admin/user')
def user():
    return render_template("admin/user.html")

# Add new user
@app.route('/add_user', methods=['POST'])
def add_user():
    try:
        # Parse form data
        data = request.form
        name = data.get('name')
        gender = data.get('gender')
        phone = data.get('phone')
        email = data.get('email')

        # Parse image data (file upload or Base64 string)
        image_data = request.files.get('image') or data.get('image')
        image_path = None

        if image_data and isinstance(image_data, str):
            # Save Base64 image
            image_path = save_base64_image(image_data, 'static/images/cropped/')
        elif image_data:
            # Save file upload
            image_path = save_uploaded_file(image_data, 'static/images/cropped/')

        # Insert user into the database
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "INSERT INTO user (name, gender, phone, email, image) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (name, gender, phone, email, image_path))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'User added successfully'}), 201

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500

# Get all users
@app.route('/get_users', methods=['GET'])
def get_users():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        cursor.close()
        connection.close()
        return jsonify(users), 200

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500

# Delete user by ID
@app.route('/delete_user/<int:id>', methods=['DELETE'])
def delete_user(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = "DELETE FROM user WHERE id = %s"
        cursor.execute(query, (id,))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'User deleted successfully'}), 200

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500

# Update user by ID
@app.route('/update_user/<int:id>', methods=['PUT'])
def update_user(id):
    try:
        data = request.form
        name = data.get('name')
        gender = data.get('gender')
        phone = data.get('phone')
        email = data.get('email')

        # Handle image upload and save the image file name
        image_data = request.files.get('image') or data.get('image')  # Check if the image is a file or Base64
        image_path = None

        if image_data and isinstance(image_data, str):
            # Base64 Image
            image_path = save_base64_image(image_data, 'static/images/cropped/')
        elif image_data:
            # File Upload
            image_filename = image_data.filename
            image_path = f'static/images/cropped/{image_filename}'
            image_data.save(os.path.join(current_app.root_path, image_path))

        # Connect to database and update user data
        connection = get_db_connection()
        cursor = connection.cursor()

        if image_path:
            # Delete old image if there's a new one
            cursor.execute("SELECT image FROM user WHERE id = %s", (id,))
            old_image_path = cursor.fetchone()
            if old_image_path and os.path.exists(old_image_path[0]):
                os.remove(old_image_path[0])  # Delete old image

            # Update user with the new image
            query = "UPDATE user SET name = %s, gender = %s, phone = %s, email = %s, image = %s WHERE id = %s"
            cursor.execute(query, (name, gender, phone, email, image_path, id))
        else:
            # Update user without changing the image if no new image is uploaded
            query = "UPDATE user SET name = %s, gender = %s, phone = %s, email = %s WHERE id = %s"
            cursor.execute(query, (name, gender, phone, email, id))

        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({
            'message': 'User updated successfully',
            'image': image_path  # Send back the new image path to update the frontend
        }), 200

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500
# Helper function to save Base64 image
def save_base64_image(base64_str, folder):
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
        image_data = base64.b64decode(base64_str.split(",")[1])
        file_name = f"{uuid.uuid4().hex}.png"
        file_path = os.path.join(folder, file_name)
        with open(file_path, "wb") as f:
            f.write(image_data)
        return file_name  # Return just the filename
    except Exception as e:
        logging.error(f"Error saving Base64 image: {e}")
        raise

def save_uploaded_file(uploaded_file, folder):
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
        file_name = f"{uuid.uuid4().hex}_{uploaded_file.filename}"
        file_path = os.path.join(folder, file_name)
        uploaded_file.save(file_path)
        return file_name  # Return just the filename
    except Exception as e:
        logging.error(f"Error saving uploaded file: {e}")
        raise


@app.route('/static/images/cropped/<filename>')
def serve_image(filename):
    return send_from_directory('static/images/cropped', filename)

# Main entry point
if __name__ == "__main__":
    app.run(debug=True)
