from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import (StringField, PasswordField,
                     SubmitField, BooleanField, ValidationError)
from wtforms.validators import (DataRequired, Length,
                                EqualTo, Regexp)
from hocam.models import User
from wtforms_alchemy import Unique, ModelForm
import re


metumail_validator = re.compile(r"[a-z]+[.][a-z]+@metu.edu.tr")


class RegistirationForm(FlaskForm, ModelForm):
    username = StringField("Username",
                           validators=[DataRequired(),
                                       Length(min=5, max=15),
                                       Unique(User.username)
                                       ])
    email = StringField("Metu mail",
                        validators=[DataRequired(),
                                    Regexp(metumail_validator,
                                    message="Please enter a valid Metu Mail."),
                                    Unique(User.email)])
    password = PasswordField("Password",
                             validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password",
                                     validators=[DataRequired(),
                                                 EqualTo("password")])
    submit = SubmitField("Sign up")


class LoginForm(FlaskForm, ModelForm):
    email = StringField("Email",
                        validators=[DataRequired(), Regexp(metumail_validator,
                                    message="Please enter a valid Metu Mail.")]
                        )
    password = PasswordField("Password",
                             validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class UpdateForm(FlaskForm):
    username = StringField("Username",
                           validators=[DataRequired(),
                                       Length(min=5, max=15)])
    image = FileField("Update Profile Picture",
                      validators=[FileAllowed(["png", "jpg"])])
    submit = SubmitField("Update")

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError("This username is taken!")


class ResendConfirmationForm(FlaskForm):
    email = StringField("Email",
                        validators=[DataRequired(), Regexp(metumail_validator,
                                    message="Please enter a valid Metu Mail.")]
                        )
    submit = SubmitField("Resend")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError("There is no account with that email "
                                  "you must register first!")


class ForgetPasswordForm(FlaskForm):
    email = StringField("Email",
                        validators=[DataRequired(), Regexp(metumail_validator,
                                    message="Please enter a valid Metu Mail.")]
                        )
    submit = SubmitField("Renew Password")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError("There is no account with that "
                                  "email you must register first!")


class RenewPasswordForm(FlaskForm):
    password = PasswordField("Password",
                             validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password",
                                     validators=[DataRequired(),
                                                 EqualTo("password")])
    submit = SubmitField("Renew Password")
