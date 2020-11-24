from wtforms import Form, SubmitField, StringField, PasswordField, validators
from wtforms.fields.html5 import EmailField


class LoginForm(Form):
    username_login = StringField('username', [
        validators.Length(min=4, max=25),
        validators.DataRequired()
    ])
    password_login = PasswordField('password', [
        validators.DataRequired()
    ])
    button_login = SubmitField('Submit')


class RegisterForm(Form):
    username_register = StringField('username', [
        validators.Length(min=4, max=25),
        validators.DataRequired()
    ])
    email_register = EmailField('email', [
        validators.DataRequired(),
        validators.Email()
    ])
    password_register = PasswordField('password', [
        validators.DataRequired()
    ])
    invite_code = StringField('invite-code', [
        validators.Length(min=0, max=32),
        validators.DataRequired()
    ])
    button_register = SubmitField('Submit')


class PasswordReset(Form):
    current_password = PasswordField('current-password', [
        validators.DataRequired()
    ])
    new_password = PasswordField('new-password', [
        validators.DataRequired(),
        validators.EqualTo('new_password_confirm', message='Passwords must match.')
    ])
    new_password_confirm = PasswordField('new-password-confirm', [
        validators.DataRequired()
    ])
    button_submit = SubmitField('Submit')
