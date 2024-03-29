from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager
import os
import secrets
from db import db
import models
from blocklist import BLOCKLIST
from flask_migrate import Migrate
from dotenv import load_dotenv

from resources.item import blp as ItemBlueprint
from resources.store import blp as StoreBlueprint
from resources.tags import blp as TagsBlueprint
from resources.user import blp as UserBlueprint


def create_app(db_url=None):

    app = Flask(__name__)
    load_dotenv()

    app.config["PROPAGATE_EXCEPTION"] = True
    app.config["API_TITLE"] = "Stores REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    migrate = Migrate(app,db)

    api = Api(app)

    # app.config["JWT_SECRET_KEY"] = secrets.SystemRandom().getrandbits(128)
    app.config["JWT_SECRET_KEY"] = "199147354889184238543979285757619692115"
    jwt = JWTManager(app)


    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BLOCKLIST

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            jsonify({"message": "User has logged out. Token has revoked.", "error": "token_revoked"}), 
            401,
        )

    @jwt.needs_fresh_token_loader
    def token_unfresh_callback(jwt_header, jwt_payload):
        return (
            jsonify({"message": "Non fresh token.", "error": "token_unfresh"}), 
            401,
        )

    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        if identity == 2:
            return {
                "is_admin": True
            }
        return {
            "is_admin": False
        }

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify({"message": "Token has expired.", "error": "token_expired"}), 
            401,
        )
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {"message": "Sign Verify Failed", "error": "invalid token"}
            ), 
            401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    "description": "Missing Token", 
                    "error": "authorizationz_required"
                }
            ), 
            401,
        )

    # @app.before_first_request
    # def create_tables():
    #     db.create_all()

    # with app.app_context():
    #     db.create_all()

    api.register_blueprint(StoreBlueprint)
    api.register_blueprint(ItemBlueprint)
    api.register_blueprint(TagsBlueprint)
    api.register_blueprint(UserBlueprint)

    return app


# http://127.0.0.1:5000/store - to be accessed this way
