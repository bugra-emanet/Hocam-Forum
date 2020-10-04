# Hocam is a basic forumpage restricted to metu/odtü students
# Created by: Buğra Emanet
# My email account: bugra01emanet@gmail.com
from flask import Blueprint
import datetime
from hocam import db
from hocam.forumpages.functions import localizetime
from flask import (render_template, flash, redirect,
                   url_for, request, abort)
from hocam.forumpages.forms import NewForumPageForm, PostForm
from hocam.models import ForumPages, Posts
from flask_login import (login_required, current_user)


forumpages = Blueprint("forumpages", __name__)


@forumpages.route("/forumpage/new", methods=["GET", "POST"])
@login_required
def newforumpage():
    form = NewForumPageForm()
    if form.validate_on_submit():
        # create new forumpage object according
        # to the data from the form add it to the database
        forumpage = ForumPages(topic=form.topic.data,
                               description=form.description.data,
                               date_created=datetime.datetime.now(
                                   datetime.timezone.utc),
                               user_id=current_user.id)
        db.session.add(forumpage)
        db.session.commit()
        flash("Topic Creation Succesfull!", "success")
        return redirect(url_for("forumpages.showforumpage",
                                forumpage_id=forumpage.query.filter_by
                                (topic=form.topic.data).first().id))
    return render_template("newforumpage.html", form=form)


@forumpages.route("/forumpage/<forumpage_id>", methods=["GET", "POST"])
def showforumpage(forumpage_id):
    form = PostForm()
    forumpage = ForumPages.query.get_or_404(forumpage_id)
    if form.validate_on_submit():
        post = Posts(content=form.comment.data, user_id=current_user.id,
                     date_created=datetime.datetime.now(
                         datetime.timezone.utc),
                     forumpage=forumpage_id)
        db.session.add(post)
        db.session.commit()
        flash("Posted", "success")
        return redirect(url_for('forumpages.showforumpage',
                                forumpage_id=forumpage.id))
    # pagination
    page = request.args.get("page", 1, type=int)
    # find the posts that belong to the forumpage
    posts = Posts.query.filter_by(forumpage=forumpage.id)
    # latest post to oldest
    posts = posts.order_by(Posts.date_created.desc())
    # 5 posts per page
    posts = posts.paginate(page=page, per_page=5)
    return render_template("forumpagelayout.html", forumpage=forumpage,
                           form=form, title=forumpage.topic, posts=posts,
                           localizetime=localizetime)


@login_required
@forumpages.route("/forumpage/<forumpage_id>/description/edit",
                  methods=["GET", "POST"])
def editdescription(forumpage_id):
    form = PostForm()
    forumpage = ForumPages.query.get_or_404(forumpage_id,
                                            description="No such page!")
    if forumpage.creator != current_user and not current_user.admin:
        # if the description was not written by
        # the current_user and current_user is not an admin
        abort(403)
    if form.validate_on_submit():
        # change the description and commit the changes
        forumpage.description = form.comment.data
        db.session.commit()
        flash("Your description has been edited!", "success")
        return redirect(url_for("forumpages.showforumpage",
                                forumpage_id=forumpage.id))
    elif request.method == "GET":
        # when the user views the page
        form.comment.data = forumpage.description
    # pagination
    page = request.args.get("page", 1, type=int)
    # get the posts for the current forumpage
    posts = Posts.query.filter_by(forumpage=forumpage.id)
    # posts latest to oldest
    posts = posts.order_by(Posts.date_created.desc())
    # 5 posts per page
    posts = posts.paginate(page=page, per_page=5)
    return render_template("editforumpagelayout_description.html",
                           forumpage=forumpage,
                           form=form, title=forumpage.topic, posts=posts,
                           localizetime=localizetime)


@login_required
@forumpages.route("/forumpage/<forumpage_id>/delete",
                  methods=["POST"])
def delete_description(forumpage_id):
    forumpage = ForumPages.query.get_or_404(forumpage_id)
    if forumpage.creator != current_user and not current_user.admin:
        # if the forumpage was not created
        # by current_user and current_user is not an admin
        abort(403)
    # delete the description
    forumpage.description = None
    db.session.commit()
    flash("Your description has been deleted!", "success")
    return redirect(url_for("forumpages.showforumpage",
                            forumpage_id=forumpage.id))
