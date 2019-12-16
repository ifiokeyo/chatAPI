import sqlalchemy as sa
from sqlalchemy.orm import validates
from datetime import datetime
from src.app import db


class ModelOpsMixin(object):
    """
    Contains the serialize method to convert objects to a dictionary
    """

    def serialize(self):
        return {column.name: getattr(self, column.name)
                for column in self.__table__.columns if column.name not in ['password', 'updated_at']}

    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()


group_convo_members = db.Table('group_convo_members',
                               db.Column('conversation_id', db.Integer, db.ForeignKey('conversation.id'),
                                         primary_key=True),
                               db.Column('participant_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
                               )

CONVERSATION_TYPE_ENUM = ('Personal', 'Group')


class User(db.Model, ModelOpsMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), nullable=False)
    email = db.Column(db.String(1000), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    username = db.Column(db.String(1000), unique=True, nullable=False)

    __table_args__ = (
        sa.CheckConstraint('char_length(password) >= 8',
                           name='password_min_length'),
    )

    @validates('password')
    def validate_password_length(self, key, password) -> str:
        if len(password) < 8:
            raise ValueError('password length too short')
        return password

    def __repr__(self):
        return f'User: {self.name}'


class Conversation(db.Model, ModelOpsMixin):
    __tablename__ = "conversation"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    owner = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(), nullable=False)
    personal_convo_participant = db.Column(db.Integer, nullable=True)
    group_convo_members = db.relationship('User', secondary=group_convo_members, lazy='subquery',
                                          backref=db.backref('conversations', lazy=True))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        sa.CheckConstraint('type IN ("Personal", "Group")',
                           name='conversation type options'),
    )

    @validates('type')
    def validate_password_length(self, key, type) -> str:
        if type not in CONVERSATION_TYPE_ENUM:
            raise ValueError('Conversation type can either be Personal or Group')
        return type

    def __repr__(self):
        return f'Conversation: {self.name} : {self.owner}'


class Message(db.Model, ModelOpsMixin):
    __tablename__ = "message"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    owner = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'Message: {self.conversation_id} : {self.owner} : {self.content}'


class RevokedAccessToken(db.Model, ModelOpsMixin):
    __tablename__ = "Revoked_token"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(), nullable=False)

    @classmethod
    def is_token_blacklisted(cls, jti):
        query = cls.query.filter_by(jti=jti).first()
        return bool(query)