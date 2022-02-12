from flask import Flask,request, jsonify, make_response
import gunicorn
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table, Enum
from sqlalchemy.types import TEXT
import os
from flask_cors import CORS
from MySQLdb import _mysql
import uuid
app = Flask(__name__)
connstr =  "mysql://etlfzuiqep3x9epw:rm0aadwhwg8876si@z3iruaadbwo0iyfp.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/bvfo3h955t68zhoz"
app.config['SQLALCHEMY_DATABASE_URI'] = connstr
db = SQLAlchemy(app)
CORS(app, resources={r"/*": {"origins": "*"}})

engine = create_engine(connstr)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]= True
app.config['UPLOAD_FOLDER'] = '/static'

meta = MetaData()   
meta.bind= engine

class Running(db.Model):
    uuid = db.Column(db.String(255), primary_key=True, nullable=False)
    email = db.Column(db.String(255), db.ForeignKey('users.email'), nullable=False)
    project = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    results = db.relationship('Results', backref="running")

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}
class Projects(db.Model):
    id= db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(255))
    tests = db.relationship("TestRunner", backref="projects")
    course = db.Column(db.String(255))
    section = db.Column(db.String(255))
    lastupdated = db.Column(db.DATETIME)
    prof = db.Column(db.String(255))
    runs = db.relationship("Running", backref="projects")
    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class TestRunner(db.Model):
    pid = db.Column(db.Integer,nullable=False, primary_key=True)
    ratings = db.Column(db.Integer)
    author = db.Column(db.String(255), nullable = False)
    name  = db.Column(db.String(255), nullable=False)
    lastupdated = db.Column(db.DATETIME)
    pre = db.Column(db.String(255), nullable = False)
    post = db.Column(db.String(255), nullable = False)
    command = db.Column(db.String(255), nullable = False)
    project = db.Column(db.ForeignKey('projects.id'), nullable = False)
    runs = db.relationship('Results', backref='test_runner', lazy=True)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}
class Users(db.Model):
    email = db.Column(db.String(255), nullable = False, primary_key = True)
    name = db.Column(db.Integer, nullable = False)
    runs = db.relationship('Running', backref='users', lazy=True)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Results(db.Model):
    pid = db.Column(db.Integer, primary_key=True, nullable=False)
    uuid = db.Column(db.String(255), db.ForeignKey('running.uuid'), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    tests = db.Column(db.Integer, db.ForeignKey('test_runner.pid'), nullable=False)
    time = db.Column(db.DATETIME, nullable=False)
    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Status(db.Model):
    id = db.Column(db.String(255), nullable =False, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

@app.route('/create', methods = ['POST'])
def create():
    print(request.json)
    if('file' in request.files):
        file = request.files['file']
        file.save(os.path.join(app.config["UPLOAD_FOLDER"]), file.filename)
        return jsonify({"path" : os.path.join(app.config["UPLOAD_FOLDER"])})
    if(request.json.get('type', None) == "user"):
        user = Users(email = request.json.get('email', "N/A"), name = request.json.get('name', "N/A"))
        db.session.add(user)
        db.session.commit()
        return jsonify({"user" : False})
    if(request.json.get('type', None) == "testcase"):
        if(not request.json.get("projectid")):
            return jsonify({"error":True})
        test = TestRunner(
            ratings = request.json.get('rating', None), author = request.json.get('author', 'John Doe'), name = request.json.get('name', 'N/A'),
            lastupdated = request.json.get('date', None), pre = request.json.get('pre', ""), post = request.json.get('post', ""), 
            command = request.json.get("command", ""), project = request.json.get("projectid", 1)) 
        db.session.add(test)
        db.session.flush()
        pid = test.pid
        db.session.commit()
        return jsonify({"test_id" : pid})
    if(request.json.get('type', None) == "project"):
        project = Projects(name=request.json.get("name"),course=request.json.get("course"),section=request.json.get("section", "")
        ,lastupdated=request.json.get("lastupdated"), prof = request.json.get("prof",""))
        db.session.add(project)
        db.session.flush()
        pid = project.id
        db.session.commit()
        return jsonify({"proj_id":pid})
    return jsonify({"error" : True})



@app.route('/get', methods=['POST'])
def tests():
    if(request.json.get('type') == "project"):
        if(request.json.get('ct') == "ALL"):
            return jsonify([i.as_dict() for i in Projects.query.all()])
        else:
            return jsonify(Projects.query.filter(Projects.id == request.json.get('id')).first().as_dict())
    if(request.json.get('type') == "results"):
        return [i.as_dict() for i in db.session.query(Running, Results, TestRunner, Projects,Status).join(Results, 
        Results.uuid == Running.uuid).join(TestRunner, Results.tests == TestRunner.pid
        ).join(Projects, Running.project == Projects.id, 
        ).join(Status, Results.status == Status.name).filter(Running.uuid == request.json.get('uuid')).all()]
    if(request.json.get('type') == "testcases"):
        pass
    return jsonify({"error":False})


@app.route('/new', methods = ['POST'])
def new():
    return jsonify({"uuid": uuid.uuid4()})
if(__name__ == "__main__"):
    
    with engine.connect() as con:
        con.execute("SET FOREIGN_KEY_CHECKS = 0;drop table if exists running;drop table if exists projects;drop table if exists test_runner;SET FOREIGN_KEY_CHECKS = 1;")
        con.execute("SET FOREIGN_KEY_CHECKS = 0;drop table if exists users;drop table if exists results;SET FOREIGN_KEY_CHECKS = 1;")
        db.create_all()
        print(con.execute("SHOW COLUMNS from running").all())
        print(con.execute("SHOW COLUMNS from test_runner").all())

    
    app.run()
