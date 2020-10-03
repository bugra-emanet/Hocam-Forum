import os
import datetime
from hocam import app, db, bcrypt
from hocam.functions import (localizetime, save_picture,
                             generate_token, confirm_token, send_mail)
from flask import (render_template, flash, redirect,
                   url_for, request, abort)
from hocam.forms import (RegistirationForm, LoginForm,
                         UpdateForm, NewForumPageForm,
                         PostForm, ResendConformationForm)
from hocam.models import User, ForumPages, Posts
from flask_login import (login_user, logout_user,
                         login_required, current_user)


@app.route("/")
@app.route("/home")
def home():
    forumpages = ForumPages.query.order_by(ForumPages.date_created.desc())
    forumpages = forumpages.all()
    return render_template("index.html", forumpages=forumpages,
                           localizetime=localizetime)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for("home"))

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
        token = generate_token(user.email)
        confirm_url = url_for("confirm_email", token=token, _external=True)
        template = render_template('message_activate.html',
                                   confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_mail(recipients=user.email,
                  subject=subject,
                  template=template,
                  sender=app.config["MAIL_DEFAULT_SENDER"])
        login_user(user)
        flash('A confirmation email has been sent via email.', 'success')
        logout_user()
        return redirect(url_for("login"))
    return render_template("signup.html", title="Sign up!",
                           form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


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
                               date_created=datetime.datetime.now(
                                            datetime.timezone.utc),
                               user_id=current_user.id)
        db.session.add(forumpage)
        db.session.commit()
        flash("Topic Creation Succesfull!", "success")
        return redirect(url_for("showforumpage",
                        forumpage_id=forumpage.query.filter_by
                        (topic=form.topic.data).first().id))
    return render_template("newforumpage.html", form=form)


@app.route("/forumpage/<int:forumpage_id>", methods=["GET", "POST"])
def showforumpage(forumpage_id):
    form = PostForm()
    forumpage = ForumPages.query.get_or_404(forumpage_id,
                                            description="No such page!")
    if form.validate_on_submit():
        post = Posts(content=form.comment.data, user_id=current_user.id,
                     date_created=datetime.datetime.now(
                                  datetime.timezone.utc),
                     forumpage=forumpage_id)
        db.session.add(post)
        db.session.commit()
        flash("Posted", "success")
        return redirect(url_for('showforumpage', forumpage_id=forumpage.id))
    page = request.args.get("page", 1, type=int)
    posts = Posts.query.filter_by(forumpage=forumpage.id)
    posts = posts.order_by(Posts.date_created.desc())
    posts = posts.paginate(page=page, per_page=5)
    return render_template("forumpagelayout.html", forumpage=forumpage,
                           form=form, title=forumpage.topic, posts=posts,
                           localizetime=localizetime)


@login_required
@app.route("/forumpage/<int:forumpage_id>/post/<int:post_id>/edit",
           methods=["GET", "POST"])
def editpost(forumpage_id, post_id):
    form = PostForm()
    post = Posts.query.get_or_404(post_id)
    forumpage = ForumPages.query.get_or_404(forumpage_id,
                                            description="No such page!")
    if forumpage_id != post.forumpage:
        abort(404)
    if post.author != current_user:
        abort(403)

    if form.validate_on_submit():
        post.content = form.comment.data
        db.session.commit()
        flash("Your post has been edited!", "success")
        return redirect(url_for("showforumpage", forumpage_id=forumpage.id))
    elif request.method == "GET":
        form.comment.data = post.content
    page = request.args.get("page", 1, type=int)
    posts = Posts.query.filter_by(forumpage=forumpage.id)
    posts = posts.order_by(Posts.date_created.desc())
    posts = posts.paginate(page=page, per_page=5)
    return render_template("editforumpagelayout.html", forumpage=forumpage,
                           form=form, title=forumpage.topic, posts=posts,
                           localizetime=localizetime)


@login_required
@app.route("/forumpage/<int:forumpage_id>/post/<int:post_id>/delete",
           methods=["POST"])
def delete_post(forumpage_id, post_id):
    post = Posts.query.get_or_404(post_id)
    if forumpage_id != post.forumpage:
        abort(404)
    if post.author != current_user:
        abort(403)
    forumpage = post.forumpage
    db.session.delete(post)
    db.session.commit()
    flash("Your post has been deleted!", "success")
    return redirect(url_for("showforumpage", forumpage_id=forumpage))


@app.route('/confirm/<token>')
@login_required
def confirm_email(token):
    email = confirm_token(token)
    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        flash('Account already confirmed. Please login.', 'success')
    if not confirm_token(token):
        flash('The confirmation link is invalid or has expired.', 'danger')
    else:
        user.confirmed = True
        user.confirmed_on = datetime.datetime.now()
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('home'))


@login_required
@app.route("/resendconformation", methods=["GET", "POST"])
def resend_conformation():
    form = ResendConformationForm()
    form.email.data = current_user.email
    if form.validate_on_submit():
        token = generate_token(form.email.data)
        confirm_url = url_for("confirm_email", token=token, _external=True)
        template = render_template('message_activate.html',
                                   confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_mail(recipients=current_user.email,
                  subject=subject,
                  template=template,
                  sender=app.config["MAIL_DEFAULT_SENDER"])
        flash('A confirmation email has been sent via email.', 'success')
    return render_template("resendconformation.html", form=form,
                           title="resendconformation")
