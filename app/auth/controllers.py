from flask import (Blueprint, session, redirect, request,
                   render_template, flash, url_for)

from .forms import LoginForm, RegisterForm
from ..interfaces import Interfaces
from ..utils import misc
from .middleware import login_required

import hashlib

auth = Blueprint("auth", __name__, template_folder='templates')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('home.panel'))

    login_form = LoginForm(request.form)
    if request.method == 'POST':
        if login_form.validate():
            password = hashlib.sha256(login_form.password_login.data.encode('utf-8')).hexdigest()
            user = Interfaces.users.find_one({'username': login_form.username_login.data, 'password': password})

            if user:
                if user['banned']:
                    flash('User is banned.', 'danger')
                    return redirect(url_for('auth.login'))

                user['_id'] = str(user['_id'])
                session['user'] = user
                return redirect(url_for('home.panel'))
            else:
                flash('Invalid credentials.', 'danger')
                return redirect(url_for('auth.login'))

        else:
            flash('Please enter valid credentials.', 'danger')

    return render_template('home.html', login_form=login_form)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm(request.form)
    if request.method == 'POST':
        if register_form.validate():
            password = hashlib.sha256(register_form.password_register.data.encode('utf-8')).hexdigest()

            # existing username check
            existing_username = Interfaces.users.find_one({
                'username': register_form.username_register.data
            })

            if existing_username:
                flash('Username already exists.', 'danger')
            else:
                database_invite = Interfaces.invites.find_one({
                    'code': register_form.invite_code.data
                })
                if database_invite:
                    if not database_invite['used-by']:
                        # update invite collection
                        Interfaces.invites.update_one({
                            'code': database_invite['code']
                        }, {
                            '$set': {
                                'used-by': register_form.username_register.data
                            }
                        })

                        # insert user into the database
                        Interfaces.users.insert({
                            'username': register_form.username_register.data,
                            'email': register_form.email_register.data,
                            'role': 'user',
                            'banned': False,
                            'password': password,
                            'token': misc.random_string(32)
                        })
                        flash('Registration successful!', 'success')
                        return redirect(url_for('auth.login'))
                    else:
                        flash('Invite has been used.', 'danger')
                else:
                    flash('Invite is invalid.', 'danger')

        else:
            flash('Please enter valid credentials.', 'danger')

    return render_template('register.html', register_form=register_form)


@auth.route('/logout')
@login_required
def logout():
    session.pop('user')
    return redirect(url_for('auth.login'))
