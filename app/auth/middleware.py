from flask import session, redirect, url_for
from functools import wraps


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('auth.login'))

    return wrap


def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session['user']['role'] == 'admin':
            return f(*args, **kwargs)
        else:
            return redirect(url_for('auth.login'))

    return wrap
