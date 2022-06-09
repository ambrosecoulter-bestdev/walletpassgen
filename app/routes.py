#External Imports
from flask import render_template, flash, redirect, url_for, request, send_file
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
import uuid
from datetime import datetime
import urllib
import os
import urllib.request

#Internal Imports
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm
from app.models import User

from wallet.models import Pass, Barcode, StoreCard, EventTicket, Generic, IBeacon

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
    if request.form['TicketType'] == 'Generic':
        cardInfo = Generic()
    else:
        return 'error'
        
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
    #BACKFIELD
    if request.form['PassBackInformation'] != '':
        bffi = json.loads(request.form['PassBackInformation'])
        cardInfo.addBackField(bffi["key"], bffi["value"], bffi["label"])
    cardInfo.addBackField('disclaimer', 'This pass has been created "" for evaluation purposes using the third party service Spectrum which is owned and operated by Spectrum in Queensland Australia. The pass issuer has attested that any trademarks and/or copyrighted content contained within this pass are being used with the consent of the owner. Questions, complaints or claims with respect to this pass should be addressed to the pass issuer"". NEITHER APPLE NOR SPECTRUM SHALL be liable for any damages or losses arising for any use, distribution, misuse, reliance on, inability to use, interruption, suspension or termination of passbook, this pass, or any services provided in connection therewithin, including but not limited to any loss or failure to display your pass in passbook or any claim arising from any use of the foregoing by you, the pass issuer.', 'Disclaimer')


    #CUSTOMISATION
    passfile.description = request.form['Description']
    passfile.backgroundColor = request.form['BackgroundColor']
    passfile.foregroundColor = request.form['ForegroundColor']
    passfile.labelColor = request.form['LabelColor']
    passfile.ibeacons = [IBeacon('EFB8454C-6988-11EB-9439-0242AC130002',0,0),]



    #BARCODE
    if request.form['Barcode'] != '':
        bfi = json.loads(request.form['Barcode'])
        barcodeFormat = bfi["barcodeFormat"]
        stdBarcode = Barcode(bfi["value"], barcodeFormat, bfi["alternateText"])
        passfile.barcode = stdBarcode


    
    #LOGOS
    passfile.addFile('icon.png', open('/root/walletpassgen/ticketimages/'+request.form['iconPath'], 'rb'))
    passfile.addFile('icon@2x.png', open('/root/walletpassgen/ticketimages/'+request.form['iconPath'], 'rb'))
    passfile.addFile('logo.png', open('/root/walletpassgen/ticketimages/'+request.form['logoPath'], 'rb'))

     






    jsonpassuuid = {'passuuid':pkpassuuid}
    passfile.create(app.root_path+'/certificate.pem', app.root_path+'/key.pem', app.root_path+'/wwdr_certificate.pem', "challenge1!" , '/root/walletpassgen/generatedpasses/'+pkpassuuid+'.pkpass')
    
    if os.path.exists('/root/walletpassgen/ticketimages/'+request.form['iconPath']):
        os.remove('/root/walletpassgen/ticketimages/'+request.form['iconPath'])
        
    
    return json.dumps(jsonpassuuid)


@app.route('/passdownload/<passid>', methods=['GET', 'POST'])
def pass_download(passid):
    return send_file("/root/walletpassgen/generatedpasses/"+passid+".pkpass", as_attachment=False)




@app.route('/imageupload', methods=['GET', 'POST'])
def image_upload():
    imageuuid = str(uuid.uuid4())
    if request.form['imageURL'] != '':
        urllib.request.urlretrieve(request.form['imageURL'], "/root/walletpassgen/ticketimages/"+imageuuid+"."+request.form['imageType'])
    jsonimageuuid = {'imagePath':imageuuid+'.'+request.form['imageType']}
    return jsonimageuuid