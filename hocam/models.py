from hocam import db, login_manager
from flask_login import UserMixin
import datetime
from hocam.errors import HttpException404

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default="default.png")
    password = db.Column(db.String(60), nullable=False)
    forumpages = db.relationship("ForumPages", backref="author", lazy=True)
    def __repr__(self):
        return f"User ('{self.username}','{self.email} {self.image_file}')"


class ForumPages(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(35), nullable=False, unique=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow())
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    @classmethod
    def get_or_404(cls, id):
        forumpage = cls.query.get(id)
        if not forumpage:
            raise HttpException404
        return forumpage

