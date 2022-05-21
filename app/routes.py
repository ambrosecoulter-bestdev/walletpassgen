#External Imports
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
import uuid
from datetime import datetime

#Internal Imports
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm
from app.models import User

from wallet.models import Pass, Barcode, StoreCard

import json

from M2Crypto import BIO
from M2Crypto import SMIME
from M2Crypto import X509
from path import Path



###
# Init
###

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

###
# Routes
###


cwd = Path(__file__).parent

wwdr_certificate = cwd / 'certificates' / 'wwdr_certificate.pem'
certificate = cwd / 'certificates' / 'certificate.pem'
key = cwd / 'certificates' / 'private.key'
password_file = cwd / 'certificates' / 'password.txt'




@app.route('/')
@app.route('/index')
@login_required
def index():
    user = {'username': 'Kyle'}
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Home', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, uuid=str(uuid.uuid4()))
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<user_uuid>')
@login_required
def user(user_uuid):
    user = User.query.filter_by(uuid=user_uuid).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)




@app.route('/testgen', methods=['GET', 'POST'])
def test_gen():
    pass_type_identifier = "pass.com.yourcompany.some_name"
    team_identifier = "ABCDE1234"  # Your Apple team ID
    cert_pem = "certficate.pem"
    key_pem = "private.pem"
    wwdr_pem = "wwdr_certificate.pem"
    key_pem_password = "testing-123-drop-mic"
    organization_name="testorg"

    cardInfo = StoreCard()
    cardInfo.addPrimaryField('name', 'John Doe', 'Name')

    passfile = Pass(cardInfo,
                    passTypeIdentifier=pass_type_identifier,
                    organizationName=organization_name,
                    teamIdentifier=team_identifier)

    # charge_response.id is trackable via the Stripe dashboard
    passfile.serialNumber = "324234234"
    passfile.barcode = Barcode(message = "testqrgen", format="PKBarcodeFormatQR")
    passfile.description = "testgen"

    # Including the icon and logo is necessary for the passbook to be valid.
    passfile.addFile("icon.png", open("static/images/icon.png", "rb"))
    passfile.addFile("logo.png", open("logo.png", "rb"))
    _ = passfile.create(cert_pem,
                        key_pem,
                        wwdr_pem,
                        key_pem_password,
                        "pass_name.pkpass")
    return "success"

