from app.user import user_bp
from app.post import post_bp
import os
import secrets
from datetime import datetime

from PIL import Image
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app import db
from app import bcrypt
from .forms import LoginForm, RegistrationForm, UpdateAccountForm
from ..models import User


@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('post_bp.posts'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            flash("Sing in successfully", "success")
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('post_bp.posts')
            return redirect(next_page)
        else:
            flash('Login or password is incorrect', 'warning')
    return render_template('login.html', form=form)


@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('post_bp.posts'))
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')

        user = User(username=username, email=email, password_hash=hashed)
        db.session.add(user)
        db.session.commit()
        flash("Sing up successfully")
    return render_template('register.html', form=form)


@user_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('post_bp.posts'))


@user_bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.about_me = form.about_me.data
        if form.old_password.data:
            current_user.password_hash = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
        db.session.commit()
        flash('Your account has been updated!', 'success')
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.about_me.data = current_user.about_me
    image_file = url_for('static', filename='images/thumbnails/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form, user=current_user)


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    f_name, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = f_name + random_hex + f_ext
    picture_path = os.path.join(user_bp.root_path, 'static/images/thumbnails/', picture_fn)
    # form_picture.save(picture_path)

    output_size = (128, 128)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@user_bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
