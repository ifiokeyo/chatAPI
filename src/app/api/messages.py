import logging
from flask_restful import Resource
from flask import request, jsonify, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.app.models import models
from src.app.utils.utils import (
    validate_request, paginate_query, validate_convo_participants, DEFAULT_PAGE
)

User = models.User
Conversation = models.Conversation
Message = models.Message


class MessageResource(Resource):

    @jwt_required
    @validate_request('content')
    def post(self, conversation_id):
        payload = request.get_json()
        current_user = get_jwt_identity()
        conversation = Conversation.query.get_or_404(conversation_id)

        content = payload['content']
        current_user_id = current_user['id']

        is_member = validate_convo_participants(conversation=conversation, participant_id=current_user_id)

        if not is_member:
            return {
                       "status": "fail",
                       "message": "Access denied"
                   }, 403

        try:
            new_message = Message(
                content=content,
                owner=current_user_id,
                conversation_id=conversation_id
            )
            new_message.save()

            response = jsonify(dict(
                status="success",
                data={
                    "message": "Conversation created successfully",
                    "content": new_message.serialize()
                }
            ))
            response.status_code = 201
            return response
        except Exception as error:
            logging.error(error)
            return {
                       "status": "fail",
                       "message": "Server error"
                   }, 500

    @jwt_required
    def get(self, conversation_id):
        current_user = get_jwt_identity()
        current_user_id = current_user['id']
        conversation = Conversation.query.get_or_404(
            conversation_id,
            description=f'No message was found with id {conversation_id}'
        )

        is_member = validate_convo_participants(conversation=conversation, participant_id=current_user_id)

        if not is_member:
            return {
                       "status": "fail",
                       "message": "Access denied"
                   }, 403

        page = request.args.get('page', DEFAULT_PAGE, type=int)

        msg_query = Message.query.filter_by(conversation_id=conversation.id)

        try:
            pagination_object = paginate_query(msg_query, page)
            response = jsonify(dict(
                status="success",
                data={
                    'has_next': pagination_object.has_next,
                    'has_prev': pagination_object.has_prev,
                    'page': pagination_object.page,
                    'next': url_for(
                        'get_conversation_messages_paginated',
                        conversation_id=conversation_id,
                        page=pagination_object.next_num
                    ) if pagination_object.has_next else None,
                    'previous': url_for(
                        'get_conversation_messages_paginated',
                        conversation_id=conversation_id,
                        page=pagination_object.prev_num
                    ) if pagination_object.has_prev else None,
                    'pages': pagination_object.pages,
                    'per_page': pagination_object.per_page,
                    'total': pagination_object.total,
                    'messages': [
                        message.serialize() for message in pagination_object.items if
                        pagination_object.items is not None
                    ]
                }
            ))
            response.status_code = 200
            return response
        except Exception as error:
            logging.error(error)
            return {
                       "status": "fail",
                       "message": "Server error"
                   }, 500


class MessagePollResource(Resource):
    @jwt_required
    def get(self, conversation_id, last_msg_id):
        current_user = get_jwt_identity()
        current_user_id = current_user['id']
        conversation = Conversation.query.get_or_404(
            conversation_id,
            description=f'No message was found with id {conversation_id}'
        )

        is_member = validate_convo_participants(conversation=conversation, participant_id=current_user_id)

        if not is_member:
            return {
                       "status": "fail",
                       "message": "Access denied"
                   }, 403

        try:
            msg = Message.query.get_or_404(last_msg_id,  description=f'No message was found with id {last_msg_id}')
            messages = Message.query.filter(Message.conversation_id == conversation_id,
                                            Message.created_at > msg.created_at).all()
            response = jsonify(dict(
                status="success",
                data={
                    'messages': [message.serialize() for message in messages]
                }
            ))
            response.status_code = 200
            return response
        except Exception as error:
            logging.error(error)
            return {
                       "status": "fail",
                       "message": "Server error"
                   }, 500
