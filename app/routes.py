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

from wallet.models import Pass, Barcode, StoreCard, EventTicket

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


    ###
    #EVENT TICKET GENERATION
    ###
    if request.form['TicketType'] == 'EventTicket':
        cardInfo = EventTicket()
        
        passfile = Pass(cardInfo, organizationName='Org Name', passTypeIdentifier='pass.com.spectrum.ticketpass', teamIdentifier='PFWC6XGUU8')
        passfile.serialNumber = pkpassuuid



        #FIELDS
        #PRIMARY
        if request.form['PrimaryField'] != '':
            pfi = json.loads(request.form['PrimaryField'])
            cardInfo.addPrimaryField(pfi["key"], pfi["value"], pfi["label"])
        #SECONDARY
        if request.form['SecondaryField'] != '':
            sfi = json.loads(request.form['SecondaryField'])
            cardInfo.addPrimaryField(sfi["key"], sfi["value"], sfi["label"])



        #CUSTOMISATION
        passfile.description = request.form['Description']
        passfile.backgroundColor = request.form['BackgroundColor']
        passfile.foregroundColor = request.form['ForegroundColor']
        passfile.labelColor = request.form['LabelColor']



        #BARCODE
        if request.form['Barcode'] != '':
            bfi = json.loads(request.form['Barcode'])
            barcodeFormat = bfi["barcodeFormat"]
            stdBarcode = Barcode(bfi["value"], barcodeFormat, bfi["alternateText"])
            passfile.barcode = stdBarcode
    

        
        #LOGOS
        passfile.addFile('icon.png', open(app.root_path+'/static/images/icon.png', 'rb'))
        passfile.addFile('icon@2x.png', open(app.root_path+'/static/images/icon.png', 'rb'))
        passfile.addFile('logo.png', open(app.root_path+'/static/images/logo.png', 'rb'))
    else:
        return 'error'
     






    jsonpassuuid = {'passuuid':pkpassuuid}
    passfile.create(app.root_path+'/certificate.pem', app.root_path+'/key.pem', app.root_path+'/wwdr_certificate.pem', "challenge1!" , '/root/walletpassgen/generatedpasses/'+pkpassuuid+'.pkpass')
    return json.dumps(jsonpassuuid)


@app.route('/passdownload/<passid>', methods=['GET', 'POST'])
def pass_download(passid):
    return send_file("/root/walletpassgen/generatedpasses/"+passid+".pkpass", as_attachment=False)