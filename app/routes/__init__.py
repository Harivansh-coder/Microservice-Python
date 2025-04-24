from app.routes.auth import auth_router
from flask import Blueprint

routes = Blueprint("routes", __name__)


@routes.route("/ping", methods=["GET"])
def ping():
    return {
        "status": "success",
        "message": "pong"
    }


# auth route is registered
routes.register_blueprint(auth_router, url_prefix="/auth")
