import os


class Config:
    SECRET_KEY = os.environ.get("HOCAM_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ\
        .get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")
