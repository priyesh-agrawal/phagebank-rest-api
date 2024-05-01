import os
from flask_restful import Resource, reqparse
import requests
import json

from db import db
#from flask_jwt import jwt_required
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.phagebank import Role, Patient, LotPatient, Lot, Vial, UserTrial, Trial,  TrialPatient, PatientVialUsed, Randomization, UserSite, Site, PatientSite #add TrialPatient and rename Userinf
from models.phagebank  import UserModel as User

from models.database_log import LogInfo

from resources.PhageBankModule import generate_password 
import datetime

def get_dt_string():
	now = datetime.datetime.now()
	dt_string = now.strftime("%Y/%m/%d %H:%M:%S")

	return dt_string

def get_freezer_location(vial_barcode):
	url = 'https://aphage.freezerpro.com/api'

	fields = {"method": "location_info", "username": "pagrawal@aphage.com", "barcode": vial_barcode, "password": ""}

	response = requests.post(url, data=fields, verify=False)
	json_data = response.json()

	if "location" in json_data:
		freezer_location = json_data["location"]
		freezer_position = json_data["position"]
		#freezer_location_lst = freezer_location.split("&rarr;")
		#freezer_location = freezer_location_lst[0]
		return freezer_location, freezer_position
	else:
		return None, None


def send_email_without_attachment(receiver_address, mail_subject, mail_text):
	import smtplib
	from email.mime.multipart import MIMEMultipart
	from email.mime.text import MIMEText
	from email.mime.base import MIMEBase
	from email import encoders
	
	smtp_port = 587  # For starttls
	smtp_server = "smtp.office365.com"
	#sender_email = "clinical@aphage.com"
	sender_email = "phagebank@aphage.com"
	receiver_email = receiver_address
	#password = "Yellow33Run"
	password = " "

	msg = MIMEMultipart()

	msg['From'] = sender_email
	msg['To'] = receiver_email
	msg['Subject'] = mail_subject

	body = mail_text

	msg.attach(MIMEText(body, 'html'))

	receiver_email_list = receiver_email.split(",")

	#print('receiver_email_list', receiver_email_list)
	try:
		
		server = smtplib.SMTP(smtp_server, smtp_port)
		server.starttls()
		
		server.login(sender_email, password)
		server.sendmail(sender_email, receiver_email_list, msg.as_string())
		
		server.quit()
		
		return {'msg': 'Mail Sent Successfully!'}
	except Exception as Err:
		return{'msg': 'Error: Message could not be sent! {}'.format(str(Err))}


def send_email(receiver_address, mail_subject, mail_text, mail_attachment, mail_attachment_path):
	import smtplib
	from email.mime.multipart import MIMEMultipart
	from email.mime.text import MIMEText
	from email.mime.base import MIMEBase
	from email import encoders
	
	smtp_port = 587  # For starttls
	smtp_server = "smtp.office365.com"
	sender_email = "phagebank@aphage.com"
	receiver_email = receiver_address
	password = " "

	msg = MIMEMultipart()

	msg['From'] = sender_email
	msg['To'] = receiver_email
	msg['Subject'] = mail_subject

	body = mail_text

	# msg.attach(MIMEText(body, 'plain'))
	msg.attach(MIMEText(body, 'html'))

	filename_lst = mail_attachment.split(",")
	for filename in filename_lst:
		filename = filename.strip()
		mail_attachment_path = os.path.join('/var/www/html/phagebankapprestapi/documents/', filename)
		attachment = open(mail_attachment_path, "rb")
		part = MIMEBase('application', 'octet-stream')
		part.set_payload((attachment).read())
		encoders.encode_base64(part)
		part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
		msg.attach(part)
	receiver_email_list = receiver_email.split(",")
	try:
		server = smtplib.SMTP(smtp_server, smtp_port)
		server.starttls()
		server.login(sender_email, password)
		#text = msg.as_string()
		server.sendmail(sender_email, receiver_email_list, msg.as_string())
		server.quit()
		return {'msg': 'Mail Sent Successfully!'}
	except Exception as Err:
		return{'msg': 'Error: Message could not be sent! {}'.format(str(Err))}



_parser = reqparse.RequestParser()

_parser.add_argument('lot_number', type=str, required=True, help="This field cannot be blank!")
_parser.add_argument('potency', type=str, required=True, help="This field cannot be blank!")
_parser.add_argument('HCP', type=str, required=True, help="This field cannot be blank!")
_parser.add_argument('Chloro', type=str, required=False, help="")
_parser.add_argument('Triton', type=str, required=False, help="")
_parser.add_argument('endo', type=str, required=False, help="")
_parser.add_argument('analysis_date', type=str, required=False, help="")
_parser.add_argument('report_date', type=str, required=False, help="")
_parser.add_argument('pH', type=str, required=True, help="This field cannot be blank!")
_parser.add_argument('name', type=str, required=True, help="This field cannot be blank!")
_parser.add_argument('review_dt', type=str, required=False, help="This field cannot be blank!")
_parser.add_argument('reviewed_by', type=str, required=False, help="This field cannot be blank!")



_parser_add_user = reqparse.RequestParser()

_parser_add_user.add_argument('fname', type=str, required=True, help="This field cannot be blank.")
_parser_add_user.add_argument('lname', type=str, required=True, help="This field cannot be blank.")
_parser_add_user.add_argument('email_address', type=str, required=True, help="This field cannot be blank.")
_parser_add_user.add_argument('street1', type=str, required=True, help="This field cannot be blank.")
_parser_add_user.add_argument('street2', type=str, help="This field cannot be blank.")
_parser_add_user.add_argument('city', type=str, required=True, help="This field cannot be blank.")
_parser_add_user.add_argument('state', type=str, required=True, help="This field cannot be blank.")
_parser_add_user.add_argument('zip', type=str, required=True, help="This field cannot be blank.")
_parser_add_user.add_argument('phone', type=str, required=True, help="This field cannot be blank.")
_parser_add_user.add_argument('isLive', type=str, required=True, help="This field cannot be blank.")
_parser_add_user.add_argument('role_id', type=str, required=True, help="This field cannot be blank.")


class PatientToVial(Resource):
	
	@jwt_required()
	def get(self, query_patient_id):
		user_id = get_jwt_identity()
		user_inf = User.find_by_id(user_id)

		items = db.session.query(Patient.patient_id, Vial.serial_number, Lot.lot_number).join(LotPatient, LotPatient.lot_id == Vial.lot_id).join(Patient, LotPatient.patient_id == Patient.idPatient).join(Lot, LotPatient.lot_id == Lot.idLot).filter(Patient.patient_id==query_patient_id).order_by(Vial.serial_number).all()


		
		if items:
			##REPORTING LOG
			user_log = LogInfo(None, user_inf.username, 'get_patient_vial', query_patient_id, "Select Patient.patient_id, Vials.serial_number, Lot.lot_number from Vials join Patient_Lot on Patient_Lot.lot_id=Vials.lot_id join Patient on Patient_Lot.patient_id=Patient.idPatient join Lot on Patient_Lot.lot_id=Lot.idLot where Patient.patient_id = '{}' order by Vials.serial_number;".format(query_patient_id), 'API', get_dt_string(), 'Success!')
			user_log.save_to_db()
			##
			return {'Data': [{'PatientId': item[0], 'SerialNumber':item[1], 'LotNumber': item[2]} for item in items]}
		
		##REPORTING LOG
		user_log = LogInfo(None, user_inf.username, 'get_patient_vial', query_patient_id, "Select Patient.patient_id, Vials.serial_number, Lot.lot_number from Vials join Patient_Lot on Patient_Lot.lot_id=Vials.lot_id join Patient on Patient_Lot.patient_id=Patient.idPatient join Lot on Patient_Lot.lot_id=Lot.idLot where Patient.patient_id = '{}' order by Vials.serial_number;".format(query_patient_id), 'API', 'Nothing Was Found!')
		user_log.save_to_db()
		##
		return {'msg': 'Nothing Was Found!'}

'''
select Patient.patient_id, Lot.lot_number, Lot.potency, Lot.HCP, Lot.Chloro, Lot.Triton, Lot.endo, Lot.analysis_date, Lot.report_date, Lot.pH, Lot.name,
Vials.serial_number from User join User_Trials on User_Trials.user_id = User.idUser join Trials on Trials.idTrials = User_Trials.Trial_id join Trial_Patient
on Trial_Patient.trial_id = Trials.idTrials join Patient on Patient.idPatient = Trial_Patient.patient_id join Patient_Lot on Patient_Lot.patient_id = Patient.idPatient join Lot
on Lot.idLot = Patient_Lot.lot_id join Vials on Vials.lot_id = Lot.idLot where idUser = 1 and Vials.used = 0;
'''


class UserPatientVial(Resource):	   #idUser = 1 and Vials.used = 0;
	
	@jwt_required()
	def get(self, query_user_id):
		#items = db.session.query(Patient.patient_id, Lot.lot_number, Lot.potency, Lot.HCP, Lot.Chloro, Lot.Triton, Lot.endo, Lot.analysis_date, Lot.report_date, Lot.pH, Lot.name, Vial.serial_number).join(UserTrial, UserTrial.user_id == User.idUser).join(Trial, Trial.idTrials == UserTrial.trial_id).join(TrialPatient, TrialPatient.trial_id == Trial.idTrials).join(Patient, Patient.idPatient == TrialPatient.patient_id).join(LotPatient, LotPatient.patient_id == Patient.idPatient).join(Lot, Lot.idLot == LotPatient.lot_id).join(Vial, Vial.lot_id == Lot.idLot).filter(User.idUser==query_user_id).filter(Vial.used == query_vial_used)
		items = db.session.query(Patient.patient_id, Lot.lot_number, Lot.potency, Lot.HCP, Lot.Chloro, Lot.Triton, Lot.endo, Lot.analysis_date, Lot.report_date, Lot.pH, Lot.name, Vial.serial_number).select_from(User).join(UserTrial, UserTrial.user_id == User.idUser).join(Trial, Trial.idTrials == UserTrial.trial_id).join(TrialPatient, TrialPatient.trial_id == Trial.idTrials).join(Patient, Patient.idPatient == TrialPatient.patient_id).join(LotPatient, LotPatient.patient_id == Patient.idPatient).join(Lot, Lot.idLot == LotPatient.lot_id).join(Vial, Vial.lot_id == Lot.idLot).filter(User.idUser== query_user_id)

		user_id = get_jwt_identity()
		user_inf = User.find_by_id(user_id)
		#user_log = LogInfo(None, user_inf.username, 'get_user_patient_vial', query_user_id, "select Patient.patient_id, Lot.lot_number, Lot.potency, Lot.HCP, Lot.Chloro, Lot.Triton, Lot.endo, Lot.analysis_date, Lot.report_date, Lot.pH, Lot.name, Vials.serial_number from User join User_Trials on User_Trials.user_id = User.idUser join Trials on Trials.idTrials = User_Trials.Trial_id join Trial_Patient on Trial_Patient.trial_id = Trials.idTrials join Patient on Patient.idPatient = Trial_Patient.patient_id join Patient_Lot on Patient_Lot.patient_id = Patient.idPatient join Lot on Lot.idLot = Patient_Lot.lot_id join Vials on Vials.lot_id = Lot.idLot where idUser = '{}'".format(query_user_id), 'API', dt_string)
		#user_log.save_to_db()

		if items:
			user_log = LogInfo(None, user_inf.username, 'get_user_patient_vial', query_user_id, "select Patient.patient_id, Lot.lot_number, Lot.potency, Lot.HCP, Lot.Chloro, Lot.Triton, Lot.endo, Lot.analysis_date, Lot.report_date, Lot.pH, Lot.name, Vials.serial_number from User join User_Trials on User_Trials.user_id = User.idUser join Trials on Trials.idTrials = User_Trials.Trial_id join Trial_Patient on Trial_Patient.trial_id = Trials.idTrials join Patient on Patient.idPatient = Trial_Patient.patient_id join Patient_Lot on Patient_Lot.patient_id = Patient.idPatient join Lot on Lot.idLot = Patient_Lot.lot_id join Vials on Vials.lot_id = Lot.idLot where idUser = '{}'".format(query_user_id), 'API', get_dt_string(), 'Success!')
			user_log.save_to_db()
			
			return{'Data' : [{'patient_id': item[0],
							'lot_number' : item[1], 
							'potency': item[2], 
							'HCP' : item[3], 
							'Chloro' : item[4], 
							'Triton' : item[5], 
							'endo' : item[6], 
							'analysis_date' : str(item[7]), 
							'report_date' : str(item[8]), 
							'pH' : item[9], 
							'name' : item[10], 
							'serial_number' : item[11]} for item in items]}

		user_log = LogInfo(None, user_inf.username, 'get_user_patient_vial', query_user_id, "select Patient.patient_id, Lot.lot_number, Lot.potency, Lot.HCP, Lot.Chloro, Lot.Triton, Lot.endo, Lot.analysis_date, Lot.report_date, Lot.pH, Lot.name, Vials.serial_number from User join User_Trials on User_Trials.user_id = User.idUser join Trials on Trials.idTrials = User_Trials.Trial_id join Trial_Patient on Trial_Patient.trial_id = Trials.idTrials join Patient on Patient.idPatient = Trial_Patient.patient_id join Patient_Lot on Patient_Lot.patient_id = Patient.idPatient join Lot on Lot.idLot = Patient_Lot.lot_id join Vials on Vials.lot_id = Lot.idLot where idUser = '{}'".format(query_user_id), 'API', get_dt_string(), 'Nothing Was Found!')
		user_log.save_to_db()
		return {'msg': 'Nothing Was Found!'}



class LotList(Resource):
	@jwt_required()
	def get(self):
		items = db.session.query(Lot.idLot, Lot.lot_number, Lot.potency, Lot.HCP, Lot.Chloro, Lot.Triton, Lot.endo, Lot.analysis_date, Lot.report_date, Lot.create_dt, Lot.pH, Lot.name, Lot.review_dt, Lot.created_by, Lot.reviewed_by).order_by(Lot.idLot).all()


		###REPORTING LOG
		user_id = get_jwt_identity()
		user_inf = User.find_by_id(user_id)
		#user_log = LogInfo(None, user_inf.username, 'all_lot', 'Not Applicable', "select * from Lot order by Lot.idLot ASC", 'API', dt_string)
		#user_log.save_to_db()
		###

		if items:
			user_log = LogInfo(None, user_inf.username, 'all_lot', 'Not Applicable', "select * from Lot order by Lot.idLot ASC", 'API', get_dt_string(), 'success')
			user_log.save_to_db()
			return{'Data': [{'idLot': item[0],
					'lot_number':  item[1],
					'potency': item[2],
					'HCP': item[3],
					'Chloro': item[4],
					'Triton': item[5],
					'endo': item[6],
					'analysis_date': str(item[7]),
					'report_date': str(item[8]),
					'create_dt': str(item[9]),
					'pH': item[10],
					'name': item[11],
					'review_dt': str(item[12]),
					'created_by': item[13],
					'reviewed_by': item[14]} for item in items]}

		user_log = LogInfo(None, user_inf.username, 'all_lot', 'Not Applicable', "select * from Lot order by Lot.idLot ASC", 'API', get_dt_string(), 'Nothing Was Found!')
		user_log.save_to_db()
		return {'msg': 'Nothing Was Found!'}

class AddNewLot(Resource):
	@jwt_required()
	def post(self):
		user_id = get_jwt_identity()
		user_role = User.find_role_by_userid(user_id)
		
		if user_role.descr == "guest":
			return {'msg': 'You are not Authorized for This Task!'}

		inputdata = _parser.parse_args()
		
		inputdata_11 = inputdata
		inputdata_str = json.dumps(inputdata_11)

		inputdata = Lot(None, inputdata['lot_number'], inputdata['potency'], inputdata['HCP'], inputdata['Chloro'], 
				inputdata['Triton'], inputdata['endo'], inputdata['analysis_date'], inputdata['report_date'], get_dt_string(), 
				inputdata['pH'], inputdata['name'], inputdata['review_dt'], user_id, inputdata['reviewed_by'])
		
		try:
			inputdata.save_to_db()
			
			###REPORTING LOG
			user_inf = User.find_by_id(user_id)

			user_log = LogInfo(None, user_inf.username, 'add_lot', inputdata_str, "*Adding New Lot to the DB!", 'API', get_dt_string(), 'Seccessfully added to The Database!')
			user_log.save_to_db()
			###
			
			return {'msg': 'Seccessfully added to The Database!'}
		
		except Exception as Err:
			return {'msg': 'Could not add to Database!'+str(Err)}


class AddNewPatient(Resource):

	parserPatient = reqparse.RequestParser()
	parserPatient.add_argument('patient_id', type=str, required=True, help="This field cannot be blank!")
	parserPatient.add_argument('patient_wt', type=float, required=True, help="This field cannot be blank!")
	parserPatient.add_argument('ulcer_area', type=float, help="Provide information about 'ulcer area' of the Patient!")
	parserPatient.add_argument('dosing_target', type=str, help="Provide information about 'dosing target' of the Patient!")
	parserPatient.add_argument('patient_attributes', type=str, help="Provide information about 'patient_attributes'(JSON) of the Patient!")
	
	@jwt_required()
	def post(self):
		user_id = get_jwt_identity()
		user_role = User.find_role_by_userid(user_id)
		if user_role.descr == "guest":
			return {'msg': 'You are not Authorized for This Task!'}

		inputdata = self.parserPatient.parse_args()
		
		if Patient.find_by_patient_id(inputdata['patient_id']):
			return {"msg": "The Patient Id '{}' is already Present in the DB.".format(inputdata['patient_id'])}, 400
		
		if 'ulcer_area' not in inputdata:
			inputdata['ulcer_area'] = None
		if 'dosing_target' not in inputdata:
			inputdata['dosing_target'] = None
		if 'patient_attributes' not in inputdata:
			inputdata['patient_attributes'] = None
		
		inputdata_11 = inputdata
		inputdata_str = json.dumps(inputdata_11)
		inputdata = Patient(None, inputdata['patient_id'], get_dt_string(), inputdata['patient_wt'], inputdata['ulcer_area'], inputdata['dosing_target'], inputdata['patient_attributes'])

		try:
			inputdata.save_to_db()
		
			###REPORTING LOG
			user_inf = User.find_by_id(user_id)
			user_log = LogInfo(None, user_inf.username, 'add_patient', inputdata_str, "*Adding New Patient to the DB!", 'API', get_dt_string(), 'New Patient seccessfully added to The Database!')
			user_log.save_to_db()
			###
			
			return {'msg': 'New Patient seccessfully added to The Database!'}
		except Exception as Err:
			return {'msg': 'Could not add to Database!'+str(Err)}

class UpdatePatientInfo(Resource):

	parserPatient = reqparse.RequestParser()
	parserPatient.add_argument('idPatient', type=int, required=True, help="This field cannot be blank!")
	parserPatient.add_argument('patient_wt', type=float, help="Patient's Weight in KG!")
	parserPatient.add_argument('ulcer_area', type=float, help="Provide information about 'ulcer area' of the Patient!")
	parserPatient.add_argument('dosing_target', type=str, help="Provide information about 'dosing target' of the Patient!")
	parserPatient.add_argument('patient_attributes', type=str, help="Provide information about 'patient_attributes'(JSON) of the Patient!")

	@jwt_required()
	def post(self):
		inputdata = self.parserPatient.parse_args()
		#print('xx', inputdata)
		inputdata_11 = inputdata
		inputdata_str = json.dumps(inputdata_11)
		
		if Patient.find_by_idPatient(inputdata['idPatient']):
			patient_inf = Patient.query.filter_by(idPatient=inputdata['idPatient']).first()
			
			if 'patient_wt' in inputdata:
				patient_inf.patient_wt = inputdata['patient_wt']
			if 'ulcer_area' in inputdata:
				patient_inf.ulcer_area = inputdata['ulcer_area']
			if 'dosing_target' in inputdata:
				patient_inf.dosing_target = inputdata['dosing_target']
			if 'patient_attributes' in inputdata:
				#patient_inf.patient_attributes = json.dumps(inputdata['patient_attributes'])
				patient_inf.patient_attributes = inputdata['patient_attributes']
			db.session.commit()


			###REPORTING LOG
			user_id = get_jwt_identity()
			user_inf = User.find_by_id(user_id)
			user_log = LogInfo(None, user_inf.username, 'update_patient_info', inputdata_str, "*Update Patient Info(patient_wt|ulcer_area|dosing_target|patient_attributes)", 'API', get_dt_string(), 'Successfully Updated Patient Record!')
			user_log.save_to_db()
			###
			
			return {'msg': 'Successfully Updated Patient Record!'}
		else:
			###REPORTING LOG
			user_id = get_jwt_identity()
			user_inf = User.find_by_id(user_id)
			user_log = LogInfo(None, user_inf.username, 'update_patient_info', inputdata_str, "*Update Patient Info(patient_wt|ulcer_area|dosing_target|patient_attributes)", 'API', get_dt_string(), 'Error! incorrect Patient id')
			user_log.save_to_db()
			###
			return {'msg': 'Error! incorrect database id.'}



class UpdateUsedVial(Resource):
	@jwt_required()
	def get(self, serial_number):
	
		try:
			vial_rows = Vial.query.filter_by(serial_number=serial_number).all()

			for row in vial_rows:
				row.used = 1
			db.session.commit()

			vial_rows_updated = Vial.query.filter_by(serial_number=serial_number).all()
			
			###REPORTING LOG
			user_id = get_jwt_identity()
			user_inf = User.find_by_id(user_id)
			user_log = LogInfo(None, user_inf.username, 'update_used_vial', serial_number, "*Update Vials set used=1 where serial_number='{}'".format(serial_number), 'API', get_dt_string(), 'Successfully Updated!')
			user_log.save_to_db()
			###
		
			return {'msg': 'Successfully Updated!'}
		except:
			###REPORTING LOG
			user_id = get_jwt_identity()
			user_inf = User.find_by_id(user_id)
			user_log = LogInfo(None, user_inf.username, 'update_used_vial', serial_number, "*Update Vials set used=1 where serial_number='{}'".format(serial_number), 'API', get_dt_string(), 'Error! Could not update the Table!')
			user_log.save_to_db()
			###
			return {'msg': 'Error! Could not update the Table.'}


class UpdateUNUsedVial(Resource):
	@jwt_required()
	def get(self, serial_number):
	
		try:
			vial_rows = Vial.query.filter_by(serial_number=serial_number).all()

			for row in vial_rows:
				row.used = 0
			db.session.commit()

			vial_rows_updated = Vial.query.filter_by(serial_number=serial_number).all()
			
			###REPORTING LOG
			user_id = get_jwt_identity()
			user_inf = User.find_by_id(user_id)
			user_log = LogInfo(None, user_inf.username, 'update_vial_to_unused', serial_number, "*Update Vials set used=0 where serial_number='{}'".format(serial_number), 'API', get_dt_string(), 'Successfully Updated!')
			user_log.save_to_db()
			###
		
			return {'msg': 'Successfully Updated!'}
		except:
			###REPORTING LOG
			user_id = get_jwt_identity()
			user_inf = User.find_by_id(user_id)
			user_log = LogInfo(None, user_inf.username, 'update_vial_to_unused', serial_number, "*Update Vials set used=0 where serial_number='{}'".format(serial_number), 'API', get_dt_string(), 'Error! Could not update the Table!')
			user_log.save_to_db()
			###
			return {'msg': 'Error! Could not update the Table.'}



class TrialForPatient(Resource):
	@jwt_required()
	def get(self, query_patient_id):
		items = db.session.query(Trial.idTrials,  Trial.name).select_from(Trial).join(TrialPatient, TrialPatient.trial_id == Trial.idTrials).join(Patient, Patient.idPatient == TrialPatient.patient_id).filter(Patient.idPatient == query_patient_id)

		###REPORTING LOG
		#user_id = get_jwt_identity()
		#user_inf = User.find_by_id(user_id)
		#user_log = LogInfo(None, user_inf.username, 'trial_for_patient', query_patient_id, "Select Trials.idTrials, Trials.name, join Trial_Patient on Trial_Patient.trial_id = Trials.idTrials join Patient on Patient.idPatient=Trial_Patient.patient_id where Patient.idPatient='{}'".format(str(query_patient_id)), 'API', dt_string)
		#user_log.save_to_db()
		###
		
		if items:
			###REPORTING LOG
			user_id = get_jwt_identity()
			user_inf = User.find_by_id(user_id)
			user_log = LogInfo(None, user_inf.username, 'trial_for_patient', query_patient_id, "Select Trials.idTrials, Trials.name, join Trial_Patient on Trial_Patient.trial_id = Trials.idTrials join Patient on Patient.idPatient=Trial_Patient.patient_id where Patient.idPatient='{}'".format(str(query_patient_id)), 'API', get_dt_string(), 'Success!')
			user_log.save_to_db()
			###
			return {'Data': [{'idTrials': item[0], 'Name':item[1]} for item in items]}
		
		###REPORTING LOG
		user_id = get_jwt_identity()
		user_inf = User.find_by_id(user_id)
		user_log = LogInfo(None, user_inf.username, 'trial_for_patient', query_patient_id, "Select Trials.idTrials, Trials.name, join Trial_Patient on Trial_Patient.trial_id = Trials.idTrials join Patient on Patient.idPatient=Trial_Patient.patient_id where Patient.idPatient='{}'".format(str(query_patient_id)), 'API', get_dt_string(), 'Nothing Can be Retrieved!')
		user_log.save_to_db()
		###
		return {'msg': 'Nothing Can be Retrieved!'}

'''
Select Vials.serial_number from Vials
join Lot
on Vials.lot_id = Lot.idLot
join Patient_Lot
on Patient_Lot.lot_id = Lot.idLot
join Trial_Patient
on Patient_Lot.patient_id = Trial_Patient.patient_id
where Patient_Lot.patient_id = 1 and Trial_Patient.trial_id = 1 and Vials.freezer_barcode_tag = 12012899;
'''
class VialForPatient(Resource):
	@jwt_required()
	def get(self, query_patient_id, query_freezer_barcode):
		items = db.session.query(Vial.serial_number).select_from(Patient).join(LotPatient, LotPatient.patient_id == Patient.idPatient).join(Lot, Lot.idLot == LotPatient.lot_id).join(Vial, Vial.lot_id == Lot.idLot).filter(Patient.idPatient == query_patient_id).filter(Vial.used == 0).filter(Vial.freezer_barcode_tag == query_freezer_barcode)

		if items:
			###REPORTING LOG
			user_id = get_jwt_identity()
			user_inf = User.find_by_id(user_id)
			user_log = LogInfo(None, user_inf.username, 'vial_for_patient', '{},{}'.format(str(query_patient_id), query_freezer_barcode), "Select Vials.serial_number from Patient join Patient_Lot on Patient_Lot.patient_id=Patient.idPatient join Lot on Lot.idLot = Patient_Lot.lot_id join Vials on Vials.lot_id = Lot.idLot where Patient.idPatient='{}' and Vial.used=0 and Vial.freezer_barcode_tag='{}'".format(str(query_patient_id), query_freezer_barcode), 'API', get_dt_string(), 'Success')
			user_log.save_to_db()
		###
			return {'Data': [{'serial_number': item[0]} for item in items]}

		###REPORTING LOG
		user_id = get_jwt_identity()
		user_inf = User.find_by_id(user_id)
		user_log = LogInfo(None, user_inf.username, 'vial_for_patient', '{},{}'.format(str(query_patient_id), query_freezer_barcode), "Select Vials.serial_number from Patient join Patient_Lot on Patient_Lot.patient_id=Patient.idPatient join Lot on Lot.idLot = Patient_Lot.lot_id join Vials on Vials.lot_id = Lot.idLot where Patient.idPatient='{}' and Vial.used=0 and Vial.freezer_barcode_tag='{}'".format(str(query_patient_id), query_freezer_barcode), 'API', get_dt_string(), 'Nothing Can be Retrieved!')
		user_log.save_to_db()
		###
		
		return {'msg': 'Nothing Can be Retrieved!'}

'''
select Patient.idPatient, Patient.patient_id, Patient.patient_wt, Patient.ulcer_area, Patient.dosing_target, 
Patient.patient_attributes, Sites.Descr, Trials.descr from Patient
join Patient_Sites on Patient.idPatient = Patient_Sites.patient_id
join Sites on Patient_Sites.site_id = Sites.idSites
join User_Sites on User_Sites.site_id = Patient_Sites.site_id
join User on User.idUser = User_Sites.user_id
join Trial_Patient on Trial_Patient.patient_id = Patient.idPatient
join Trials on Trial_Patient.trial_id = Trials.idTrials
join User_Trials on User_Trials.user_id = User.idUser
where User.idUser = 6 
and User.isLive = 1
and Patient.isLive = 1
and User_Trials.isLive = 1;
'''

class PatientsForUserDev(Resource):
	@jwt_required()
	def get(self):
		logdin_userid = get_jwt_identity()
		#items = db.session.query(Patient.idPatient, Patient.patient_id, Patient.patient_wt, Patient.ulcer_area, Patient.dosing_target, Patient.patient_attributes, Trial.idTrials, Trial.name, Site.Descr, Site.site_id).select_from(User).join(UserTrial, UserTrial.user_id == User.idUser).join(Trial, Trial.idTrials == UserTrial.trial_id).join(TrialPatient, TrialPatient.trial_id == Trial.idTrials).join(Patient, Patient.idPatient == TrialPatient.patient_id).join(UserSite, UserSite.user_id == User.idUser).join(Site, Site.idSites == UserSite.site_id).filter(User.idUser == logdin_userid).join(PatientSite,  PatientSite.site_id == UserSite.site_id).filter(UserTrial.islive == 1).filter(Patient.isLive == 1).filter(UserSite.isLive == 1).filter(PatientSite.isLive == 1)
		items = db.session.query(Patient.idPatient, Patient.patient_id, Patient.patient_wt, Patient.ulcer_area, Patient.dosing_target, 
		Patient.patient_attributes, Trial.idTrials, Trial.name, Site.Descr, Trial.descr).select_from(Patient).join(PatientSite, Patient.idPatient == PatientSite.patient_id).join(Site, 
        PatientSite.site_id == Site.idSites).join(UserSite, UserSite.site_id == PatientSite.site_id).join(User, User.idUser == UserSite.user_id).join(TrialPatient, 
        TrialPatient.patient_id == Patient.idPatient).join(Trial, TrialPatient.trial_id == Trial.idTrials).join(UserTrial, UserTrial.user_id == User.idUser).filter(User.idUser == logdin_userid).filter(User.isLive == 1).filter(Patient.isLive == 1).filter(UserTrial.islive == 1).filter(TrialPatient.isLive == 1).filter(PatientSite.isLive == 1).filter(Trial.isLive == 1).filter(UserSite.isLive == 1)
		###REPORTING LOG
		#user_inf = User.find_by_id(logdin_userid)
		#user_log = LogInfo(None, user_inf.username, 'get_user_patient', logdin_userid, "Select Patient.idPatient, Patient.patient_id, Patient.patient_wt, Trials.idTrials, Trials.name from User join User_Trials on User_Trials.user_id=User.idUser join Trials on Trials.idTrials=User_trials.trial_id join Trial_Patient on Trial_Patient.trial_id=Trials.idTrials join Patient on Patient.idPatient=Trial_Patient.patient_id where User.idUser='{}')".format(str(logdin_userid)), 'API', dt_string)
		#user_log.save_to_db()
		###
		
		if items:
			###REPORTING LOG
			user_inf = User.find_by_id(logdin_userid)
			user_log = LogInfo(None, user_inf.username, 'get_user_patient', logdin_userid, "Select Patient.idPatient, Patient.patient_id, Patient.patient_wt, Trials.idTrials, Trials.name from User join User_Trials on User_Trials.user_id=User.idUser join Trials on Trials.idTrials=User_trials.trial_id join Trial_Patient on Trial_Patient.trial_id=Trials.idTrials join Patient on Patient.idPatient=Trial_Patient.patient_id where User.idUser='{}')".format(str(logdin_userid)), 'API', get_dt_string(), 'Success')
			user_log.save_to_db()
			###
			out_data_dict_list = []
			for item in items:
				if item[5] is None:
					out_data_dict_list.append({'idPatient': item[0], 'patient_id': item[1], 'patient_wt': item[2], 'ulcer_area': item[3], 'dosing_target': item[4], 'patient_attributes': None, 'idTrials': item[6], 'TrialName': item[7]})
				else:
					patient_attributes = item[5]
					patient_attributes = patient_attributes.replace("\'", "\"")
					#patient_attributes = patient_attributes.replace("^\"", "\'")
					#print('patient_attributes', patient_attributes)
					json_patient_attrib = json.loads(patient_attributes)
					out_data_dict_list.append({'idPatient': item[0], 'patient_id': item[1], 'patient_wt': item[2], 'ulcer_area': item[3], 'dosing_target': item[4], 'patient_attributes': json_patient_attrib, 'idTrials': item[6], 'TrialName': item[7]})
			
			return {'Data': out_data_dict_list}

			
			#return {'Data': [{'idPatient': item[0], 'patient_id': item[1], 'patient_wt': item[2], 'ulcer_area': item[3], 'dosing_target': item[4], 'patient_attributes': json.loads(item[5]), 'idTrials': item[6], 'TrialName': item[7]} for item in items]}
		###REPORTING LOG
		user_inf = User.find_by_id(logdin_userid)
		user_log = LogInfo(None, user_inf.username, 'get_user_patient', logdin_userid, "Select Patient.idPatient, Patient.patient_id, Patient.patient_wt, Trials.idTrials, Trials.name from User join User_Trials on User_Trials.user_id=User.idUser join Trials on Trials.idTrials=User_trials.trial_id join Trial_Patient on Trial_Patient.trial_id=Trials.idTrials join Patient on Patient.idPatient=Trial_Patient.patient_id where User.idUser='{}')".format(str(logdin_userid)), 'API', get_dt_string(), 'No Information was Found!')
		user_log.save_to_db()
		###
		
		return {'msg': 'No Information was Found!'}

class PatientsForUser(Resource):
	@jwt_required()
	def get(self):
		logdin_userid = get_jwt_identity()
		items = db.session.query(Patient.idPatient, Patient.patient_id, Patient.patient_wt, Patient.ulcer_area, Patient.dosing_target, Patient.patient_attributes, Trial.idTrials, Trial.name).select_from(User).join(UserTrial, UserTrial.user_id == User.idUser).join(Trial, Trial.idTrials == UserTrial.trial_id).join(TrialPatient, TrialPatient.trial_id == Trial.idTrials).join(Patient, Patient.idPatient == TrialPatient.patient_id).filter(User.idUser == logdin_userid).filter(UserTrial.islive == 1).filter(Patient.isLive == 1).filter(TrialPatient.isLive == 1)

		###REPORTING LOG
		#user_inf = User.find_by_id(logdin_userid)
		#user_log = LogInfo(None, user_inf.username, 'get_user_patient', logdin_userid, "Select Patient.idPatient, Patient.patient_id, Patient.patient_wt, Trials.idTrials, Trials.name from User join User_Trials on User_Trials.user_id=User.idUser join Trials on Trials.idTrials=User_trials.trial_id join Trial_Patient on Trial_Patient.trial_id=Trials.idTrials join Patient on Patient.idPatient=Trial_Patient.patient_id where User.idUser='{}')".format(str(logdin_userid)), 'API', dt_string)
		#user_log.save_to_db()
		###
		
		if items:
			###REPORTING LOG
			user_inf = User.find_by_id(logdin_userid)
			user_log = LogInfo(None, user_inf.username, 'get_user_patient', logdin_userid, "Select Patient.idPatient, Patient.patient_id, Patient.patient_wt, Trials.idTrials, Trials.name from User join User_Trials on User_Trials.user_id=User.idUser join Trials on Trials.idTrials=User_trials.trial_id join Trial_Patient on Trial_Patient.trial_id=Trials.idTrials join Patient on Patient.idPatient=Trial_Patient.patient_id where User.idUser='{}')".format(str(logdin_userid)), 'API', get_dt_string(), 'Success')
			user_log.save_to_db()
			###
			out_data_dict_list = []
			for item in items:
				if item[5] is None:
					out_data_dict_list.append({'idPatient': item[0], 'patient_id': item[1], 'patient_wt': item[2], 'ulcer_area': item[3], 'dosing_target': item[4], 'patient_attributes': None, 'idTrials': item[6], 'TrialName': item[7]})
				else:
					patient_attributes = item[5]
					patient_attributes = patient_attributes.replace("\'", "\"")
					#patient_attributes = patient_attributes.replace("^\"", "\'")
					#print('patient_attributes', patient_attributes)
					json_patient_attrib = json.loads(patient_attributes)
					out_data_dict_list.append({'idPatient': item[0], 'patient_id': item[1], 'patient_wt': item[2], 'ulcer_area': item[3], 'dosing_target': item[4], 'patient_attributes': json_patient_attrib, 'idTrials': item[6], 'TrialName': item[7]})
			
			return {'Data': out_data_dict_list}

			
			#return {'Data': [{'idPatient': item[0], 'patient_id': item[1], 'patient_wt': item[2], 'ulcer_area': item[3], 'dosing_target': item[4], 'patient_attributes': json.loads(item[5]), 'idTrials': item[6], 'TrialName': item[7]} for item in items]}
		###REPORTING LOG
		user_inf = User.find_by_id(logdin_userid)
		user_log = LogInfo(None, user_inf.username, 'get_user_patient', logdin_userid, "Select Patient.idPatient, Patient.patient_id, Patient.patient_wt, Trials.idTrials, Trials.name from User join User_Trials on User_Trials.user_id=User.idUser join Trials on Trials.idTrials=User_trials.trial_id join Trial_Patient on Trial_Patient.trial_id=Trials.idTrials join Patient on Patient.idPatient=Trial_Patient.patient_id where User.idUser='{}')".format(str(logdin_userid)), 'API', get_dt_string(), 'No Information was Found!')
		user_log.save_to_db()
		###
		
		return {'msg': 'No Information was Found!'}



class GetLotFromPatientIDTrialID(Resource):
	@jwt_required()
	def get(self, query_patient_id, query_trial_id):
		items = db.session.query(Lot.idLot, Lot.lot_number, Lot.potency, Lot.HCP, Lot.Chloro, Lot.Triton, Lot.endo, Lot.analysis_date, Lot.report_date, Lot.pH, Lot.name, Lot.review_dt, Lot.created_by, Lot.reviewed_by).select_from(Lot).join(LotPatient, LotPatient.lot_id == Lot.idLot).join(TrialPatient, TrialPatient.patient_id == LotPatient.patient_id).filter(LotPatient.patient_id == query_patient_id).filter(TrialPatient.trial_id == query_trial_id).filter(Lot.reviewed_by != None).filter(LotPatient.reviewed_by != None)

		if items:
			###REPORTING LOG
			user_id = get_jwt_identity()
			user_inf = User.find_by_id(user_id)
			user_log = LogInfo(None, user_inf.username, 'get_lot_for_patient_trial', '{}, {}'.format(str(query_patient_id), str(query_trial_id)), "select * from Lot join Patient_Lot on Patient_Lot.lot_id = Lot.idLot join Trial_Patient on Trial_Patient.patient_id= Patient_Lot.patient_id where Patient_Lot.patient_id='{}' and Trial_Patient.trial_id='{}' and Lot.reviewed_by is not Null and Patient_Lot.reviewed_by is not Null".format(str(query_patient_id), str(query_trial_id)), 'API', get_dt_string(), 'Success')
			user_log.save_to_db()
			###
			return {'Data': [{'idLot' : item[0], 'lot_number' : item[1], 'potency' : item[2], 'HCP' : item[3], 'Chloro' : item[4], 'Triton' : item[5], 'endo' : item[6], 'analysis_date' : str(item[7]), 'report_date' : str(item[8]), 'pH' : item[9], 'name' : item[10], 'review_dt': str(item[11]), 'created_by': str(item[12]), 'reviewed_by': item[13]} for item in items]}
		
		
		###REPORTING LOG
		user_id = get_jwt_identity()
		user_inf = User.find_by_id(user_id)
		user_log = LogInfo(None, user_inf.username, 'get_lot_for_patient_trial', '{}, {}'.format(str(query_patient_id), str(query_trial_id)), "select * from Lot join Patient_Lot on Patient_Lot.lot_id = Lot.idLot join Trial_Patient on Trial_Patient.patient_id= Patient_Lot.patient_id where Patient_Lot.patient_id='{}' and Trial_Patient.trial_id='{}' and Lot.reviewed_by is not Null and Patient_Lot.reviewed_by is not Null".format(str(query_patient_id), str(query_trial_id)), 'API', get_dt_string(), 'No Information was Found!')
		user_log.save_to_db()
		###

		return {'msg': 'No Information was Found!'}


class GetVialFromLotIdandFreezerId(Resource):
	@jwt_required()
	def get(self, query_lot_id, query_freezer_id):
		items = db.session.query(Vial.idVials, Vial.serial_number, Vial.create_dt, Vial.lot_id, Vial.used, Vial.freezer_barcode_tag).select_from(Vial).filter(Vial.lot_id == query_lot_id).filter(Vial.freezer_barcode_tag == query_freezer_id).filter(Vial.used == 0)
		
		
		if items:
			###REPORTING LOG
			user_id = get_jwt_identity()
			user_inf = User.find_by_id(user_id)
			user_log = LogInfo(None, user_inf.username, 'get_vial_for_lot_freezer', '{}, {}'.format(str(query_lot_id), str(query_freezer_id)), "select * from Vials where Vials.lot_id='{}' and Vials.freezer_barcode_tag='{}' and Vials.used=0".format(str(query_lot_id), str(query_freezer_id)), 'API', get_dt_string(), 'Success')
			user_log.save_to_db()
			###
			return{'Data': [{'idVials' : item[0], 'serial_number' : item[1], 'create_dt' : str(item[2]), 'lot_id' : item[3], 'used' : item[4], 'freezer_barcode_tag' : item[5]} for item in items]}
		
		###REPORTING LOG
		user_id = get_jwt_identity()
		user_inf = User.find_by_id(user_id)
		user_log = LogInfo(None, user_inf.username, 'get_vial_for_lot_freezer', '{}, {}'.format(str(query_lot_id), str(query_freezer_id)), "select * from Vials where Vials.lot_id='{}' and Vials.freezer_barcode_tag='{}' and Vials.used=0".format(str(query_lot_id), str(query_freezer_id)), 'API', get_dt_string(), 'No Information was Found!')
		user_log.save_to_db()
		###
		return {'msg': 'No Information was Found!'}

class GetFreezerLocationFromVial(Resource):
	@jwt_required()
	def get(self, vial_serial_number):

		freezer_location, freezer_position = get_freezer_location(vial_serial_number)
		
		###REPORTING LOG
		user_id = get_jwt_identity()
		user_inf = User.find_by_id(user_id)
		user_log = LogInfo(None, user_inf.username, 'get_freezer_location', str(vial_serial_number), "*Executing FreezerPro API 'location_info' with parameter '{}'!".format(str(vial_serial_number)), 'API', get_dt_string(), 'Success')
		user_log.save_to_db()
		###

		return {'location': freezer_location, 'position': freezer_position}


class UpdateFreezerProForUsedSample(Resource):

	@jwt_required()
	def get(self, vial_serial_number):
		url = 'https://aphage.freezerpro.com/api'

		fields = {"method": "take_samples_out", "username": "pagrawal@aphage.com", "json":"{\"tags\":[\""+vial_serial_number+"\"],\"type\":\"barcode_tags\"}", "password": "APT123!"}

		response = requests.post(url, data=fields, verify=False)
		json_data = response.json()

	#freezer_location = freezer_location_lst[0]
		
		###REPORTING LOG
		user_id = get_jwt_identity()
		user_inf = User.find_by_id(user_id)
		user_log = LogInfo(None, user_inf.username, 'update_freezer_pro_for_used_vial', str(vial_serial_number), "*Executing FreezerPro API 'take_samples_out' with parameter '{}'!".format(str(vial_serial_number)), 'API', get_dt_string(), 'Success')
		user_log.save_to_db()
		###
		
		return json_data


class SendMailFromClinical(Resource):

	parserMail = reqparse.RequestParser()
	parserMail.add_argument('receiver_address', type=str, required=True, help="Provide Receiver's Email")
	parserMail.add_argument('subject', type=str, required=True, help="Subject of Mail")
	parserMail.add_argument('body', type=str, required=True, help="Body of Mail")
	parserMail.add_argument('attachment', type=str, required=False, help="name of attached pdf")

	@jwt_required()
	def post(self):
		inputdata = self.parserMail.parse_args()
		
		if User.find_uname_by_email(inputdata['receiver_address']):
			user_inf = User.find_uname_by_email(inputdata['receiver_address'])
			mail_text = 'Dear {} {},\n{}\n\n'.format(user_inf.fname, user_inf.lname ,inputdata['body'])
		else:
			username = inputdata['receiver_address'].split('@')[0]
			mail_text = 'Dear {},\n{}\n\n'.format(username ,inputdata['body'])
		if inputdata['attachment']:
			#mail_attachment_path = os.path.join('/var/www/html/phagebankapprestapi/documents/', inputdata['attachment'])
			mail_attachment_path = '/var/www/html/phagebankapprestapi/documents/'

			feedback = send_email(inputdata['receiver_address'], inputdata['subject'], mail_text, inputdata['attachment'], mail_attachment_path)
		else:
			feedback = send_email_without_attachment(inputdata['receiver_address'], inputdata['subject'], mail_text)

		###REPORTING LOG
		user_id = get_jwt_identity()
		user_inf = User.find_by_id(user_id)
		user_log = LogInfo(None, user_inf.username, 'send_mail', '{}, {}'.format(inputdata['receiver_address'], inputdata['subject']), "*Executing 'send_mail' API", 'API', get_dt_string(), 'Success')
		user_log.save_to_db()
		###
		
		return feedback


class UpdateVialForPatient(Resource):
	
	parserPatientVialUsed = reqparse.RequestParser()
	parserPatientVialUsed.add_argument('patient_id', type=str, help="Patient's ID!")
	parserPatientVialUsed.add_argument('box_number', type=str, help="Box Number")
	parserPatientVialUsed.add_argument('vial_serial_number', type=str, help="Vial Serial Number!")

	@jwt_required()
	def post(self):
		
		user_id = get_jwt_identity()
		user_inf = User.find_by_id(user_id)
		
		inputdata = self.parserPatientVialUsed.parse_args()

		inputdata_11 = inputdata
		inputdata_str = json.dumps(inputdata_11)
		
		if Patient.find_by_patient_id(inputdata['patient_id']):
			
			if inputdata['patient_id'] and inputdata['box_number'] and inputdata['vial_serial_number']:

				data_to_save_to_db = PatientVialUsed(None, inputdata['patient_id'], inputdata['box_number'], inputdata['vial_serial_number'], get_dt_string()) 
		
				try:
					data_to_save_to_db.save_to_db()
			
					user_log = LogInfo(None, user_inf.username, 'update_vial_for_patient', inputdata_str, "*Updating Used Vial for Patient", 'API', get_dt_string(), 'Seccess!')
					user_log.save_to_db()
			
					return {'msg': 'Seccessfully added to The Database!'}
		
				except Exception as Err:
			
			
					user_log = LogInfo(None, user_inf.username, 'update_vial_for_patient', inputdata_str, "*Updating Used Vial for Patient", 'API', get_dt_string(), 'Failed! '+str(Err))
					user_log.save_to_db()

					return {'msg': 'Could not add to Database!'+str(Err)}
			else:
				
				user_log = LogInfo(None, user_inf.username, 'update_vial_for_patient', inputdata_str, "*Updating Used Vial for Patient", 'API', get_dt_string(), 'Failed! Incorrect Parameters Provided!!')
				user_log.save_to_db()

				return {'msg': 'Please provide all the parameters!'}
		else:

			user_log = LogInfo(None, user_inf.username, 'update_vial_for_patient', inputdata_str, "*Updating Used Vial for Patient", 'API', get_dt_string(), "Failed! Patient Id '{}' not found!!".format(str(inputdata['patient_id'])))
			user_log.save_to_db()

			return {'msg': "Failed! Patient Id '{}' not found!!".format(str(inputdata['patient_id']))}


class AddNewUser(Resource):
	@jwt_required()
	def post(self):
		data = _parser_add_user.parse_args()

		data_11 = data
		data_str = json.dumps(data_11)
		
		logdin_user_id  = get_jwt_identity()
		logdin_user_inf =  User.find_role_by_userid(logdin_user_id)

		if int(logdin_user_inf.role_id) != 1:

			return {"message": "Error: You Don't have Enough Privelage For this Task!"}
			user_log = LogInfo(None, data['email_address'], 'add_new_user', data_str, "*Adding New User!", 'API', get_dt_string(), "Not Enough Privelage to perform the task!")

		if User.find_by_username(data['email_address']):
			###REPORTING LOG
			user_log = LogInfo(None, data['email_address'], 'add_new_user', data_str, "*Adding New User!", 'API', get_dt_string(), "A user with that username already exists")
			user_log.save_to_db()
			###
			return {"message": "Error: A user with that username already exists"}, 400

		try:
			user_password  = generate_password()
			user = User(None, data['email_address'], user_password, data['fname'], data['lname'], data['email_address'], data['street1'],
				data['street2'], data['city'], data['state'], data['zip'], data['phone'], None, data['isLive'], data['role_id'])

			user.save_to_db()

			mail_subject = "Welcome To PhageBank App {}!".format(data['fname'])
			mail_text = "\
					<html>\
					<head>\
					</head>\
					<body>\
					<p>Dear {} {},<br><br>\
					You have been registered to use PhageBank App. Here are your login credentials.<br><br>\
					<b>Username : {}</b><br>\
					<b>Password : {}</b><br><br>\
					Please Do not Share Your credentials with anyone else!\
					</p>\
					</body>\
					</html>".format(data['fname'], data['lname'], data['email_address'], user_password)
			feedback = send_email_without_attachment(data['email_address'], mail_subject, mail_text)
			
			user_log = LogInfo(None, data['email_address'], 'add_new_user', data_str, "*Adding New User!", 'API', get_dt_string(), "User Added successfully.")
			user_log.save_to_db()
		except Exception as Err:
			
			user_log = LogInfo(None, data['email_address'], 'add_new_user', data_str, "*Adding New User", 'API', gte_dt_string(), "Task Failed! {}".format(str(Err)))
			user_log.save_to_db()
			return {"message": "Error: {}".format(str(Err))}, 400

		return {"message": "User created successfully."}, 201


#'/get_randomization_info/<string:patient_id>/<string:user_id>/<string:randnumber>'
class GetRandomizationInfo(Resource):
	@jwt_required()
	def get(self, patientid, userid, randnumber):
		item = db.session.query(Randomization.Rand_Code, Randomization.Rand_descr).filter(Randomization.patient_id==patientid).filter(Randomization.user_id==userid).filter(Randomization.RandomizationNumber==randnumber).first()

		if item:
			###REPORTING LOG
			user_id = get_jwt_identity()
			user_inf = User.find_by_id(user_id)
			user_log = LogInfo(None, user_inf.username, 'get_randomization_info', '{}, {}, {}'.format(patientid, userid, randnumber), "Retrieves information from Randomization Table", 'API', get_dt_string(), 'Success')
			user_log.save_to_db()
			###
			return {'Rand_Code' : item[0], 'Rand_descr' : item[1]}
		
		
		###REPORTING LOG
		user_id = get_jwt_identity()
		user_inf = User.find_by_id(user_id)
		user_log = LogInfo(None, user_inf.username, 'get_randomization_info', '{}, {}, {}'.format(patientid, userid, randnumber), "Retrieves information from Randomization Table", 'API', get_dt_string(), 'Success')
		user_log.save_to_db()
		###

		return {'msg': 'No Information was Found!'}