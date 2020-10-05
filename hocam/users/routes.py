
# Hocam is a basic forumpage restricted to metu/odtü students
# Created by: Buğra Emanet
# My email account: bugra01emanet@gmail.com
import os
import datetime
from flask import Blueprint, current_app
from hocam import db, bcrypt
from hocam.users.functions import (save_picture,
                                   generate_token, confirm_token, send_mail)
from flask import (render_template, flash, redirect,
                   url_for, request)
from hocam.users.forms import (RegistirationForm, LoginForm,
                               UpdateForm, ResendConfirmationForm,
                               ForgetPasswordForm, RenewPasswordForm)
from hocam.models import User
from flask_login import (login_user, logout_user,
                         login_required, current_user)


users = Blueprint("users", __name__)


@users.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        # if the user is already logged in return to home
        return redirect(url_for("main.home"))

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
                    else redirect(url_for("main.home")))
        else:
            # if login unsuccessful
            flash("Login Unsuccessful.Please check email and password.",
                  "danger")
    return render_template("login.html", title="Login", form=form)


@users.route("/signup", methods=["GET", "POST"])
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
        confirm_url = url_for("users.confirm_email",
                              token=token, _external=True)
        template = render_template('message_activate.html',
                                   confirm_url=confirm_url)
        subject = "Please confirm your email"
        # send the mail with the token
        send_mail(to_email=user.email,
                  subject=subject,
                  template=template,
                  from_email=current_app.config["MAIL_DEFAULT_SENDER"]
                  )
        flash('A confirmation email has been sent via email.', 'success')
        # redirect  the newly registered user to the login page
        return redirect(url_for("users.login"))
    return render_template("signup.html", title="Sign up!",
                           form=form)


# basic logout manager
@users.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.home"))


@users.route("/profile", methods=["GET", "POST"])
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
        return redirect(url_for("users.profile"))
    elif request.method == "GET":
        # if the user wants the see the page
        form.username.data = current_user.username
    image_file = url_for("static",
                         filename="profile_pics/" + current_user.image_file)
    return render_template("profile.html", form=form, image_file=image_file)


@users.route('/confirm/<token>')
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
    return redirect(url_for('main.home'))


# if the confirmation token expired before the user can confirm his/her email
@login_required
@users.route("/resendconfirmation", methods=["GET", "POST"])
def resend_confirmation():
    form = ResendConfirmationForm()
    form.email.data = current_user.email
    if form.validate_on_submit() and form.email.data == current_user.email:
        # generate token from email
        token = generate_token(form.email.data)
        # neccessary parameters for the send_mail function
        # (check out function.py )
        confirm_url = url_for("users.confirm_email", token=token,
                              _external=True)
        template = render_template('message_activate.html',
                                   confirm_url=confirm_url)
        subject = "Please confirm your email"
        # sending the mail
        send_mail(to_email=current_user.email,
                  subject=subject,
                  template=template,
                  from_email=current_app.config["MAIL_DEFAULT_SENDER"]
                  )
        flash('A confirmation email has been sent via email.', 'success')
    return render_template("resendconfirmation.html", form=form,
                           title="resendconfirmation")


@users.route("/forgetpassword", methods=["GET", "POST"])
def forget_password():
    if current_user.is_authenticated:
        # if the user is logged in
        return redirect(url_for("main.home"))
    form = ForgetPasswordForm()
    if form.validate_on_submit():
        # get user from the email
        user = User.query.filter_by(email=form.email.data).first()
        # generate token from the email
        token = generate_token(user.email)
        # neccessary parameters for the send_mail function
        # (check out function.py )
        confirm_url = url_for("users.reset_password",
                              token=token, _external=True)
        template = render_template('message_new_password.html',
                                   confirm_url=confirm_url)
        subject = "Hocam Password Reset"
        # sending the mail
        send_mail(to_email=user.email,
                  subject=subject,
                  template=template,
                  from_email=current_app.config["MAIL_DEFAULT_SENDER"]
                  )
        flash("Password reset email has been sent!", "info")

    return render_template("resetrequest.html", form=form,
                           title="Reset Your Password")


@users.route("/forgetpassword/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        # if the user is logged in
        return redirect(url_for("main.home"))
    if not confirm_token(token):
        # if the token is invalid
        flash("That is an invalid/expired token!", "warning")
        return redirect(url_for("users.forget_password"))
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
        return redirect(url_for("users.login"))

    return render_template("resetpassword.html", form=form,
                           title="Reset Your Password")
