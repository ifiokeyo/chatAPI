import os
import logging
from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager


db = SQLAlchemy()
migrate = Migrate()

try:
    from ..config import app_configuration
    from .api.auth import SignupResource, LoginResource, LogoutResource
    from .api.conversation import (
        PersonalConversationResource, GroupConversationResource,
        ConversationResource, UserConversationResource
    )
    from .api.users import UserResource, SingleUserResource
    from .api.messages import MessageResource, MessagePollResource

except (ModuleNotFoundError, ImportError):
    from src.config import app_configuration
    from src.app.api.auth import SignupResource, LoginResource, LogoutResource
    from src.app.api.conversation import (
        PersonalConversationResource, GroupConversationResource,
        ConversationResource, UserConversationResource
    )
    from src.app.api.users import UserResource, SingleUserResource
    from src.app.api.messages import MessageResource, MessagePollResource


def create_flask_app(environment=os.environ.get('FLASK_ENV')):
    # initialize logging module
    log_format = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    logging.basicConfig(format=log_format, level=logging.INFO)

    # initialize Flask
    app = Flask(__name__, instance_relative_config=True, static_folder=None)

    # to allow cross origin resource sharing
    CORS(app)
    app.config.from_object(app_configuration[environment])
    app.config.from_pyfile('config.py')
    app.url_map.strict_slashes = False
    jwt = JWTManager(app)

    # initialize SQLAlchemy
    try:
        from .models import models
    except ModuleNotFoundError:
        from src.app.models import models

    db.init_app(app)
    migrate.init_app(app, db)

    app.url_map.strict_slashes = False

    # tests route
    @app.route('/')
    def index():
        return "Welcome to Bunq Chat API"

    # Create a function that will be called whenever create_access_token
    # is used. It will take whatever object is passed into the
    # create_access_token method, and lets us define what custom claims
    # should be added to the access token.
    @jwt.user_claims_loader
    def add_claims_to_access_token(user):
        return {'email': user['email']}

    @jwt.token_in_blacklist_loader
    def check_if_token_in_blacklist(decrypted_token):
        jti = decrypted_token['jti']
        return models.RevokedAccessToken.is_token_blacklisted(jti)

    # create endpoints
    api = Api(app, prefix='/api/v1')

    api.add_resource(
        LoginResource,
        '/auth/login',
        endpoint='login')

    api.add_resource(
        SignupResource,
        '/auth/signup',
        endpoint='signup')

    api.add_resource(
        LogoutResource,
        '/logout',
        endpoint='logout')

    api.add_resource(
        PersonalConversationResource,
        '/conversation/personal',
        endpoint='create_personal_conversation'
    )

    api.add_resource(
        GroupConversationResource,
        '/conversation/group',
        endpoint='create_group_conversation'
    )

    api.add_resource(
        UserResource,
        '/users',
        endpoint='get_all_users'
    )

    api.add_resource(
        SingleUserResource,
        '/users/<int:user_id>',
        endpoint='get_user_detail'
    )

    api.add_resource(
        MessageResource,
        '/conversation/<int:conversation_id>/message/send',
        endpoint='create_conversation_message'
    )

    api.add_resource(
        MessageResource,
        '/conversation/<int:conversation_id>/message',
        endpoint='get_conversation_messages_paginated'
    )

    api.add_resource(
        MessagePollResource,
        '/conversation/<int:conversation_id>/poll/<int:last_msg_id>',
        endpoint='poll_conversation_messages'
    )

    api.add_resource(
        ConversationResource,
        '/conversation/<int:conversation_id>',
        endpoint='get_conversation_detail'
    )

    api.add_resource(
        UserConversationResource,
        '/conversation/user/<int:user_id>',
        endpoint='get_all_user_conversations'
    )

    # handle default 500 exceptions with a custom response
    @app.errorhandler(500)
    def internal_server_error(error):
        response = jsonify(dict(status=500, error='Internal server error',
                                message="""It is not you. It is me. The server encountered an 
                                internal error and was unable to complete your request.  
                                Either the server is overloaded or there is an error in the
                                application"""))
        response.status_code = 500
        return response

    return app
