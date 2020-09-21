import pandas as pd
import secrets
import os
from hocam import app, db, bcrypt
from flask import (render_template, flash, redirect,
                   url_for, request)
from hocam.forms import (RegistirationForm, LoginForm,
                         UpdateForm,
                         NewForumPageForm,
                         NewPostForm)
from hocam.models import User, ForumPages
from flask_login import (login_user, logout_user,
                         login_required, current_user)
from PIL import Image
from hocam.errors import HttpException404


@app.route("/")
def home():
    topics = ForumPages.query.all()
    urls = ForumPages.query.all()
    topics = [forumpages.topic for forumpages in topics]
    urls = [forumpages.id for forumpages in urls]
    urls = [f"{url_for('home')}forumpage/{url}" for url in urls]
    values = pd.DataFrame()
    values["topic"] = topics
    values["url"] = urls
    values = values[["topic", "url"]]
    values = list(values.itertuples(index=False, name=None))
    if len(values) == 0:
        truth = False
    else:
        truth = True

    return render_template("index.html", values=values, truth=truth)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,
                                               form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return (redirect(next_page) if next_page
                    else redirect(url_for("home")))
        else:
            flash("Login Unsuccessful.Please check email and password.",
                  "danger")
    return render_template("login.html", title="Login", form=form)


@app.route("/signup", methods=["GET", "POST"])
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
    picture_path = os.path.join(app.root_path, "static/profile_pics",
                                picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = UpdateForm()
    if form.validate_on_submit():
        if form.image.data:
            picture_file = save_picture(form.image.data)
            if current_user.image_file != "default.png":
                os.remove("hocam/static/profile_pics/"
                          + current_user.image_file)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        db.session.commit()
        flash("Account Update Succesfull", "success")
        return redirect(url_for("profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
    image_file = url_for("static",
                         filename="profile_pics/" + current_user.image_file)
    return render_template("profile.html", form=form, image_file=image_file)


@app.route("/forumpage/new", methods=["GET", "POST"])
@login_required
def newforumpage():
    form = NewForumPageForm()
    if form.validate_on_submit():
        forumpage = ForumPages(topic=form.topic.data,
                               description=form.description.data,
                               user_id=current_user.id)
        db.session.add(forumpage)
        db.session.commit()
        flash("Topic Creation Succesfull!", "success")
        return redirect(url_for("show_forumpage",
                        forumpage_id=forumpage.query.filter_by
                        (topic=form.topic.data).first().id))
    return render_template("newforumpage.html", form=form)


@app.route("/forumpage/<int:forumpage_id>", methods=["GET", "POST"])
def show_forumpage(forumpage_id):
    try:
        form = NewPostForm()
        forumpage = ForumPages.get_or_404(forumpage_id)
        return render_template("forumpagelayout.html", forumpage=forumpage,
                               form=form)
    except HttpException404:
        return render_template("404error.html")
