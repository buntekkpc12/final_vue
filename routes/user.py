from app import app, render_template
from flask import request, jsonify
import mysql.connector


def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='pos_final'
    )
    return connection


@app.route('/admin/user')
def user():
    return render_template("admin/user.html")


@app.route('/add_user', methods=['POST'])
def add_user():
    try:
        data = request.get_json()
        print(f"Received data: {data}")
        name = data.get('name')
        gender = data.get('gender')
        phone = data.get('phone')
        email = data.get('email')

        print(f"name: {name}, gender: {gender}, phone: {phone}, email: {email}")

        connection = get_db_connection()
        cursor = connection.cursor()

        query = "INSERT INTO user (name, gender, phone, email) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (name, gender, phone, email))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'User added successfully'}), 201

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500


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
        print(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500


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
        print(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/update_user/<int:id>', methods=['PUT'])
def update_user(id):
    try:
        data = request.get_json()
        name = data.get('name')
        gender = data.get('gender')
        phone = data.get('phone')
        email = data.get('email')

        connection = get_db_connection()
        cursor = connection.cursor()

        query = "UPDATE user SET name = %s, gender = %s, phone = %s, email = %s WHERE id = %s"
        cursor.execute(query, (name, gender, phone, email, id))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'User updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
