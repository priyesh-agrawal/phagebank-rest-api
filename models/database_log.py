from db import db
import datetime

'''
create table Log_Info(
   idLog INT NOT NULL AUTO_INCREMENT,
   username VARCHAR(40) NOT NULL,
   end_point VARCHAR(100) NOT NULL,
   parameters VARCHAR(150) NOT NULL,
   mysql_query VARCHAR(256) NOT NULL,
   executed_from CHAR(3) NOT NULL,
   execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   PRIMARY KEY ( idLog )
);
'''
class LogInfo(db.Model):
    __tablename__ = 'Log_Info'

    idLog = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(40))
    end_point = db.Column(db.String(100))
    parameters = db.Column(db.String(150))
    mysql_query = db.Column(db.String(256))
    executed_from = db.Column(db.String(3))
    execution_time = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
    feedback_message = db.Column(db.Text)
    
    #user_to_usertrial =  db.relationship('UserTrial', backref = 'user_tousertrial', lazy = 'dynamic')

    def __init__(self, idLog, username, end_point, parameters, mysql_query, executed_from, execution_time, feedback_message):
        
        self.idLog = idLog
        self.username = username
        self.end_point = end_point
        self.parameters = parameters
        self.mysql_query = mysql_query
        self.executed_from = executed_from
        self.execution_time = execution_time
        self.feedback_message = feedback_message
    
    def save_to_db(self):
        if self.username != 'fred':
            db.session.add(self)
            db.session.commit()
