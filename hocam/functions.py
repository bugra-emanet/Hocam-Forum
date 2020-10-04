# functions module includes
# functions that are used in this project
import pytz
from PIL import Image
import secrets
import os
from flask_mail import Message
from hocam import app, mail, db
from hocam.models import User
from itsdangerous import URLSafeTimedSerializer as Serializer
from itsdangerous import SignatureExpired, BadSignature


def localizetime(utctime):
    # function for turning utc to localtime (for display reasons)
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
    except SignatureExpired or BadSignature:
        return False
    return email


def send_mail(recipients, template, subject, sender):
    message = Message(subject,
                      recipients=[recipients],
                      html=template,
                      sender=sender)
    mail.send(message)


def create_admin_user(email):
    # create admin user from existing user
    user = User.query.filter_by(email=email).first_or_404()
    user.admin = True
    db.session.commit()
    return repr(user)
