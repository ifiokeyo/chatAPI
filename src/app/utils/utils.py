import logging
from passlib.hash import sha256_crypt
from flask_restful import reqparse
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import (
    verify_jwt_in_request, get_jwt_claims,
    get_jwt_identity
)

from src.app.models import models
from src.app import db


User = models.User
Message = models.Message
Conversation = models.Conversation
group_convo_members = models.group_convo_members

ITEMS_PER_PAGE = 20
DEFAULT_PAGE = 1


def get_last_seen(conversation_id, participant_id):
    last_user_msg = Message.query.filter(
        Message.conversation_id == conversation_id,
        Message.owner == participant_id
    ).order_by(Message.created_at.desc()).first()

    return last_user_msg.created_at if last_user_msg is not None else None


def paginate_query(query, page=DEFAULT_PAGE, per_page=ITEMS_PER_PAGE):
    return query.paginate(page, per_page, False)


def validate_convo_participants(*, conversation, participant_id):
    convo_type = conversation.type

    if convo_type == 'Personal' and (conversation.owner != participant_id or
                                     conversation.personal_convo_participant != participant_id):
        return False

    group_user = db.session.query(group_convo_members).filter_by(
        conversation_id=conversation.id, participant_id=participant_id
    ).first()

    if convo_type == 'Group' and group_user is None:
        return False

    return True


def validate_participants(users):
    validated_users = []
    validated_users_append = validated_users.append

    for user in users:
        valid_user = User.query.get(user['id'])

        if valid_user is None:
            logging.error(f'User with id {user["id"]} not found')
            return []
        validated_users_append(valid_user)
    return validated_users


def validate_conversation(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        request_payload = request.get_json()
        current_user = get_jwt_identity()
        validated_users = validate_participants(request_payload['participants'])
        convo_type = None
        group_name = None

        request_path = request.path

        if request_path.find('personal') != -1:
            convo_type = 'Personal'

        if request_path.find('group') != -1:
            convo_type = 'Group'
            group_name = request_payload['group_name']

        if not validated_users:
            return {
                "status": "fail",
                "message": "Conversation can only occur with at least one valid user"
            }

        if request_path.find('personal') != -1 and len(validated_users) > 1:
            return {
                "status": "fail",
                "message": "Personal conversation can only occur with one valid user"
            }

        request.payload = {
            "current_user": current_user,
            'owner_id': current_user['id'],
            'convo_type': convo_type,
            'group_name': group_name,
            'participants': validated_users
        }

        return fn(*args, **kwargs)
    return decorated


def pw_encrypt(pw):
    return sha256_crypt.hash(pw)


def verify_pw(pw_str, pw_hash):
    return sha256_crypt.verify(pw_str, pw_hash)


def verify_signup_input(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument('name', type=str, required=True, help="Name cannot be blank!")
        parser.add_argument('username', type=str, required=True, help="Username cannot be blank!")
        parser.add_argument('email', type=str, required=True, help="Email cannot be blank!")
        parser.add_argument('password', type=str, required=True, help="Password cannot be blank!")
        parser.parse_args()

        return f(*args, **kwargs)
    return decorated


def validate_request(*expected_args):
    def validate_input(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not request.json:
                return {
                    'status': 'fail',
                    "data": {"message": "Request must be a valid JSON"}
                }, 400

            payload = request.get_json()
            if payload:
                for value in expected_args:
                    if value not in payload or not payload[value]:
                        return {
                            "status": "fail",
                            "data": {"message": value + " is required"}
                        }, 400

                    if value in ['participants'] and (type(payload[value]) != list or len(payload[value]) < 1):
                        return {
                            "status": "fail",
                            "message": "Participants not provided"
                        }, 400

                    if value == 'password' and len(payload[value]) < 8:
                        return {
                            "status": "fail",
                            "message": f'{value.capitalize} must be a minimum of 8 characters'
                        }, 400
                    if value in ['group_name', 'content'] and type(payload[value]) != str:
                        return {
                            "status": "fail",
                            "message": f'{value} must be a string'
                        }, 400
            return f(*args, **kwargs)
        return decorated
    return validate_input
