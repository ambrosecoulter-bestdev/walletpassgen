#External Imports
from flask import render_template, flash, redirect, url_for, request, send_file
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





@app.route('/testgen', methods=['GET', 'POST'])
def test_gen():
    pkpassuuid = str(uuid.uuid4())
    cardInfo = StoreCard()
    cardInfo.addPrimaryField('name', u'Jähn Doe', 'Name')

    barcodeFormat = "PKBarcodeFormatQR"
    stdBarcode = Barcode('test barcode', barcodeFormat, 'alternate text')
    passfile = Pass(cardInfo, organizationName='Org Name', passTypeIdentifier='pass.com.yourcompany.some_name', teamIdentifier='ABCDE1234')
    
    passfile.serialNumber = pkpassuuid
    passfile.description = 'A Sample Pass'
    passfile.addFile('icon.png', open(app.root_path+'/static/images/icon.png', 'rb'))
    passfile.addFile('logo.png', open(app.root_path+'/static/images/logo.png', 'rb'))

     
    passfile.create(app.root_path+'/certificate.pem', app.root_path+'/private.key', app.root_path+'/wwdr_certificate.pem', "testing-123-drop-mic" , '/root/walletpassgen/generatedpasses/'+pkpassuuid+'.pkpass')
    return send_file("/root/walletpassgen/generatedpasses/"+pkpassuuid+".pkpass", as_attachment=False)
