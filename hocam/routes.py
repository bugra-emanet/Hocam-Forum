import secrets
import os
from hocam import app, db, bcrypt
from flask import (render_template, flash, redirect, 
                   url_for, request, session)
from hocam.forms import RegistirationForm, LoginForm, UpdateForm, NewForumPageForm
from hocam.models import User, ForumPages
from flask_login import login_user, logout_user, login_required, current_user
from PIL import Image


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,
                                               form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("home"))
        else:
            flash("Login Unsuccessful.Please check email and password.",
                  "danger")
    return render_template("login.html", title="Login",form=form)

@app.route("/signup", methods=["GET","POST"])
def signup():
    form = RegistirationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        hashed_password = hashed_password.decode("utf-8")
        user = User(username=form.username.data, email=form.email.data,
                    password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Your account has been created!", "success")
        return redirect(url_for("login"))
    return render_template("signup.html", title="Sign up!",
                           form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, "static/profile_pics",picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

   


@app.route("/profile", methods=["GET","POST"])
@login_required
def profile():
    form = UpdateForm()
    if form.validate_on_submit():
        if form.image.data:
            picture_file = save_picture(form.image.data)
            if current_user.image_file != "default.png":
                os.remove("hocam/static/profile_pics/" + current_user.image_file)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        db.session.commit()
        flash("Account Update Succesfull", "success")
        return redirect(url_for("profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
    image_file = url_for("static", filename="profile_pics/" + current_user.image_file)
    return render_template("profile.html", form=form, image_file=image_file)


@app.route("/forumpage/new",methods=["GET","POST"])
@login_required
def newforumpage():
    global furl
    form = NewForumPageForm()
    if form.validate_on_submit():
        forumpage = ForumPages(topic=form.topic.data, 
                               description=form.description.data, 
                               user_id=current_user.id)
           
        generated_url = f'forumpage/{forumpage.topic}'
        forumpage.url = generated_url
        furl = forumpage.url
        db.session.add(forumpage)
        db.session.commit()
        flash("Topic Creation Succesfull!", "success")
        
        
    return render_template("newforumpage.html",form=form)

for formpages in ForumPages.query:
    @app.route("/<url>")
    def createurl(url):
        url = formpages.url
        return "f"

