from flask import Flask, request, jsonify, render_template, send_file
from PIL import Image
from pathlib import Path
import os
import bs4
import random
import string
import datetime

cwd = os.getcwd()

server_secret = "super-secret"
base_url = "http://127.0.0.1:5000"
image_char_length = 8


def write_to_file(file_name, data):
    with open(file_name, "w") as f:
        return f.write(data)


def read_file(file_name):
    with open(file_name, "r") as f:
        return f.read()


def random_word(length):
    return ''.join(random.choice(string.ascii_lowercase + string.digits + string.ascii_uppercase) for i in range(length))


def path_template(file_name):
    data = read_file(cwd + '/app/templates/image.html')
    prepared_url = ("%s/files/%s.png" % (base_url, file_name))

    date = datetime.datetime.now()

    # soup
    soup = bs4.BeautifulSoup(data)
    soup.title.string = file_name
    soup.find("meta", property="og:title")['content'] = file_name
    soup.find("meta", id="discord")['content'] = prepared_url
    soup.find("meta", property="og:description")['content'] = ("uploaded on %s" % date.strftime("%Y-%m-%d %H:%M"))
    soup.find("img")['src'] = prepared_url

    return str(soup.prettify())


def create_app():
    app = Flask(__name__)

    @app.route('/')
    def index():
        return '<code>image hosting service</code>'

    @app.route('/upload', methods=['POST'])
    def upload():
        secret = request.form['secret']
        file_name = random_word(image_char_length)

        if secret == server_secret:
            Path(cwd + '/app/templates/').mkdir(parents=True, exist_ok=True)
            Path(cwd + '/app/images/').mkdir(parents=True, exist_ok=True)

            image = Image.open(request.files['image'].stream)
            image.save((cwd + "/app/images/%s.png" % file_name), "PNG")

            template = path_template(file_name)
            write_to_file(cwd + "/app/templates/%s.html" % file_name, template)

            return jsonify({"filename": file_name})

        return jsonify({'error': 'invalid secret'}), 401

    @app.route('/files/<filename>')
    def pure_file_route(filename):
        file_path = cwd + '/app/images/%s' % filename
        if os.path.exists(file_path):
            return send_file(file_path)

        return jsonify({'error': 'images does not exist'}), 400

    @app.route('/<filename>')
    def file_route(filename):
        if os.path.exists(cwd + "/app/templates/%s.html" % filename):
            return render_template("%s.html" % filename)

        return jsonify({'error': 'image does not exist'}), 400

    return app


if __name__ == '__main__':
    create_app().run()
