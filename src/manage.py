from .app import create_flask_app, db
from .app.models.models import User, RevokedAccessToken, Conversation, Message

app = create_flask_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'RevokedAccessToken': RevokedAccessToken,
            'Conversation': Conversation, 'Message': Message}
