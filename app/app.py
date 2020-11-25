import os
from .auth.middleware import login_required


from flask import Flask, redirect, url_for

from .config import Config

from .auth.controllers import auth
from .home.controllers import home
from .files.controllers import files

cwd = os.getcwd()


def register_blueprints(app):
    app.register_blueprint(auth)
    app.register_blueprint(home)
    app.register_blueprint(files)


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = Config.secret_key
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

    register_blueprints(app)

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    return app


if __name__ == '__main__':
    create_app().run()
