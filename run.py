from hocam import create_app, db

app = create_app()

with app.app_context():
    from hocam import models
    db.create_all()

if __name__ == "__main__":
    app.run(debug=False)