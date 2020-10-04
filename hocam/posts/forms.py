from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class PostForm(FlaskForm):
    comment = TextAreaField("Comment", validators=[DataRequired(),
                                                   Length(min=1, max=300)])
    post = SubmitField("Post")
