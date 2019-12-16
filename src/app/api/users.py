import logging
from flask_restful import Resource
from flask import request, jsonify, url_for
from flask_jwt_extended import jwt_required

from src.app.models import models
from src.app.utils.utils import paginate_query, DEFAULT_PAGE


User = models.User


class UserResource(Resource):

    @jwt_required
    def get(self):
        page = request.args.get('page', DEFAULT_PAGE, type=int)

        try:
            user_query = User.query
            pagination_object = paginate_query(user_query, page)
            response = jsonify(dict(
                status="success",
                data={
                    'has_next': pagination_object.has_next,
                    'has_prev': pagination_object.has_prev,
                    'page': pagination_object.page,
                    'next': url_for(
                        'get_all_users',
                        page=pagination_object.next_num
                    ) if pagination_object.has_next else None,
                    'previous': url_for(
                        'get_all_users',
                        page=pagination_object.prev_num
                    ) if pagination_object.has_prev else None,
                    'pages': pagination_object.pages,
                    'per_page': pagination_object.per_page,
                    'total': pagination_object.total,
                    'users': [
                        user.serialize() for user in pagination_object.items if
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


class SingleUserResource(Resource):
    @jwt_required
    def get(self, user_id):

        try:
            user = User.query.get(user_id)
            serialized_user = user.serialize()

            response = jsonify(dict(
                status="success",
                user=serialized_user
            ))
            response.status_code = 200
            return response
        except Exception as error:
            logging.error(error)
            return {
                       "status": "fail",
                       "message": "Server error"
                   }, 500
