from werkzeug.security import generate_password_hash, check_password_hash
from db import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, reqparse
import json
from models.phagebank import UserModel
from models.database_log import LogInfo



import datetime
now = datetime.datetime.now()
dt_string = now.strftime("%Y/%m/%d %H:%M:%S")

def generate_password():
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for i in range(15))

    return password



_parser = reqparse.RequestParser()
_parser.add_argument('password', type=str,required=True,help="This field cannot be blank.")
_parser.add_argument('fname', type=str, required=True, help="This field cannot be blank.") 
_parser.add_argument('lname', type=str, required=True, help="This field cannot be blank.")
_parser.add_argument('email_address', type=str, required=True, help="This field cannot be blank.")
_parser.add_argument('street1', type=str, required=True, help="This field cannot be blank.")
_parser.add_argument('street2', type=str, help="This field cannot be blank.")
_parser.add_argument('city', type=str, required=True, help="This field cannot be blank.")
_parser.add_argument('state', type=str, required=True, help="This field cannot be blank.")
_parser.add_argument('zip', type=str, required=True, help="This field cannot be blank.")
_parser.add_argument('phone', type=str, required=True, help="This field cannot be blank.")
_parser.add_argument('isLive', type=str, required=True, help="This field cannot be blank.")
_parser.add_argument('role_id', type=str, required=True, help="This field cannot be blank.")


class UserRegister(Resource):
    def post(self):
        data = _parser.parse_args()

        data_11 = data
        data_str = json.dumps(data_11)
        data['username'] = data['email_address']
        
        if UserModel.find_by_username(data['username']):
            ###REPORTING LOG
            user_log = LogInfo(None, data['username'], 'register', data_str, "*Registering New User!", 'API', dt_string, "A user with that username already exists")
            user_log.save_to_db()
            ###        
            return {"message": "A user with that username already exists"}, 400

        user = UserModel(None, data['username'], data['password'], data['fname'], data['lname'], data['email_address'], data['street1'], 
                data['street2'], data['city'], data['state'], data['zip'], data['phone'], None, data['isLive'], data['role_id'])
        
        user.save_to_db()
 
        ###REPORTING LOG
        user_log = LogInfo(None, data['username'], 'register', data_str, "*Registering New User!", 'API', dt_string, "User created successfully.")
        user_log.save_to_db()
        ###        

        return {"message": "User created successfully."}, 201


class UserList(Resource):
    @jwt_required()
    def get(self):
        #user_list = UserModel.get_all_user()
        user_id = get_jwt_identity()
        user_role = UserModel.find_role_by_userid(user_id)
        user_list = db.session.query(UserModel).all()
        
        if user_list:
            ###REPORTING LOG
            user_inf = UserModel.find_by_id(user_id)
            user_log = LogInfo(None, user_inf.username, 'all_users', 'Not Applicable', "select * from User", 'API', dt_string, "Success")
            user_log.save_to_db()
            ###
            user_role_dict = {'1': 'admin', '2': 'superuser', '3': 'manager', '4': 'guest', '5': 'user'}
            if user_role.descr == 'admin':
                #return {'claims': user_id, 'User Role': user_role.descr}
                return {'Users': [{'UserID': user.idUser, 'UserName': user.username, 'email_address': user.email_address,
                    'phone': user.phone, 'Role id': user.role_id, 'Role': user_role_dict[str(user.role_id)]} for user in user_list]}
            else:
                return {'Users': [{'UserID': user.idUser, 'UserName': user.username} for user in user_list]}
        
        
        ###REPORTING LOG
        user_inf = UserModel.find_by_id(user_id)
        user_log = LogInfo(None, user_inf.username, 'all_users', 'Not Applicable', "select * from User", 'API', dt_string, 'Could Not Retrieve Data!')
        user_log.save_to_db()
        ###
        return {'Message': 'Could Not Retrieve Data!'}



