from flask import Blueprint, request, jsonify
from app.models import User
from app import db
from marshmallow import ValidationError
from app.utils.token import encode_token, decode_token
from app.schema import user_schema, user_login_schema, user_response_schema

auth_router = Blueprint("auth_router", __name__)


@auth_router.route("/login", methods=['POST'])
def login_route():

    try:
        request_payload = request.get_json()

        try:
            payload_user = user_login_schema.load(
                request_payload, session=db.session)
        except ValidationError as e:
            return jsonify({"status": "error", "message": e.messages}), 400

        # check if user exists
        user = User.get_user_by_email(payload_user.email)
        if not user or not User.verify_password(user.password, payload_user.password):
            return jsonify({'msg': 'Invalid email or password'}), 401

        # Generate JWT
        access_token = encode_token({"sub": user.id})

        if not access_token:
            return jsonify({'msg': 'Failed to generate token'}), 500

        # Return the token in the response

        return {
            "status": "success",
            "access_token": access_token,
        }

    except Exception as e:
        return jsonify({"status": "error", "message": "something went wrong"}), 500


@auth_router.route("/signup", methods=['POST'])
def sigup_route():
    try:
        request_payload = request.get_json()

        try:
            payload_user = user_schema.load(
                request_payload, session=db.session)
        except ValidationError as e:
            return jsonify({"status": "error", "message": e.messages}), 400

        # check if user exists
        user = User.get_user_by_email(payload_user.email)

        if user:
            return jsonify({'msg': 'User already exists'}), 409

        # Create a new user
        new_user = User.create_user(
            name=payload_user.name,
            email=payload_user.email,
            password=payload_user.password
        )

        # Return the created user in the response
        return user_response_schema.dump(new_user), 201

    except Exception as e:
        return jsonify({"status": "error", "message": e.messages}), 500


@auth_router.route("/validate", methods=['POST'])
def validate_route():
    try:
        request_header = request.headers.get("Authorization")
        if not request_header:
            return jsonify({"status": "error", "message": "Authorization header is missing"}), 401

        token = request_header.split(" ")[1]

        try:
            decoded_token = decode_token(token)
        except Exception as e:
            return jsonify({"status": "error", "message": "Invalid token"}), 401

        user_id = decoded_token.get("sub")
        if not user_id:
            return jsonify({"status": "error", "message": "Invalid token"}), 401

        user = User.get_user_by_id(user_id)
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        return user_response_schema.dump(user), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "something went wrong"}), 500
