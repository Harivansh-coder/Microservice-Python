from app import create_flask_app
from app import db
from app.models import *

app = create_flask_app()


# Initialize the database
with app.app_context():
    # Create the database tables if they don't exist
    db.create_all()


if __name__ == '__main__':

    # Run the Flask app

    app.run(host='0.0.0.0', port=5000)
