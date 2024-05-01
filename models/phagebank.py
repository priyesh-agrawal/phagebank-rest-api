from werkzeug.security import generate_password_hash, check_password_hash
from db import db
import datetime


class Role(db.Model):
    __tablename__ = 'Roles'

    idRoles = db.Column(db.Integer, primary_key = True, autoincrement=True)
    descr = db.Column(db.String(45), nullable=False)

class UserModel(db.Model):
    __tablename__ = 'User'

    idUser = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(45))
    password = db.Column(db.String(45))
    fname = db.Column(db.String(45))
    lname = db.Column(db.String(45))
    email_address = db.Column(db.String(45))
    street1 = db.Column(db.String(45))
    street2 = db.Column(db.String(45))
    city = db.Column(db.String(45))
    state = db.Column(db.String(45))
    zip = db.Column(db.String(45))
    phone = db.Column(db.String(45))
    create_dt = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
    isLive = db.Column(db.SmallInteger())
    role_id = db.Column(db.Integer())
    
    #user_to_usertrial =  db.relationship('UserTrial', backref = 'user_tousertrial', lazy = 'dynamic')

    def __init__(self, idUser, username, password, fname, lname, email_address, street1, street2, city, state, zipcode, phone, create_dt, isLive, role_id):
        
        self.idUser = idUser
        self.username = username
        self.password = generate_password_hash(password)
        self.fname = fname
        self.lname = lname
        self.email_address = email_address
        self.street1 = street1
        self.street2 = street2
        self.city = city
        self.state = state
        self.zipcode = zipcode
        self.phone = phone
        self.create_dt = create_dt
        self.isLive = isLive
        self.role_id = role_id

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()


    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(idUser=_id).first()
    
    @classmethod
    def get_all_user(cls):
        return cls.query.fetchall()
    

    @classmethod
    def find_role_by_username(cls, username):
        return db.session.query(cls.username, cls.role_id, Role.idRoles, Role.descr).join(Role, Role.idRoles == cls.role_id).filter(cls.username==username).first()

    @classmethod
    def find_role_by_userid(cls, userid):
        return db.session.query(cls.username, cls.idUser, cls.role_id, Role.idRoles, Role.descr).join(Role, Role.idRoles == cls.role_id).filter(cls.idUser==userid).first()

    @classmethod
    def find_uname_by_email(cls, email):
        return cls.query.filter_by(email_address=email).first()


class Patient(db.Model):
	
    __tablename__ = 'Patient'
    idPatient     = db.Column(db.Integer, primary_key = True, autoincrement = True)
    patient_id    = db.Column(db.String(45), nullable=False)
    patient_wt    = db.Column(db.Float(), nullable=True)
    create_dt     = db.Column(db.DateTime(), nullable=False)
    ulcer_area    = db.Column(db.Float(), nullable=True)
    dosing_target = db.Column(db.String(4), nullable=True)
    patient_attributes = db.Column(db.Text, nullable=True)
    isLive = db.Column(db.SmallInteger())
    #patient_tolot =  db.relationship('LotPatient', backref = db.backref('patient_tolot', lazy=True), lazy = 'dynamic')
    #patient_to_trialpatient =  db.relationship('TrialPatient', backref = 'patient_totrialpatient', lazy = 'dynamic')

    def __init__(self, idPatient, patient_id, create_dt, patient_wt, ulcer_area, dosing_target, patient_attributes, isLive):
        self.idPatient = idPatient
        self.patient_id = patient_id
        self.patient_wt = patient_wt
        self.ulcer_area = ulcer_area
        self.dosing_target = dosing_target
        self.patient_attributes = patient_attributes
        self.create_dt = create_dt
        self.isLive = isLive

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_patient_id(cls, patient_id):
        return db.session.query(cls.idPatient).filter(cls.patient_id == patient_id).first()
    
    @classmethod
    def find_by_idPatient(cls, idPatient):
        return db.session.query(cls.patient_id).filter(cls.idPatient == idPatient).first()

class LotPatient(db.Model):

    __tablename__ = 'Patient_Lot'
    idPatient_Lot = db.Column(db.Integer, primary_key = True, autoincrement = True)
    patient_id    = db.Column(db.Integer, db.ForeignKey('Patient.idPatient'))
    lot_id        = db.Column(db.Integer, db.ForeignKey('Lot.idLot'))
    create_dt     = db.Column(db.DateTime())
    reviewed_by   = db.Column(db.Integer)
    reviewed_dt   = db.Column(db.DateTime())
    #item          = db.relationship('Item', backref = 'members', lazy = 'dynamic')

class Lot(db.Model):

    __tablename__ = 'Lot'

    idLot = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    lot_number = db.Column(db.String(45), nullable=False)
    potency = db.Column(db.BigInteger, nullable=False)
    HCP = db.Column(db.Float(), nullable=True)
    Chloro = db.Column(db.Float(), nullable=True)
    Triton = db.Column(db.Float(), nullable=True)
    endo = db.Column(db.Float(), nullable=False)
    analysis_date = db.Column(db.Date(), nullable=True)
    report_date = db.Column(db.Date(), nullable=True)
    create_dt = db.Column(db.DateTime(), nullable=True, default=datetime.datetime.utcnow)
    pH = db.Column(db.Float(precision=2), nullable=True)
    name = db.Column(db.String(45), nullable=False)
    review_dt = db.Column(db.DateTime(), nullable=True)
    created_by = db.Column(db.Integer, nullable=False)
    reviewed_by = db.Column(db.Integer, nullable=True)
    
    def __init__(self, idLot, lot_number, potency, HCP, Chloro, Triton, endo, analysis_date, report_date, create_dt, pH, name, review_dt, created_by, reviewed_by):
        
        self.idLot = idLot
        self.lot_number = lot_number
        self.potency = potency
        self.HCP = HCP
        self.Chloro = Chloro
        self.Triton = Triton
        self.endo = endo
        self.analysis_date = analysis_date
        self.report_date = report_date
        self.create_dt = create_dt
        self.pH = pH
        self.name = name
        self.review_dt = review_dt
        self.created_by = created_by
        self.reviewed_by = reviewed_by


    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
    #lot_to_patient =  db.relationship('LotPatient', backref = 'lot_topatient',lazy = 'dynamic')
    #lot_to_vial =  db.relationship('Vial', backref = 'lot_tovial',lazy = 'dynamic')


#db.session.query(Patient.patient_id, Vial.serial_number, Lot.lot_number).join(LotPatient, LotPatient.lot_id == Vial.lot_id).join(Patient, LotPatient.patient_id == Patient.idPatient).join(Lot, LotPatient.lot_id == Lot.idLot).filter(Patient.patient_id=='demo-999').order_by(Vial.serial_number).all()

class Vial(db.Model):
    __tablename__ = 'Vials'

    idVials = db.Column(db.Integer, primary_key = True, autoincrement=True)
    serial_number = db.Column(db.String(45), nullable=False)
    create_dt = db.Column(db.DateTime(), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey('Lot.idLot'))
    used = db.Column(db.SmallInteger, nullable=False)
    freezer_barcode_tag = db.Column(db.BigInteger, nullable=False)


class UserTrial(db.Model):
    __tablename__ = 'User_Trials'

    idUser_Trials = db.Column(db.Integer, primary_key = True, autoincrement=True)
    trial_id = db.Column(db.Integer, db.ForeignKey('Trial.idTrials'))
    user_id = db.Column(db.Integer, db.ForeignKey('User.idUser'))       #<-left to map
    islive = db.Column(db.Integer)


class Trial(db.Model):
    __tablename__ = 'Trials'

    idTrials = db.Column(db.Integer, primary_key = True, autoincrement=True)
    name = db.Column(db.String(45), nullable=False)
    descr = db.Column(db.String(45), nullable=False)
    create_dt = db.Column(db.DateTime(), nullable=False)
    isLive = db.Column(db.Integer)
    #trial_to_usertrial =  db.relationship('UserTrial', backref = 'trial_tousertrial', lazy = 'dynamic')
    #trial_to_trialpatient =  db.relationship('TrialPatient', backref = 'trial_to_trialpatient', lazy = 'dynamic')

class TrialPatient(db.Model):
    __tablename__ = 'Trial_Patient'

    idTrial_Patient = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trial_id = db.Column(db.Integer, db.ForeignKey('Trial.idTrial'))
    patient_id = db.Column(db.Integer, db.ForeignKey('Patient.idPatient'))
    isLive = db.Column(db.Integer, nullable=False)

class Randomization(db.Model):
    __tablename__ = 'Randomization'
    idRandomization = db.Column(db.Integer, primary_key=True, autoincrement=True)
    RandomizationNumber =  db.Column(db.String(45))
    Rand_descr =  db.Column(db.String(45))
    Rand_Code =  db.Column(db.String(45))
    patient_id =  db.Column(db.String(45))
    user_id =  db.Column(db.String(45))
    mod_dt = db.Column(db.DateTime(), nullable=False, default=datetime.datetime.utcnow)


class PatientVialUsed(db.Model):
    __tablename__ = 'Patient_Vial_Used'

    idPatientVialUsed = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_number =  db.Column(db.String(255))
    box_number =  db.Column(db.String(255))
    vial_serial_number = db.Column(db.String(255))
    vial_used_dt = db.Column(db.DateTime(), nullable=False)

    def __init__(self, idPatientVialUsed, patient_number, box_number, vial_serial_number, vial_used_dt):
        
        self.idPatientVialUsed = idPatientVialUsed
        self.patient_number =  patient_number
        self.box_number = box_number
        self.vial_serial_number = vial_serial_number
        self.vial_used_dt = vial_used_dt
    
    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

class UserSite(db.Model):
	__tablename__ = 'User_Sites'

	idUser_Sites = db.Column(db.Integer, primary_key=True, autoincrement=True)
	user_id = db.Column(db.Integer, nullable=False)
	site_id = db.Column(db.Integer, nullable=False)
	isLive = db.Column(db.Integer, nullable=False)
	create_dt = db.Column(db.DateTime(), nullable=False)
 
class Site(db.Model):
	__tablename__ = 'Sites'

	idSites = db.Column(db.Integer, primary_key=True, autoincrement=True)
	Descr = db.Column(db.String(255), nullable=False)
	create_dt = db.Column(db.DateTime(), nullable=False)
	site_id = db.Column(db.String(255), nullable=False)
	isLive = db.Column(db.Integer, nullable=False)


class PatientSite(db.Model):
	__tablename__ = 'Patient_Sites'
	idPatient_Sites = db.Column(db.Integer, primary_key=True, autoincrement=True)
	site_id = db.Column(db.Integer, nullable=False)
	patient_id = db.Column(db.Integer, nullable=False)
	isLive = db.Column(db.Integer, nullable=False)
	create_dt = db.Column(db.DateTime(), nullable=False)
	reviewed_by   = db.Column(db.Integer)
	reviewed_date   = db.Column(db.DateTime())