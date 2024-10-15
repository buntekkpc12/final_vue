from app import app, render_template


@app.route('/admin/category')
def category():
    return render_template("admin/category.html")