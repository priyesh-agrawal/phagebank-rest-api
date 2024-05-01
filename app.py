import os

###
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_restful import Api
from flask_jwt_extended import JWTManager

from db import db
from blacklist import BLACKLIST
from resources.user import UserRegister, UserList
from resources.userlogin import UserLogin, UserLogout, ChangePasswd, DropUser #TokenRefresh

from resources.phagebank import (LotList, PatientToVial, UserPatientVial, AddNewLot, UpdateUsedVial, UpdateUNUsedVial,
        TrialForPatient, VialForPatient, PatientsForUser, PatientsForUserDev, GetLotFromPatientIDTrialID, GetVialFromLotIdandFreezerId, 
        AddNewPatient, GetFreezerLocationFromVial, UpdatePatientInfo, UpdateFreezerProForUsedSample, SendMailFromClinical, 
        UpdateVialForPatient, AddNewUser, GetRandomizationInfo
        )

from resources.api_doc import GetAPIDoc
from jwt_redis_blocklist import JWT_REDIS_BLOCKLIST, ACCESS_EXPIRES

app = Flask(__name__, static_folder="documents")

CORS(app)
app.route("/")

app.config['DEBUG'] = True

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = ACCESS_EXPIRES
api = Api(app)

"""
JWT related configuration. The following functions includes:
1) add claims to each jwt
2) customize the token expired error message 
"""
app.config['JWT_SECRET_KEY'] = 'ABC'                                # we can also use app.secret like before, Flask-JWT-Extended can recognize both
#app.config['JWT_BLACKLIST_ENABLED'] = True                          # enable blacklist feature
#app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']    # allow blacklisting for access and refresh tokens
jwt = JWTManager(app)

"""
`claims` are data we choose to attach to each jwt payload
and for each jwt protected endpoint, we can retrieve these claims via `get_jwt_claims()`
one possible use case for claims are access level control, which is shown below

"""
'''
@jwt.additional_claims_loader
def add_claims_to_jwt(identity):
    if identity == 1:                                               #instead of hard-coding, we should read from a config file to get a list of admins instead
        return {'is_admin': True}
    return {'is_admin': False}

'''
                                                                    #This method will check if a token is blacklisted, and will be called automatically when blacklist is enabled
'''
@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(decrypted_token):
    return decrypted_token['jti'] in BLACKLIST
'''

@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    token_in_redis = JWT_REDIS_BLOCKLIST.get(jti)
    return token_in_redis is not None


# The following callbacks are used for customizing jwt response/error messages.
# The original ones may not be in a very pretty format.

#@jwt.expired_token_loader
#def expired_token_callback():
#    return jsonify({
#        'message': 'The token has expired.',
#        'error': 'token_expired'
#    }), 401


#@jwt.invalid_token_loader
#def invalid_token_callback(error):  # we have to keep the argument here, since it's passed in by the caller internally
#    return jsonify({
#        'message': 'Signature verification failed.',
#        'error': 'invalid_token'
#    }), 401


#@jwt.unauthorized_loader
#def missing_token_callback(error):
#    return jsonify({
#        "description": "Request does not contain an access token.",
#        'error': 'authorization_required'
#    }), 401


#@jwt.needs_fresh_token_loader
#def token_not_fresh_callback():
#    return jsonify({
#        "description": "The token is not fresh.",
#        'error': 'fresh_token_required'
#    }), 401


#@jwt.revoked_token_loader
#def revoked_token_callback():
#    return jsonify({
#        "description": "The token has been revoked.",
#        'error': 'token_revoked'
#    }), 401

# JWT configuration ends

#@app.before_first_request
#def create_tables():
#    db.create_all()

#User API's
api.add_resource(UserRegister, '/register')
api.add_resource(UserLogin, '/login')
api.add_resource(UserList, '/all_users')
#api.add_resource(TokenRefresh, '/refresh')
api.add_resource(UserLogout, '/logout')
api.add_resource(ChangePasswd, '/changepassword')

#PhageBank API's
api.add_resource(LotList, '/all_lot')
api.add_resource(AddNewLot, '/add_lot')
api.add_resource(PatientToVial, '/get_patient_vial/<string:query_patient_id>')
api.add_resource(UserPatientVial, '/get_user_patient_vial/<string:query_user_id>')

api.add_resource(UpdateUsedVial, '/update_used_vial/<string:serial_number>')
api.add_resource(UpdateUNUsedVial, '/update_vial_to_unused/<string:serial_number>')

api.add_resource(TrialForPatient, '/trial_for_patient/<string:query_patient_id>')
api.add_resource(VialForPatient, '/vial_for_patient/<string:query_patient_id>/<string:query_freezer_barcode>')
api.add_resource(PatientsForUser, '/get_user_patient')
api.add_resource(PatientsForUserDev, '/get_user_patient_dev')

api.add_resource(GetLotFromPatientIDTrialID, '/get_lot_for_patient_trial/<string:query_patient_id>/<string:query_trial_id>')
api.add_resource(GetVialFromLotIdandFreezerId, '/get_vial_for_lot_freezer/<string:query_lot_id>/<string:query_freezer_id>')
api.add_resource(AddNewPatient, '/add_patient')
api.add_resource(UpdatePatientInfo, '/update_patient_info')
api.add_resource(UpdateFreezerProForUsedSample, '/update_freezer_pro_for_used_vial/<string:vial_serial_number>')
api.add_resource(GetFreezerLocationFromVial, '/get_freezer_location/<string:vial_serial_number>')
api.add_resource(SendMailFromClinical, '/send_mail')
api.add_resource(UpdateVialForPatient, '/update_vial_for_patient')
api.add_resource(AddNewUser, '/add_new_user')
api.add_resource(GetRandomizationInfo, '/get_randomization_info/<string:patientid>/<string:userid>/<string:randnumber>')
api.add_resource(DropUser, '/flag_user')

#API for All API's
api.add_resource(GetAPIDoc, '/api_document')


if __name__ == '__main__':
    from db import db
    db.init_app(app)

    if app.config['DEBUG']:
        @app.before_first_request
        def create_tables():
            db.create_all()

    app.run()
