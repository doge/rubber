import os

from flask import (Blueprint, session, redirect, request, send_file,
                   render_template, flash, url_for, jsonify)

from PIL import Image
from pathlib import Path

from ..utils import misc
from ..config import Config
from ..interfaces import Interfaces
from ..auth.middleware import login_required


cwd = os.getcwd()
files = Blueprint('files', __name__, template_folder='templates')


@files.route('/config')
@login_required
def config():
    return jsonify({
        "DestinationType": "ImageUploader",
        "RequestURL": request.host_url + "/upload",
        "FileFormName": "image",
        "Arguments": {
            "token": session['user']['token']
        },
        "URL": request.host_url + "/$json:filename$"
    })


@files.route('/upload', methods=['POST'])
def upload():
    # find the user with the matching token
    user = Interfaces.users.find_one({'token': request.form['token']})
    if user['banned']:
        return jsonify({'error': 'user is banned'}), 401
    elif user:
        # create directory if it doesn't exist
        Path(cwd + "/app/images/%s" % user['username']).mkdir(parents=True, exist_ok=True)

        # generate a unique filename
        file_name = misc.random_string(Config.image_char_length)
        while Interfaces.images.image_exists({'name': file_name}):
            file_name = misc.random_string(Config.image_char_length)

        # insert into db
        Interfaces.images.insert_image({
            'author': user['username'],
            'name': file_name
        })

        # get the image from the request and save it
        image = Image.open(request.files['image'].stream)
        image.save((cwd + "/app/images/%s/%s.png" % (user['username'], file_name)), "PNG")

        return jsonify({"filename": file_name})

    return jsonify({'error': 'invalid token'}), 401


@files.route('/delete', methods=['POST'])
@login_required
def delete():
    if request.method == 'POST':
        file_name = request.form['to-remove']
        image = Interfaces.images.find_one({'name': file_name})
        if session['user']['username'] == image['author']:
            # remove from db and delete file
            Interfaces.images.delete_one({
                'name': file_name
            })
            os.remove((cwd + "/app/images/%s/%s.png" % (session['user']['username'], file_name)))

            flash('successfully deleted %s' % image['name'])
            return redirect(url_for('home.panel'))

        return jsonify({'error': 'not authorized'}), 401


@files.route('/files/<username>/<filename>')
def pure_file_route(username, filename):
    file_path = cwd + '/app/images/%s/%s' % (username, filename)
    if os.path.exists(file_path):
        return send_file(file_path)

    return jsonify({'error': 'not found'}), 404


@files.route('/<image_name>')
def file_route(image_name):
    file = Interfaces.images.find_one({'name': image_name})
    if file:
        return render_template("image.html", file=file)

    return jsonify({'error': 'not found'}), 404
