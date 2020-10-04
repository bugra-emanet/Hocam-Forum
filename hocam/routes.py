# Hocam is a basic forumpage restricted to metu/odtü students
# Created by: Buğra Emanet
# My email account: bugra01emanet@gmail.com
import os
import datetime
from hocam import app, db, bcrypt
from hocam.functions import (localizetime, save_picture,
                             generate_token, confirm_token, send_mail)
from flask import (render_template, flash, redirect,
                   url_for, request, abort)
from hocam.forms import (RegistirationForm, LoginForm,
                         UpdateForm, NewForumPageForm,
                         PostForm, ResendConfirmationForm,
                         ForgetPasswordForm, RenewPasswordForm)
from hocam.models import User, ForumPages, Posts
from flask_login import (login_user, logout_user,
                         login_required, current_user)
from sqlalchemy.exc import OperationalError


@app.route("/")
@app.route("/home")
def home():
    # homepage where people will see the current topics in descending order
    try:
        forumpages = ForumPages.query.order_by(ForumPages.date_created.desc())
        forumpages = forumpages.all()
    except OperationalError:
        # incase there are no topics in the datapage
        forumpages = None
    return render_template("index.html", forumpages=forumpages,
                           localizetime=localizetime)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        # if the user is already logged in return to home
        return redirect(url_for("home"))

    if form.validate_on_submit():  # if the form is valid
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,
                                               form.password.data):
            # if the user exists and the password is correct
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            # next is the page you want to access
            # but can't because you are not logged in
            # if next_page exists (for example if you wanted to
            #  access the profile page but you were not logged in)
            # after logging in redirect to there if it does not exist
            #  redirect to home
            return (redirect(next_page) if next_page
                    else redirect(url_for("home")))
        else:
            # if login unsuccessful
            flash("Login Unsuccessful.Please check email and password.",
                  "danger")
    return render_template("login.html", title="Login", form=form)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = RegistirationForm()
    if form.validate_on_submit():
        # create password hash from password
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        hashed_password = hashed_password.decode("utf-8")
        # create user object from the form data
        user = User(username=form.username.data, email=form.email.data,
                    password=hashed_password)
        # add the user object to database
        db.session.add(user)
        db.session.commit()
        flash("Your account has been created!", "success")
        # generate token for the email authentication
        token = generate_token(user.email)
        # necessary parameters to send the mail:
        confirm_url = url_for("confirm_email", token=token, _external=True)
        template = render_template('message_activate.html',
                                   confirm_url=confirm_url)
        subject = "Please confirm your email"
        # send the mail with the token
        send_mail(recipients=user.email,
                  subject=subject,
                  template=template,
                  sender=app.config["MAIL_DEFAULT_SENDER"])
        flash('A confirmation email has been sent via email.', 'success')
        # redirect  the newly registered user to the login page
        return redirect(url_for("login"))
    return render_template("signup.html", title="Sign up!",
                           form=form)


# basic logout manager
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
            # delete the old image file unless it is the default pic
            if current_user.image_file != "default.png":
                os.remove(url_for("static", filename="profile_pics")
                          + current_user.image_file)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        db.session.commit()
        flash("Account Update Succesfull", "success")
        return redirect(url_for("profile"))
    elif request.method == "GET":
        # if the user wants the see the page
        form.username.data = current_user.username
    image_file = url_for("static",
                         filename="profile_pics/" + current_user.image_file)
    return render_template("profile.html", form=form, image_file=image_file)


@app.route("/forumpage/new", methods=["GET", "POST"])
@login_required
def newforumpage():
    form = NewForumPageForm()
    if form.validate_on_submit():
        # create new forumpage object according
        # to the data from the dorm add it to the database
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


@app.route("/forumpage/<forumpage_id>", methods=["GET", "POST"])
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
    # pagination
    page = request.args.get("page", 1, type=int)
    # find the posts that belong to the forumpage
    posts = Posts.query.filter_by(forumpage=forumpage.id)
    # latest post to oldest
    posts = posts.order_by(Posts.date_created.desc())
    # 5 posts per page
    posts = posts.paginate(page=page, per_page=5)
    return render_template("forumpagelayout.html", forumpage=forumpage,
                           form=form, title=forumpage.topic, posts=posts,
                           localizetime=localizetime)


@login_required
@app.route("/forumpage/<forumpage_id>/post/<post_id>/edit",
           methods=["GET", "POST"])
def editpost(forumpage_id, post_id):
    form = PostForm()
    post = Posts.query.get_or_404(post_id)
    forumpage = ForumPages.query.get_or_404(forumpage_id,
                                            description="No such page!")
    if forumpage_id != post.forumpage:
        # if the forumpage id doesnt match the forumpage of the post
        abort(404)
    if post.author != current_user and not current_user.admin:
        # if the post was not written by
        # the current_user or the current_user is not an admin
        abort(403)
    if form.validate_on_submit():
        post.content = form.comment.data
        db.session.commit()
        flash("Your post has been edited!", "success")
        return redirect(url_for("showforumpage", forumpage_id=forumpage.id))
    elif request.method == "GET":
        # when the user wants to see the editpage
        form.comment.data = post.content
    # pagination
    page = request.args.get("page", 1, type=int)
    # get the posts for the current forumpage
    posts = Posts.query.filter_by(forumpage=forumpage.id)
    # posts latest to oldest
    posts = posts.order_by(Posts.date_created.desc())
    # 5 posts per page
    posts = posts.paginate(page=page, per_page=5)
    return render_template("editforumpagelayout.html", forumpage=forumpage,
                           form=form, title=forumpage.topic, posts=posts,
                           localizetime=localizetime)


@login_required
@app.route("/forumpage/<forumpage_id>/post/<post_id>/delete",
           methods=["POST"])
def delete_post(forumpage_id, post_id):
    post = Posts.query.get_or_404(post_id)
    if forumpage_id != post.forumpage:
        # if the forumpage id doesnt match the forumpage of the post
        abort(404)
    if post.author != current_user and not current_user.admin:
        # if the post was not written by
        # the current_user or the current_user is not an admin
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
        # if the user already confirmed his/her email
        flash('Account already confirmed. Please login.', 'success')
    if not confirm_token(token):
        # if the confirmation link is invalid
        flash('The confirmation link is invalid or has expired.', 'danger')
    else:  # if the confirmation link is not invalid
        # make user confirmed and update the database
        user.confirmed = True
        user.confirmed_on = datetime.datetime.now()
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('home'))


# if the confirmation token expired before the user can confirm his/her email
@login_required
@app.route("/resendconfirmation", methods=["GET", "POST"])
def resend_confirmation():
    form = ResendConfirmationForm()
    form.email.data = current_user.email
    if form.validate_on_submit() and form.email.data == current_user.email:
        # generate token from email
        token = generate_token(form.email.data)
        # neccessary parameters for the send_mail function
        # (check out function.py )
        confirm_url = url_for("confirm_email", token=token, _external=True)
        template = render_template('message_activate.html',
                                   confirm_url=confirm_url)
        subject = "Please confirm your email"
        # sending the mail
        send_mail(recipients=current_user.email,
                  subject=subject,
                  template=template,
                  sender=app.config["MAIL_DEFAULT_SENDER"])
        flash('A confirmation email has been sent via email.', 'success')
    return render_template("resendconfirmation.html", form=form,
                           title="resendconfirmation")


@app.route("/forgetpassword", methods=["GET", "POST"])
def forget_password():
    if current_user.is_authenticated:
        # if the user is logged in
        return redirect(url_for("home"))
    form = ForgetPasswordForm()
    if form.validate_on_submit():
        # get user from the email
        user = User.query.filter_by(email=form.email.data).first()
        # generate token from the email
        token = generate_token(user.email)
        # neccessary parameters for the send_mail function
        # (check out function.py )
        confirm_url = url_for("reset_password", token=token, _external=True)
        template = render_template('message_new_password.html',
                                   confirm_url=confirm_url)
        subject = "Hocam Password Reset"
        # sending the mail
        send_mail(recipients=user.email,
                  subject=subject,
                  template=template,
                  sender=app.config["MAIL_DEFAULT_SENDER"])
        flash("Password reset email has been sent!", "info")

    return render_template("resetrequest.html", form=form,
                           title="Reset Your Password")


@app.route("/forgetpassword/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        # if the user is logged in
        return redirect(url_for("home"))
    if not confirm_token(token):
        # if the token is invalid
        flash("That is an invalid/expired token!", "warning")
        return redirect(url_for("forget_password"))
    # get the user by email
    # (if the token is valid confirm_token
    # function returns the email of the user)
    user = User.query.filter_by(email=confirm_token(token)).first()
    form = RenewPasswordForm()
    if form.validate_on_submit():
        # generate hash from the new password
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        hashed_password = hashed_password.decode("utf-8")
        # change user's password to the new password
        user.password = hashed_password
        # commit the changes to the database
        db.session.commit()
        flash("Your password has been changed!", "success")
        return redirect(url_for("login"))

    return render_template("resetpassword.html", form=form,
                           title="Reset Your Password")


@login_required
@app.route("/forumpage/<forumpage_id>/description/edit",
           methods=["GET", "POST"])
def editdescription(forumpage_id):
    form = PostForm()
    forumpage = ForumPages.query.get_or_404(forumpage_id,
                                            description="No such page!")
    if forumpage.creator != current_user and not current_user.admin:
        # if the description was not written by
        # the current_user aor current_user is not an admin
        abort(403)
    if form.validate_on_submit():
        # change the description and commit the changes
        forumpage.description = form.comment.data
        db.session.commit()
        flash("Your description has been edited!", "success")
        return redirect(url_for("showforumpage", forumpage_id=forumpage.id))
    elif request.method == "GET":
        # when the user views the page
        form.comment.data = forumpage.description
    # pagination
    page = request.args.get("page", 1, type=int)
    # get the posts for the current forumpage
    posts = Posts.query.filter_by(forumpage=forumpage.id)
    # posts latest to oldest
    posts = posts.order_by(Posts.date_created.desc())
    # 5 posts per page
    posts = posts.paginate(page=page, per_page=5)
    return render_template("editforumpagelayout_description.html",
                           forumpage=forumpage,
                           form=form, title=forumpage.topic, posts=posts,
                           localizetime=localizetime)


@login_required
@app.route("/forumpage/<forumpage_id>/delete",
           methods=["POST"])
def delete_description(forumpage_id):
    forumpage = ForumPages.query.get_or_404(forumpage_id)
    if forumpage.creator != current_user and not current_user.admin:
        # if the forumpage was not created
        # by current_user or current_user is not an admin
        abort(403)
    # delete the description
    forumpage.description = None
    db.session.commit()
    flash("Your description has been deleted!", "success")
    return redirect(url_for("showforumpage", forumpage_id=forumpage.id))


# special route for admins
# newly created admins (admins will be created manually
# using the create_admin_user function)
# will have the change their assigned password
# ( if the user already exists
# this will not be necessary)
@app.route("/renewpassword/<token>",
           methods=["GET", "POST"])
def admin_user_renew_password(token):
    if not confirm_token(token):
        # if the token is invalid
        flash("That is an invalid/expired token!", "warning")
        return redirect(url_for("login"))
    form = RenewPasswordForm()
    user = User.query.filter_by(email=confirm_token(token)).first()
    if not user.admin:
        # if the user is not an admin
        abort(403)
    if form.validate_on_submit():
        # create  hash from the new password
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        hashed_password = hashed_password.decode("utf-8")
        # change the password in the database and commit the changes
        user.password = hashed_password
        db.session.commit()
        flash("Your password has been changed!", "success")
        return redirect(url_for("login"))

    return render_template("resetpassword.html", form=form,
                           title="Reset Your Password")
