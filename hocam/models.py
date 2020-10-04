from hocam import db, login_manager
from flask_login import UserMixin
import datetime
import uuid


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class User(db.Model, UserMixin):
    id = db.Column('id', db.Text(length=36), default=lambda: str(uuid.uuid4()),
                   primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False,
                           default="default.png")
    registered_on = db.Column(db.DateTime, nullable=False,
                              default=datetime.datetime.now(
                                  datetime.timezone.utc))
    admin = db.Column(db.Boolean, nullable=False, default=False)
    password = db.Column(db.String(60), nullable=False)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)
    forumpages = db.relationship("ForumPages", backref="creator", lazy=True)
    posts = db.relationship("Posts", backref="author", lazy=True)

    def __repr__(self):
        return f"User ({self.username}, {self.email}, {self.image_file})"


class ForumPages(db.Model):

    __tablename__ = "forumpages"

    id = db.Column('id', db.Text(length=36), default=lambda: str(uuid.uuid4()),
                   primary_key=True)
    topic = db.Column(db.String(35), nullable=False, unique=True)
    date_created = db.Column(db.DateTime, nullable=False,
                             default=datetime.datetime.now(
                                 datetime.timezone.utc))
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    posts = db.relationship("Posts", backref="topic_id", lazy=True)

    def __repr__(self):
        return (f"Forumpage ({self.topic}, {self.creator.username},"
                f"{self.creator.email})")


class Posts(db.Model):

    __tablename__ = "posts"

    id = db.Column('id', db.Text(length=36), default=lambda: str(uuid.uuid4()),
                   primary_key=True)
    date_created = db.Column(db.DateTime, nullable=False,
                             default=datetime.datetime.now(
                                 datetime.timezone.utc))
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    forumpage = db.Column(db.Integer, db.ForeignKey("forumpages.id"),
                          nullable=False)

    def __repr__(self):
        return f"Post ( {self.author.username}, {self.author.email})"
