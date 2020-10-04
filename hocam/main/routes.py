from flask import Blueprint
# Hocam is a basic forumpage restricted to metu/odtü students
# Created by: Buğra Emanet
# My email account: bugra01emanet@gmail.com
from hocam.main.functions import localizetime
from flask import render_template
from hocam.models import ForumPages
from sqlalchemy.exc import OperationalError

main = Blueprint("main", __name__)


@main.route("/")
@main.route("/home")
def home():
    # homepage where people will see the current topics in descending order
    try:
        forumpages = ForumPages.query.order_by(ForumPages.date_created.desc())
        forumpages = forumpages.all()
    except OperationalError:
        # incase there are no topics in the datapage
        forumpages = None
    return render_template("index.html", forumpages=forumpages,
                           localizetime=localizetime)
