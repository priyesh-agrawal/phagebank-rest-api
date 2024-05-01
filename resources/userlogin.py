from db import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask import jsonify
from flask_restful import Resource, reqparse
from jwt_redis_blocklist import JWT_REDIS_BLOCKLIST, ACCESS_EXPIRES
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    #revoke_token,
    #jwt_refresh_token_required,
    get_jwt_identity,
    get_jwt,
    jwt_required
)

from models.phagebank import UserModel
from models.database_log import LogInfo

import datetime
from blacklist import BLACKLIST

_user_parser = reqparse.RequestParser()
_user_parser.add_argument('username',
                          type=str,
                          required=True,
                          help="This field cannot be blank."
                          )
_user_parser.add_argument('password',
                          type=str,
                          required=True,
                          help="This field cannot be blank."
                          )


class UserLogin(Resource):
    def post(self):
        data = _user_parser.parse_args()

        user = UserModel.find_by_username(data['username'])
        role = UserModel.find_role_by_username(data['username'])
        
        if user and check_password_hash(user.password, data['password']):
            if user.isLive == 0:
                ###REPORTING LOG
                now = datetime.datetime.now()
                dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
                user_log = LogInfo(None, data['username'], 'login', 'Not Applicable', "*User Login", 'API', dt_string, "This User is Flagged and can not LogIn!")
                user_log.save_to_db()
                ###
                return {"message": "This User is Flagged and can not LogIn!"}, 401
            
            ###REPORTING LOG
            now = datetime.datetime.now()
            dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
            user_log = LogInfo(None, data['username'], 'login', 'Not Applicable', "*User Login", 'API', dt_string, "User Successfully LoggedIn!")
            user_log.save_to_db()
            ###
            
            if role.descr == 'admin':
                access_token = create_access_token(identity=user.idUser, fresh=True, additional_claims={"is_administrator": True})
                refresh_token = create_refresh_token(user.idUser, additional_claims={"is_administrator": True})
            else:
                access_token = create_access_token(identity=user.idUser, fresh=True)
                refresh_token = create_refresh_token(user.idUser)
            return {
                       'access_token': access_token,
                       'refresh_token': refresh_token,
                       'msg' : 'User Logged In!',
                       'Role' : role.descr
                   }, 200

        ###REPORTING LOG
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
        user_log = LogInfo(None, data['username'], 'login', 'Not Applicable', "*User Login", 'API', dt_string, "Invalid Credentials!")
        user_log.save_to_db()
        ###
        return {"message": "Invalid Credentials!"}, 401


class UserLogout(Resource):
    @jwt_required()
    def post(self):
        
        ###REPORTING LOG
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
        user_id = get_jwt_identity()
        user_inf = UserModel.find_by_id(user_id)
        user_log = LogInfo(None, user_inf.username, 'logout', 'Not Applicable', "*User Logout", 'API', dt_string, "Access token revoked!")
        user_log.save_to_db()
        ###
        
        jti = get_jwt()["jti"]
        JWT_REDIS_BLOCKLIST.set(jti, "", ex=ACCESS_EXPIRES)
        return jsonify(msg="Access token revoked!")



class ChangePasswd(Resource):
    @jwt_required()
    def post(self):
        loggedin_user_id = get_jwt_identity()
        loggedin_user_role = UserModel.find_role_by_userid(loggedin_user_id)
        user_role = loggedin_user_role.descr
        user_role = "everybody"
        if user_role == 'everybody':
            ###REPORTING LOG
            now = datetime.datetime.now()
            dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
            user_inf = UserModel.find_by_id(loggedin_user_id)
            user_log = LogInfo(None, user_inf.username, 'changepassword', 'Not Applicable', "*User Changed Password!", 'API', dt_string, "Changing password")
            user_log.save_to_db()
            ###
            data = _user_parser.parse_args()
            user = UserModel.query.filter_by(username=data['username']).first()
            if user:
                try:
                    if check_password_hash(user.password, data['password']):
                        return{'message':'Error: new Password can not be the current Password'}
                    else:
                        user.password = generate_password_hash(data['password'])
                        user.save_to_db()
                except Exception as Err:
                    return{'message':'Error: {}'.format(str(Err))}
                return{'message': "Password successfully updated for User '{}'".format(user.username)}
            else:
                return{'message': "Username '{}' does not Exists!".format(data['username'])}
        else:
            ###REPORTING LOG
            now = datetime.datetime.now()
            dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
            user_inf = UserModel.find_by_id(loggedin_user_id)
            user_log = LogInfo(None, user_inf.username, 'changepassword', 'Not Applicable', "*User Changed Password!", 'API', dt_string, "Only Admins are Authorized for this task!")
            user_log.save_to_db()
            ###
            return{'message': "Only Admins are Authorized for this task! (Your AuthRole: {})".format(loggedin_user_role.descr)}



class DropUser(Resource):

    parserDropUser = reqparse.RequestParser()
    parserDropUser.add_argument('user_id', type=int, required=False, help="Provide UserId to Flag!")
    parserDropUser.add_argument('user_name', type=str, required=False, help="Provide UserName to Flag")
    
    @jwt_required()
    def post(self):
        loggedin_user_id = get_jwt_identity()
        loggedin_user_role = UserModel.find_role_by_userid(loggedin_user_id)
        user_inf_log = UserModel.find_by_id(loggedin_user_id)
        if loggedin_user_role.descr == 'admin':
            inputdata = self.parserDropUser.parse_args()
            if inputdata['user_id']:
                #print('user_id', inputdata)
                user_inf = UserModel.query.filter_by(idUser=inputdata['user_id']).first()
                user_inf.isLive = 0
                db.session.commit()
                
                ###REPORTING LOG
                now = datetime.datetime.now()
                dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
                user_log = LogInfo(None, user_inf_log.username, 'flag_user', str(inputdata['user_id']), "*Flaging The User using user_id", 'API', dt_string, "Success")
                user_log.save_to_db()
                ###
                
                return {'msg': 'Successfully Flagged the UserId {}'.format(str(inputdata['user_id']))}
            elif inputdata['user_name']:
                user_inf = UserModel.query.filter_by(username=inputdata['user_name']).first()
                user_inf.isLive = 0
                db.session.commit()
                
                ###REPORTING LOG
                now = datetime.datetime.now()
                dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
                user_log = LogInfo(None, user_inf_log.username, 'flag_user', str(inputdata['user_name']), "*Flaging The User using user_name", 'API', dt_string, "Success")
                user_log.save_to_db()
                ###
                
                return {'msg': 'Successfully Flagged the UserName {}'.format(str(inputdata['user_name']))}
            else:
                ###REPORTING LOG
                now = datetime.datetime.now()
                dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
                user_log = LogInfo(None, user_inf_log.username, 'flag_user', inputdata, "*Flagging The User", 'API', dt_string, "Error: Invalid Parameters!")
                user_log.save_to_db()
                ###
                return {'msg': 'Error: Invalid Parameters!'}

        else:
            ###REPORTING LOG
            now = datetime.datetime.now()
            dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
            user_log = LogInfo(None, user_inf_log.username, 'flag_user', "Not Applicable", "*Flaging The User", 'API', dt_string, "You are not Authorized for This Task!")
            user_log.save_to_db()
            ###
            return {'msg': 'You are not Authorized for This Task!'}
        
        ###REPORTING LOG
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
        user_log = LogInfo(None, user_inf_log.username, 'flag_user', "Not Applicable", "*Flaging The User", 'API', dt_string, "Error: Cound not process the task!")
        user_log.save_to_db()
        ###

        return {'msg': 'Error: Cound not process the task!'}

            
'''
class TokenRefresh(Resource):
    @jwt_required(refresh=True)
    #@jwt_refresh_token_required()
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {'access_token': new_token}, 200

'''

