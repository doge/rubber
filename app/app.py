import os
import hashlib
import random
import string

from app.utils import database, forms


from flask import Flask, request, jsonify, render_template, send_file, session, redirect, flash
from functools import wraps
from PIL import Image
from pathlib import Path


configuration = {
    'database': {
        'ip': 'mongodb',
        'port': 27017,
        'user': 'root',
        'password': 'toor',
        'db_name': 'image-host'
    },
    'base_url': 'http://127.0.0.1:5000',
    'secret_key': 'ksSvoPVG15CSw1sTBxqONCioNZzNn1HD',
    'image_char_length': 8

}

db_images = database.Database(configuration['database'], 'images')
db_users = database.Database(configuration['database'], 'users')
db_invites = database.Database(configuration['database'], 'invites')


def random_string(length):
    return ''.join(random.choice(string.ascii_lowercase + string.digits + string.ascii_uppercase) for i in range(length))


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user' in session:
            return f(*args, **kwargs)
        else:
            return redirect(configuration['base_url'] + '/login')

    return wrap


def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session['user']['role'] == 'admin':
            return f(*args, **kwargs)
        else:
            return redirect(configuration['base_url'] + '/login')

    return wrap


def create_app():
    app = Flask(__name__)
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    app.config['SECRET_KEY'] = configuration['secret_key']

    cwd = os.getcwd()

    @app.route('/')
    def index():
        return redirect(configuration['base_url'] + '/login')

    @app.route('/login', methods=['GET', 'POST'])
    def login():

        if 'user' in session:
            return redirect(configuration['base_url'] + '/panel')

        login_form = forms.LoginForm(request.form)
        if request.method == 'POST':
            if login_form.validate():
                    password = hashlib.sha256(login_form.password_login.data.encode('utf-8')).hexdigest()
                    user = db_users.find_one({'username': login_form.username_login.data, 'password': password})

                    if user:
                        if user['banned']:
                            flash('User is banned.', 'danger')
                            return redirect(configuration['base_url'] + '/login')

                        user['_id'] = str(user['_id'])
                        session['user'] = user
                        return redirect(configuration['base_url'] + '/panel')
                    else:
                        flash('Invalid credentials.', 'danger')
                        return redirect(configuration['base_url'] + '/login')

            else:
                flash('Please enter valid credentials.', 'danger')

        return render_template('home.html', login_form=login_form)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        register_form = forms.RegisterForm(request.form)
        if request.method == 'POST':
            if register_form.validate():
                password = hashlib.sha256(register_form.password_register.data.encode('utf-8')).hexdigest()

                # existing username check
                existing_username = db_users.find_one({
                    'username': register_form.username_register.data
                })

                if existing_username:
                    flash('Username already exists.', 'danger')
                else:
                    database_invite = db_invites.find_one({
                        'code': register_form.invite_code.data
                    })
                    if database_invite:
                        if not database_invite['used-by']:
                            # update invite collection
                            db_invites.update_one({
                                'code': database_invite['code']
                            }, {
                                '$set': {
                                    'used-by': register_form.username_register.data
                                }
                            })

                            # insert user into the database
                            db_users.insert({
                                'username': register_form.username_register.data,
                                'email': register_form.email_register.data,
                                'role': 'user',
                                'banned': False,
                                'password': password,
                                'token': random_string(32)
                            })
                            flash('Registration successful!', 'success')
                        else:
                            flash('Invite has been used.', 'danger')
                    else:
                        flash('Invite is invalid.', 'danger')

            else:
                flash('Please enter valid credentials.', 'danger')

        return render_template('register.html', register_form=register_form)

    @app.route('/logout')
    @login_required
    def logout():
        session.pop('user')
        return redirect(configuration['base_url'] + '/login')

    @app.route('/panel')
    @login_required
    def panel():
        current_user = db_users.find_one({
            'username': session['user']['username']
        })
        uploads = list(db_images.get_data(current_user['username']))
        invite_codes = list(db_invites.get_data(current_user['username']))
        users = list(db_users.find())
        reset_form = forms.PasswordReset(request.form)
        return render_template('panel.html', uploads=uploads, base_url=configuration['base_url'], invites=invite_codes,
                               users=users, user=current_user, reset_form=reset_form, len=len)

    @app.route('/reset', methods=['POST'])
    @login_required
    def reset():
        reset_form = forms.PasswordReset(request.form)
        if request.method == 'POST':
            if reset_form.validate():
                users = db_users.find_one({
                    'username': request.form['user']
                })
                current_password = hashlib.sha256(reset_form.current_password.data.encode('utf-8')).hexdigest()
                password = hashlib.sha256(reset_form.new_password.data.encode('utf-8')).hexdigest()
                if users['password'] == current_password:
                    db_users.update_one({
                        'username': request.form['user']
                    }, {
                        '$set': {
                            'password': password
                        }
                    })
                    flash('Password successfully reset.', 'success')
                else:
                    flash('Current password is incorrect.', 'danger')

                return redirect(configuration['base_url'] + '/panel')

        return redirect(configuration['base_url'] + '/panel')

    @app.route('/generate', methods=['POST', 'GET'])
    @login_required
    @admin_required
    def generate():
        if request.method == 'POST':
            invite_code = random_string(16)
            db_invites.insert({
                'author': request.form['author'],
                'code': invite_code,
                'used-by': ''
            })
            flash('invite: %s ' % invite_code)
            return redirect(configuration['base_url'] + '/panel')

        return redirect(configuration['base_url'] + '/login')

    @app.route('/ban', methods=['POST'])
    @login_required
    @admin_required
    def ban():
        if request.method == 'POST':
            # set their ban and make a set a new token
            user = db_users.find_one({
                'username': request.form['to-ban']
            })

            db_users.update_one({
                'username': request.form['to-ban']
            }, {
                '$set': {
                    'banned': not user['banned']
                }
            })
            flash('User "%s" ban status changed.' % request.form['to-ban'])
            return redirect(configuration['base_url'] + '/panel')
        return redirect(configuration['base_url'] + '/login')

    @app.route('/token', methods=['POST'])
    @login_required
    def token():
        if request.method == 'POST':
            db_users.update_one({
                'username': request.form['user']
            }, {
                '$set': {
                    'token': random_string(32)
                }
            })
            flash('Token successfully changed.', 'success')
            return redirect(configuration['base_url'] + '/panel')
        return redirect(configuration['base_url'] + '/login')

    @app.route('/config')
    @login_required
    def config():
        return jsonify({
            "DestinationType": "ImageUploader",
            "RequestURL": configuration['base_url'] + "/upload",
            "FileFormName": "image",
            "Arguments": {
                "secret": session['user']['token']
            },
            "URL": configuration['base_url'] + "/$json:filename$"
        })

    @app.route('/upload', methods=['POST'])
    def upload():
        # find the user with the matching token
        user = db_users.find_one({'token': request.form['secret']})
        if user['banned']:
            return jsonify({'error': 'user is banned'}), 401
        elif user:
            # create directory if it doesn't exist
            Path(cwd + "/app/images/%s" % user['username']).mkdir(parents=True, exist_ok=True)

            # generate a unique filename
            file_name = random_string(configuration['image_char_length'])
            while db_images.image_exists({'name': file_name}):
                file_name = random_string(configuration['image_char_length'])

            # insert into db
            db_images.insert_image({
                'author': user['username'],
                'name': file_name
            })

            # get the image from the request and save it
            image = Image.open(request.files['image'].stream)
            image.save((cwd + "/app/images/%s/%s.png" % (user['username'], file_name)), "PNG")

            return jsonify({"filename": file_name})

        return jsonify({'error': 'invalid secret'}), 401

    @app.route('/delete', methods=['POST'])
    @login_required
    def delete():
        if request.method == 'POST':
            file_name = request.form['to-remove']
            image = db_images.find_one({'name': file_name})
            if session['user']['username'] == image['author']:

                # remove from db and delete file
                db_images.delete_one({
                    'name': file_name
                })
                os.remove((cwd + "/app/images/%s/%s.png" % (session['user']['username'], file_name)))

                flash('successfully deleted %s' % image['name'])
                return redirect(configuration['base_url'] + '/panel')

            return jsonify({'error': 'not authorized'}), 401

    @app.route('/files/<username>/<filename>')
    def pure_file_route(username, filename):
        file_path = cwd + '/app/images/%s/%s' % (username, filename)
        if os.path.exists(file_path):
            return send_file(file_path)

        return jsonify({'error': 'not found'}), 404

    @app.route('/<image_name>')
    def file_route(image_name):
        file = db_images.find_one({'name': image_name})
        if file:
            return render_template("image.html", base_url=configuration['base_url'], file=file)

        return jsonify({'error': 'not found'}), 404

    return app


if __name__ == '__main__':
    create_app().run()
