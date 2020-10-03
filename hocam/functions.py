import pytz
from PIL import Image
import secrets
import os
from flask_mail import Message
from hocam import app
from hocam import mail
from itsdangerous import URLSafeTimedSerializer as Serializer
from itsdangerous import SignatureExpired


def localizetime(utctime):
    utctime = utctime.replace(tzinfo=pytz.UTC)
    localtime = utctime.astimezone(pytz.timezone("ASIA/ISTANBUL"))
    localtime = localtime.strftime("%d/%b/%y %X ")
    return localtime


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


def generate_token(email):
    serializer = Serializer(app.config["SECRET_KEY"])
    return serializer.dumps(email,
                            salt=app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600):
    serializer = Serializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except SignatureExpired:
        return False
    return email


def send_mail(recipients, template, subject, sender):
    message = Message(subject,
                      recipients=[recipients],
                      html=template,
                      sender=sender)
    mail.send(message)
