from app import app, render_template


@app.route('/admin/product')
def product():
    return render_template("admin/product.html")