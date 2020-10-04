from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length
from hocam.models import ForumPages
from wtforms_alchemy import Unique, ModelForm


class NewForumPageForm(FlaskForm, ModelForm):
    topic = StringField("Topic", validators=[DataRequired(),
                                             Length(min=5, max=35),
                                             Unique(ForumPages.topic)])
    description = TextAreaField("Description")
    submit = SubmitField("Create")


class PostForm(FlaskForm):
    comment = TextAreaField("Comment", validators=[DataRequired(),
                                                   Length(min=1, max=300)])
    post = SubmitField("Post")
