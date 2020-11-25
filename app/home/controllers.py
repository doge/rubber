from flask import (Blueprint, session, redirect, request,
                   render_template, flash, url_for)


from ..auth.middleware import login_required, admin_required
from ..interfaces import Interfaces
from ..auth.forms import PasswordReset
from ..utils import misc

import hashlib

home = Blueprint("home", __name__, template_folder='templates')


@home.route('/panel')
@login_required
def panel():
    current_user = Interfaces.users.find_one({
        'username': session['user']['username']
    })
    uploads = list(Interfaces.images.get_data(current_user['username']))
    invite_codes = list(Interfaces.invites.get_data(current_user['username']))
    users = list(Interfaces.users.find())
    reset_form = PasswordReset(request.form)

    return render_template('panel.html', uploads=uploads, invites=invite_codes, users=users,
                           user=current_user, reset_form=reset_form, len=len)


@home.route('/reset', methods=['POST'])
@login_required
def reset():
    reset_form = PasswordReset(request.form)
    if request.method == 'POST':
        if reset_form.validate():
            users = Interfaces.users.find_one({
                'username': request.form['user']
            })
            current_password = hashlib.sha256(reset_form.current_password.data.encode('utf-8')).hexdigest()
            password = hashlib.sha256(reset_form.new_password.data.encode('utf-8')).hexdigest()
            if users['password'] == current_password:
                Interfaces.users.update_one({
                    'username': request.form['user']
                }, {
                    '$set': {
                        'password': password
                    }
                })
                flash('Password successfully reset.', 'success')
            else:
                flash('Current password is incorrect.', 'danger')

            return redirect(url_for('home.panel'))

    return redirect(url_for('home.panel'))


@home.route('/generate', methods=['POST', 'GET'])
@login_required
@admin_required
def generate():
    if request.method == 'POST':
        invite_code = misc.random_string(16)
        Interfaces.invites.insert({
            'author': request.form['author'],
            'code': invite_code,
            'used-by': ''
        })
        flash('Generated: %s ' % invite_code, 'success')
        return redirect(url_for('home.panel'))

    return redirect(url_for('auth.login'))


@home.route('/ban', methods=['POST'])
@login_required
@admin_required
def ban():
    if request.method == 'POST':
        # set their ban and make a set a new token
        user = Interfaces.users.find_one({
            'username': request.form['to-ban']
        })

        Interfaces.users.update_one({
            'username': request.form['to-ban']
        }, {
            '$set': {
                'banned': not user['banned']
            }
        })
        flash('User "%s" ban status changed.' % request.form['to-ban'])
        return redirect(url_for('home.panel'))
    return redirect(url_for('auth.login'))


@home.route('/token', methods=['POST'])
@login_required
def token():
    if request.method == 'POST':
        Interfaces.users.update_one({
            'username': request.form['user']
        }, {
            '$set': {
                'token': misc.random_string(32)
            }
        })
        flash('Token successfully changed.', 'success')
        return redirect(url_for('home.panel'))
    return redirect(url_for('auth.login'))
