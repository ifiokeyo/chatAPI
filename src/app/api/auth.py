from flask_restful import Resource
from flask import request, jsonify

from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_raw_jwt
)

from src.app.models import models
from src.app.utils.utils import (
    verify_signup_input, pw_encrypt,
    validate_request, verify_pw
)


User = models.User
RevokedAccessToken = models.RevokedAccessToken


class SignupResource(Resource):
    @verify_signup_input
    @validate_request('password')
    def post(self):
        signup_details = request.get_json()
        _user = User.query.filter_by(email=signup_details['email']).first()

        if _user:
            return {
                "status": "fail",
                "data": {
                    "message": "A user exists with the email provided!"
                }
            }, 403

        new_user = User(
            name=signup_details['name'],
            email=signup_details['email'],
            username=signup_details['username'],
            password=pw_encrypt(signup_details['password'])
        )
        new_user.save()

        user = new_user.serialize()
        access_token = create_access_token(identity=user)
        refresh_token = create_refresh_token(identity=user)

        response = jsonify(dict(
                        status="success",
                        data={
                            "user": user,
                            "message": "User was successfully created",
                            "access_token": access_token,
                            "refresh_token": refresh_token
                        }
                    ))
        response.status_code = 201
        return response


class LoginResource(Resource):
    @validate_request('email', 'password')
    def post(self):
        payload = request.get_json()
        user = User.query.filter_by(email=payload['email']).first()
        if not user:
            return {
                "status": "fail",
                "message": "User does not exist"
            }, 401

        check_pw = verify_pw(payload['password'], user.password)

        if not check_pw:
            return {
                "status": "fail",
                "message": "Wrong Password"
            }, 401

        _user = user.serialize()
        access_token = create_access_token(identity=_user)
        refresh_token = create_refresh_token(identity=_user)

        response = jsonify(dict(
                        status="success",
                        data={
                            "user": _user,
                            "message": "User login successful",
                            "access_token": access_token,
                            "refresh_token": refresh_token
                        }
                    ))
        response.status_code = 200
        return response


class LogoutResource(Resource):
    @jwt_required
    def post(self):
        jti = get_raw_jwt()['jti']
        revoked_token = RevokedAccessToken(jti=jti)
        revoked_token.save()
        return {
            "status": "success",
            "message": "You have been successfully logged out!"
        }, 200
