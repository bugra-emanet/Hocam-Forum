import os


class Config:
    SECRET_KEY = os.environ.get("HOCAM_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ\
        .get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = "smtp.googlemail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("GMAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT")
    MAIL_DEFAULT_SENDER = os.environ.get("GMAIL_USERNAME")
