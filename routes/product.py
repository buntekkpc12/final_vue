from app import app, render_template
from flask import request, jsonify, redirect, url_for
import mysql.connector
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join('static', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='pos_final'
    )
    return connection


@app.route('/admin/product')
def product():
    return render_template("admin/product.html")


@app.route('/add_product', methods=['POST'])
def add_product():
    try:
        code = request.form.get('code')
        name = request.form.get('name')
        category = request.form.get('category')
        cost = request.form.get('cost')
        price = request.form.get('price')
        current_stock = request.form.get('current_stock')

        image_file = request.files.get('image')
        filename = None

        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO product (code, image, name, category, cost, price, current_stock)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (code, filename, name, category, float(cost), float(price), int(current_stock)))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'Product added successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_products', methods=['GET'])
def get_products():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM product")
        products = cursor.fetchall()

        cursor.close()
        connection.close()
        return jsonify(products), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/update_product/<int:id>', methods=['PUT'])
def update_product(id):
    try:
        code = request.form.get('code')
        name = request.form.get('name')
        category = request.form.get('category')
        cost = request.form.get('cost')
        price = request.form.get('price')
        current_stock = request.form.get('current_stock')

        image_file = request.files.get('image')
        filename = None

        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        UPDATE product SET code = %s, name = %s, category = %s, cost = %s, price = %s, current_stock = %s
        """ + (", image = %s" if filename else "") + " WHERE id = %s"

        if filename:
            cursor.execute(query, (code, name, category, float(cost), float(price), int(current_stock), filename, id))
        else:
            cursor.execute(query, (code, name, category, float(cost), float(price), int(current_stock), id))

        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'Product updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/delete_product/<int:id>', methods=['DELETE'])
def delete_product(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = "DELETE FROM product WHERE id = %s"
        cursor.execute(query, (id,))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'Product deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
