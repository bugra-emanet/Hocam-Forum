# functions module includes
# functions that are used in this project
from PIL import Image
import secrets
import os
import sendgrid
from sendgrid.helpers.mail import Mail, Content, Email
from itsdangerous import URLSafeTimedSerializer as Serializer
from itsdangerous import SignatureExpired, BadSignature
from flask import current_app, render_template


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, "static/profile_pics",
                                picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn


def generate_token(email):
    serializer = Serializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email,
                            salt=current_app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600):
    serializer = Serializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=current_app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except SignatureExpired or BadSignature:
        return False
    return email


def send_mail(from_email, to_email, template, subject):

    sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
    to_email = Email(to_email)
    content = Content("html", render_template(template))
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    return response.status_code
