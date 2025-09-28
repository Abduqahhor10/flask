from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from models import User


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=128)])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    profile_image = FileField('Profile Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])  # yangi qo‘shildi
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class BlogForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    image = FileField('Blog Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Save')


class CommentForm(FlaskForm):
    text = TextAreaField('Comment', validators=[DataRequired(), Length(min=1, max=2000)])
    submit = SubmitField('Post')
