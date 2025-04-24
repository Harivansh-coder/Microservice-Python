from app import marsh
from marshmallow_sqlalchemy import auto_field
from marshmallow import validate
from app.models import User


class UserSchema(marsh.SQLAlchemySchema):
    class Meta:
        model = User
        load_instance = True  # This will create an instance of the model when deserializing data

    id = auto_field()
    name = auto_field(required=True)
    email = auto_field(required=True, validate=validate.Email())
    password = auto_field(
        required=True, validate=validate.Length(min=8, max=128))
    # This field is read-only and will not be included when creating or updating a user
    created_at = auto_field(dump_only=True)


class UserLoginSchema(marsh.SQLAlchemySchema):
    class Meta:
        model = User
        load_instance = True  # This will create an instance of the model when deserializing data

    email = auto_field(required=True, validate=validate.Email())

    password = auto_field(
        required=True, validate=validate.Length(min=8, max=128))


class UserResponseSchema(marsh.SQLAlchemySchema):
    class Meta:
        model = User
        load_instance = True  # This will create an instance of the model when deserializing data

    id = auto_field()
    name = auto_field(required=True)
    email = auto_field(required=True)
    # This field is read-only and will not be included when creating or updating a user
    created_at = auto_field(dump_only=True)


user_schema = UserSchema()
user_login_schema = UserLoginSchema()
user_response_schema = UserResponseSchema()
user_list_schema = UserSchema(many=True)
