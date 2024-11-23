import os
import base64
import uuid
import logging
from flask import request, jsonify, render_template, send_from_directory
import mysql.connector
from app import app
from PIL import Image
from werkzeug.utils import secure_filename

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

app.config['CROPPED_FOLDER'] = 'static/images/cropped'
app.config['COMPRESSED_FOLDER'] = 'static/images/compressed'


# Route to display user page
@app.route('/admin/user')
def user():
    return render_template("admin/user.html")

def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


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
        print(image_data)

        original_image = request.files.get('original') or data.get('original')
        original_path = None
        print(original_image)

        def compress_image(image_file, save_path):
            image_file.seek(0, os.SEEK_END)  # Move pointer to the end to check the size
            file_size = image_file.tell()  # Get the size of the file in bytes

            print(file_size / 1024 / 1024)

            if file_size > 2 * 1024 * 1024:

                image_file.seek(0)  # Reset pointer back to the start before opening with Pillow
                img = Image.open(image_file)
                img = img.convert("RGB")  # Ensure it’s in RGB mode (needed for saving .jpeg)
                img.save(save_path, format='JPEG', quality=75)  # Save with reduced quality
                return True
            else:
                # If the file size is acceptable, save it directly
                image_file.seek(0)  # Reset pointer back to the start
                image_file.save(save_path)
                return False



        if image_data:
            if isinstance(image_data, str):  # Base64 string
                image_path = save_base64_image(image_data, app.config['CROPPED_FOLDER'])
                image_name = os.path.basename(image_path)
            else:  # File object
                filename = secure_filename(image_data.filename)
                image_path = os.path.join(app.config['CROPPED_FOLDER'], filename)
                image_data.save(image_path)
                image_name = filename

        if original_image:
            if isinstance(original_image, str):  # Base64 string
                original_path = save_base64_image(original_image, app.config['COMPRESSED_FOLDER'])
                image_name = os.path.basename(original_path)
            else:  # File object
                filename = secure_filename(original_image.filename)
                original_path = os.path.join(app.config['COMPRESSED_FOLDER'], filename)
                original_image.save(original_path)
                image_name = filename


        # Insert user into the database
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "INSERT INTO user (name, gender, phone, email, image) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (name, gender, phone, email, image_name))
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

@app.route('/delete_user/<int:id>', methods=['DELETE'])
def delete_user(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Fetch the image path for the user before deletion
        cursor.execute("SELECT image FROM user WHERE id = %s", (id,))
        user = cursor.fetchone()

        # If the user exists and has an image associated with it
        if user and user[0]:
            # Full path to image in cropped and compressed folders
            cropped_image_path = os.path.join('static', 'images', 'cropped', user[0])
            compressed_image_path = os.path.join('static', 'images', 'compressed', user[0])

            # Check if the image file exists in the cropped folder and delete it
            if os.path.exists(cropped_image_path):
                os.remove(cropped_image_path)

            # Check if the image file exists in the compressed folder and delete it
            if os.path.exists(compressed_image_path):
                os.remove(compressed_image_path)

        # Now, delete the user from the database
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
        # Parse form data
        data = request.form
        name = data.get('name')
        gender = data.get('gender')
        phone = data.get('phone')
        email = data.get('email')

        # Parse image data (file upload or Base64 string)
        image_data = request.files.get('image') or data.get('image')
        image_path = None

        original_image = request.files.get('original') or data.get('original')
        original_path = None

        def compress_image(image_file, save_path):
            image_file.seek(0, os.SEEK_END)  # Move pointer to the end to check the size
            file_size = image_file.tell()  # Get the size of the file in bytes

            if file_size > 2 * 1024 * 1024:
                image_file.seek(0)  # Reset pointer to start
                img = Image.open(image_file)
                img = img.convert("RGB")  # Convert to RGB
                img.save(save_path, format='JPEG', quality=75)  # Save with compression
                return True
            else:
                image_file.seek(0)  # Reset pointer
                image_file.save(save_path)  # Save without compression
                return False

        # Retrieve current user data
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user WHERE id = %s", (id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Handle new images
        if image_data:
            if isinstance(image_data, str):  # Base64 string
                image_path = save_base64_image(image_data, app.config['CROPPED_FOLDER'])
                image_name = os.path.basename(image_path)
            else:  # File object
                filename = secure_filename(image_data.filename)
                image_path = os.path.join(app.config['CROPPED_FOLDER'], filename)
                image_data.save(image_path)
                image_name = filename

                # Compress image if needed
                compressed_path = os.path.join(app.config['COMPRESSED_FOLDER'], filename)
                compress_image(image_data, compressed_path)

            # Delete old image if a new one is provided
            if user.get('image'):
                old_image_cropped = os.path.join(app.config['CROPPED_FOLDER'], user['image'])
                old_image_compressed = os.path.join(app.config['COMPRESSED_FOLDER'], user['image'])
                if os.path.exists(old_image_cropped):
                    os.remove(old_image_cropped)
                if os.path.exists(old_image_compressed):
                    os.remove(old_image_compressed)

        # Handle original images
        if original_image:
            filename = secure_filename(original_image.filename)
            original_path = os.path.join(app.config['COMPRESSED_FOLDER'], filename)
            original_image.save(original_path)

        # Update user data in the database
        query = """
        UPDATE user 
        SET name = %s, gender = %s, phone = %s, email = %s, image = %s 
        WHERE id = %s
        """
        cursor.execute(query, (
            name or user['name'],
            gender or user['gender'],
            phone or user['phone'],
            email or user['email'],
            image_name if image_data else user['image'],
            id
        ))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'User updated successfully'}), 200

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500



# Helper function to save Base64 image to "cropped" and "compressed" folders
def save_base64_image(base64_str, cropped_folder):
    try:
        # Ensure the cropped folder exists
        if not os.path.exists(cropped_folder):
            os.makedirs(cropped_folder)

        # Ensure the compressed folder exists
        compressed_folder = 'static/images/compressed/'
        if not os.path.exists(compressed_folder):
            os.makedirs(compressed_folder)

        # Decode the Base64 image
        image_data = base64.b64decode(base64_str.split(",")[1])
        file_name = f"{uuid.uuid4().hex}.jpg"

        #Save the image to the cropped folder
        cropped_path = os.path.join(cropped_folder, file_name)
        with open(cropped_path, "wb") as f:
            f.write(image_data)

        # Save the same image to the compressed folder

        return file_name
    except Exception as e:
        logging.error(f"Error saving Base64 image: {e}")
        raise


# Helper function to save uploaded file to "cropped" and "compressed" folders
def save_uploaded_file(uploaded_file, cropped_folder):
    try:
        # Ensure the cropped folder exists
        if not os.path.exists(cropped_folder):
            os.makedirs(cropped_folder)

        # Ensure the compressed folder exists
        compressed_folder = 'static/images/compressed/'
        if not os.path.exists(compressed_folder):
            os.makedirs(compressed_folder)

        # Generate a unique file name
        file_name = f"{uuid.uuid4().hex}.jpg"

        # Save the file to the cropped folder
        cropped_path = os.path.join(cropped_folder, file_name)
        uploaded_file.save(cropped_path)

        # Save the same file to the compressed folder
        compressed_path = os.path.join(compressed_folder, file_name)
        uploaded_file.save(compressed_path)

        return file_name
    except Exception as e:
        logging.error(f"Error saving uploaded file: {e}")
        raise

@app.route('/static/images/cropped/<filename>')
def serve_image(filename):
    return send_from_directory('static/images/cropped', filename)


# Main entry point
if __name__ == "__main__":
    app.run(debug=True)
