# Hocam is a basic forumpage restricted to metu/odtü students
# Created by: Buğra Emanet
# My email account: bugra01emanet@gmail.com
from flask import Blueprint
from hocam import db
from hocam.posts.functions import localizetime
from flask import (render_template, flash, redirect,
                   url_for, request, abort)
from hocam.posts.forms import PostForm
from hocam.models import ForumPages, Posts
from flask_login import login_required, current_user


posts = Blueprint("posts", __name__)


@login_required
@posts.route("/forumpage/<forumpage_id>/post/<post_id>/edit",
             methods=["GET", "POST"])
def editpost(forumpage_id, post_id):
    form = PostForm()
    post = Posts.query.get_or_404(post_id)
    forumpage = ForumPages.query.get_or_404(forumpage_id)
    if forumpage_id != post.forumpage:
        # if the forumpage id doesnt match the forumpage of the post
        abort(404)
    if post.author != current_user and not current_user.admin:
        # if the post was not written by
        # the current_user and the current_user is not an admin
        abort(403)
    if form.validate_on_submit():
        post.content = form.comment.data
        db.session.commit()
        flash("Your post has been edited!", "success")
        return redirect(url_for("forumpages.showforumpage",
                                forumpage_id=forumpage.id))
    elif request.method == "GET":
        # when the user wants to see the editpage
        form.comment.data = post.content
    # pagination
    page = request.args.get("page", 1, type=int)
    # get the posts for the current forumpage
    posts = Posts.query.filter_by(forumpage=forumpage.id)
    # posts latest to oldest
    posts = posts.order_by(Posts.date_created.desc())
    # 5 posts per page
    posts = posts.paginate(page=page, per_page=5)
    return render_template("editforumpagelayout.html", forumpage=forumpage,
                           form=form, title=forumpage.topic, posts=posts,
                           localizetime=localizetime)


@login_required
@posts.route("/forumpage/<forumpage_id>/post/<post_id>/delete",
             methods=["POST"])
def delete_post(forumpage_id, post_id):
    post = Posts.query.get_or_404(post_id)
    if forumpage_id != post.forumpage:
        # if the forumpage id doesnt match the forumpage of the post
        abort(404)
    if post.author != current_user and not current_user.admin:
        # if the post was not written by
        # the current_user or the current_user is not an admin
        abort(403)
    forumpage = post.forumpage
    db.session.delete(post)
    db.session.commit()
    flash("Your post has been deleted!", "success")
    return redirect(url_for("forumpages.showforumpage",
                            forumpage_id=forumpage))
