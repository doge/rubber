from flask import Flask, request, jsonify, render_template, send_file
from PIL import Image
from . import database
import os
import random
import string

server_secret = "super-secret"
base_url = "https://img.gabe.cat"
image_char_length = 8

database_credentials = {
    'ip': 'mongodb',
    'port': 27017,
    'database': 'image-host',
    'collection': 'images'
}

cwd = os.getcwd()
database = database.Database(database_credentials)


def random_string(length):
    return ''.join(random.choice(string.ascii_lowercase + string.digits + string.ascii_uppercase) for i in range(length))


def create_app():
    app = Flask(__name__)

    @app.route('/')
    def index():
        return '<code>image hosting service</code>'

    @app.route('/upload', methods=['POST'])
    def upload():
        secret = request.form['secret']
        file_name = random_string(image_char_length)

        if secret == server_secret:
            database.insert_image({
                'author': 'gabe',
                'name': file_name
            })

            image = Image.open(request.files['image'].stream)
            image.save((cwd + "/app/images/%s.png" % file_name), "PNG")

            return jsonify({"filename": file_name})

        return jsonify({'error': 'invalid secret'}), 401

    @app.route('/files/<filename>')
    def pure_file_route(filename):
        file_path = cwd + '/app/images/%s' % filename
        if os.path.exists(file_path):
            return send_file(file_path)

        return jsonify({'error': 'images does not exist'}), 400

    @app.route('/<image_name>')
    def file_route(image_name):
        file = database.find_one({'name': image_name})
        if file:
            return render_template("image.html", base_url=base_url, file=file)

        return jsonify({'error': 'image does not exist'}), 400

    return app


if __name__ == '__main__':
    create_app().run()
