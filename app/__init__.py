from flask import Flask
from .routes.user import usermod
from .routes.site import site
#from .routes.backend import backend
from .extentions import database
from .commands.userCommands import userCommands
from .commands.email import emailCommands
from .cache import cache

def create_app(config_object="app.settings"):
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.register_blueprint(usermod)
    app.register_blueprint(site)
    #app.register_blueprint(backend)
    app.register_blueprint(userCommands)
    app.register_blueprint(emailCommands)
    LOGLEVEL = app.config.get('LOGLEVEL')
    app.logger.setLevel(LOGLEVEL)
    app.config.update(
        SESSION_COOKIE_DOMAIN=app.config.get('DOMAIN'),
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE="Lax"
    )

    cache.init_app(app)
    database.init_app(app)

    return app
