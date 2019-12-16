import logging
from flask_restful import Resource
from flask import request, jsonify, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from typing import List

from src.app.models import models
from src.app.utils.utils import (
    validate_request, validate_conversation, validate_convo_participants,
    get_last_seen, paginate_query, DEFAULT_PAGE
)


User = models.User
Conversation = models.Conversation


class PersonalConversationResource(Resource):

    def _check_conversation(self, *, owner_id: int, participant_id: int):
        conversation = Conversation.query.filter_by(owner=owner_id, type='Personal',
                                                    personal_convo_participant=participant_id).first()
        if conversation is None:
            conversation = Conversation.query.filter_by(owner=participant_id, type='Personal',
                                                        personal_convo_participant=owner_id).first()

        return conversation

    @jwt_required
    @validate_request('participants')
    @validate_conversation
    def post(self):
        convo_payload = request.payload

        current_user = convo_payload['current_user']
        owner_id = convo_payload['owner_id']
        convo_type = convo_payload['convo_type']
        participants = convo_payload['participants']

        try:
            existing_conversation = self._check_conversation(owner_id=owner_id, participant_id=participants[0].id)

            if existing_conversation is not None:
                response = jsonify(dict(
                    status="success",
                    data={
                        "message": "Conversation already exist",
                        "Conversation": {
                            'id': existing_conversation.id,
                            'name': existing_conversation.name,
                            "owner": existing_conversation.owner,
                            'participants': [
                                {
                                    'id': owner_id,
                                    'username': current_user['username'],
                                    'name': current_user['name']
                                },
                                {
                                    'id': participants[0].id,
                                    'username': participants[0].username,
                                    'name': participants[0].name
                                }
                            ]
                        }
                    }
                ))
                response.status_code = 200
                return response

            new_conversation = Conversation(
                name=participants[0].username,
                owner=owner_id,
                type=convo_type,
                personal_convo_participant=participants[0].id
            )

            new_conversation.save()

            response = jsonify(dict(
                status="success",
                data={
                    "message": "Conversation created successfully",
                    "Conversation": {
                        'id': new_conversation.id,
                        'name': new_conversation.name,
                        "owner": new_conversation.owner,
                        'participants': [
                            {
                                'id': owner_id,
                                'username': current_user['username'],
                                'name': current_user['name']
                            },
                            {
                                'id': participants[0].id,
                                'username': participants[0].username,
                                'name': participants[0].name
                            }
                        ]
                    }
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


class GroupConversationResource(Resource):

    def _add_participants(self, model, *, participants: List):
        for participant in participants:
            model.group_convo_members.append(participant)
        return model

    @jwt_required
    @validate_request('group_name', 'participants')
    @validate_conversation
    def post(self):
        convo_payload = request.payload

        owner_id = convo_payload['owner_id']
        convo_type = convo_payload['convo_type']
        participants = convo_payload['participants']
        group_name = convo_payload['group_name']
        current_user = User.query.get(owner_id)

        try:
            new_conversation = Conversation(
                name=group_name,
                owner=owner_id,
                type=convo_type,
            )
            new_conversation.group_convo_members.append(current_user)
            updated_conversation = self._add_participants(new_conversation, participants=participants)
            updated_conversation.save()

            response = jsonify(dict(
                status="success",
                data={
                    "message": "Conversation created successfully",
                    "Conversation": {
                        'id': new_conversation.id,
                        'name': new_conversation.name,
                        "owner": new_conversation.owner,
                        'participants': [member.serialize() for member in new_conversation.group_convo_members]
                    }
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


class ConversationResource(Resource):

    def _serialize_g_participants(self, conversation):
        return [
            {
                'id': participant.id,
                'username': participant.username,
                'name': participant.name,
                'last_seen': get_last_seen(conversation.id, participant.id)
            }
            for participant in conversation.group_convo_members
        ]

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

        try:
            if conversation.type == 'Personal':
                participant = User.query.get(conversation.personal_convo_participant)
                owner = User.query.get(conversation.owner)
                last_seen_participant = get_last_seen(conversation_id, participant.id)
                last_seen_owner = get_last_seen(conversation_id, owner.id)
                participants = [
                    {
                        'id': participant.id,
                        'username': participant.username,
                        'name': participant.name,
                        'last_seen': last_seen_participant
                    },
                    {
                        'id': owner.id,
                        'username': owner.username,
                        'name': owner.name,
                        'last_seen': last_seen_owner
                    }
                ]

            if conversation.type == 'Group':
                participants = self._serialize_g_participants(conversation)

            response = jsonify(dict(
                status='success',
                data={
                    'Conversation': {
                        'id': conversation.id,
                        'name': conversation.name,
                        'owner': conversation.owner,
                        'participants': participants
                    }
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


class UserConversationResource(Resource):
    @jwt_required
    def get(self, user_id):
        current_user = get_jwt_identity()

        if int(current_user['id']) != int(user_id):
            return {
                       "status": "fail",
                       "message": "Access denied"
                   }, 401

        page = request.args.get('page', DEFAULT_PAGE, type=int)

        try:
            user = User.query.get(user_id)
            convo_query = Conversation.query.filter(
                (Conversation.owner == user.id) |
                (Conversation.personal_convo_participant == user.id) |
                (Conversation.group_convo_members.contains(user))
            )
            pagination_object = paginate_query(convo_query, page)

            response = jsonify(dict(
                status="success",
                data={
                    'has_next': pagination_object.has_next,
                    'has_prev': pagination_object.has_prev,
                    'page': pagination_object.page,
                    'next': url_for(
                        'get_all_user_conversations',
                        user_id=user_id,
                        page=pagination_object.next_num
                    ) if pagination_object.has_next else None,
                    'previous': url_for(
                        'get_all_user_conversations',
                        user_id=user_id,
                        page=pagination_object.prev_num
                    ) if pagination_object.has_prev else None,
                    'pages': pagination_object.pages,
                    'per_page': pagination_object.per_page,
                    'total': pagination_object.total,
                    'conversations': [
                        {
                            'id': conversation.id,
                            'name': conversation.name,
                            'type': conversation.type,
                            'owner': conversation.owner,
                            'personal_convo_participant': conversation.personal_convo_participant,
                            'last_seen': get_last_seen(conversation.id, user_id)

                        }
                        for conversation in pagination_object.items if
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
