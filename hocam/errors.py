from flask import url_for,render_template

class HttpException404(Exception):
    
    def __str__(self):
        return f"This page is not found"
