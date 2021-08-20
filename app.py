import os
from flask import (
    Flask, g, Blueprint, flash, render_template, redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from bson import json_util
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/home")
def home():
    return render_template('home.html')


@app.route("/")
# route function to render the explore page
@app.route("/get_blogs")
def get_blogs():
    blogs = list(mongo.db.blogs.find())
    return render_template("blogs.html", blogs=blogs)


# function to render the post page
@app.route("/get_posts")
def get_posts():
    posts = list(mongo.db.posts.find())
    return render_template("post.html", posts=posts)


# create a register route function
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


# login  route function
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for(
                            "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


# create profile route function
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


# add / create blogs
@app.route("/add_blog", methods=["GET", "POST"])
def add_blog():
    if request.method == "POST":
        blog = {
            "category_name": request.form.get("category_name"),
            "title": request.form.get("title"),
            "content": request.form.get("content"),
            "img_url": request.form.get("img_url"),
            "published_date": request.form.get("published_date"),
            "tags": request.form.get("tags"),
            "read_time": request.form.get("read_time"),
            "created_by": session['user']
        }
        mongo.db.blogs.insert_one(blog)
        flash('Blog Successfully Added')
        return redirect(url_for("get_blogs"))
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template('add_blog.html', categories=categories)


# edit/update blog function
@app.route("/edit_blog/<blog_id>", methods=["GET", "POST"])
def edit_blog(blog_id):
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name"),
            "title": request.form.get("title"),
            "content": request.form.get("content"),
            "img_url": request.form.get("img_url"),
            "published_date": request.form.get("published_date"),
            "tags": request.form.get("tags"),
            "read_time": request.form.get("read_time"),
            "created_by": session['user']
        }
        mongo.db.blogs.update({"_id": ObjectId(blog_id)}, submit)
        flash('Blog Successfully Updated')

    blog = mongo.db.blogs.find_one({"_id": ObjectId(blog_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template('edit_blog.html', blog=blog, categories=categories)


# delete blog function
@app.route("/delete_blog/<blog_id>")
def delete_blog(blog_id):
    mongo.db.blogs.remove({"_id": ObjectId(blog_id)})
    flash('Blog  has been Successfully deleted!')
    return redirect(url_for("get_blogs"))


# create blog categories
@app.route("/get_categories")
def get_categories():
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template("categories.html", categories=categories)


# add blog categories
@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    """ if the function is called using the post method
    then grab data from the form and insert it into the databse,
    otherwise the default method of get displays the empty form
    available to the admin.
    """
    if request.method == "POST":
        category = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.insert_one(category)
        flash('New Category Added!')
        return redirect(url_for("get_categories"))

    return render_template("add_category.html")


# edit/update category
@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.update({"_id": ObjectId(category_id)}, submit)
        flash("Category SuccessfullY Updated")
        return redirect(url_for("get_categories"))
    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template("edit_category.html", category=category)


# error pages
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out!")
    session.pop("user")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
