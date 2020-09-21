# from flask import url_for,render_template


class HttpException404(Exception):

    def __str__(self):
        return "This page is not found"
