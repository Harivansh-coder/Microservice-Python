from app import db
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

    @staticmethod
    def set_password(password):
        return generate_password_hash(password)

    @classmethod
    def create_user(cls, name, email, password):
        try:
            hashed_password = cls.set_password(password)
            new_user = cls(name=name, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return new_user
        except Exception as e:
            print(f"Error creating user: {e}")
            db.session.rollback()
            return None

    @classmethod
    def get_user_by_email(cls, email):
        try:

            return cls.query.filter_by(email=email).first()
        except Exception as e:
            print(f"Error fetching user by email: {e}")
            return None

    @staticmethod
    def verify_password(stored_password, provided_password):
        return check_password_hash(stored_password, provided_password)

    def __repr__(self):
        return f"<User {self.name}>, {self.email}>"
