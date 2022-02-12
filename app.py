from flask import Flask,request, jsonify, make_response, send_from_directory
import gunicorn
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table, Enum
from sqlalchemy.types import TEXT
import os
from flask_cors import CORS
from MySQLdb import _mysql
import uuid
from datetime import datetime, timedelta
import sys
import boto3
from botocore.client import Config
s3 = boto3.resource('s3',
                    endpoint_url='https://' + 'tzduk7.stackhero-network.com',
                    aws_access_key_id='K42RaBy0hxCPhckiipNC',
                    aws_secret_access_key='L5IjAK7rt9ETUyl01aGTnzW3jLGpra1Ocwc0qVlp',
                    config=Config(signature_version='s3v4'),
                    region_name='us-east-1')
def currdate():
    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
    return dt_string
app = Flask(__name__, static_url_path='/static')
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
    input = db.Column(db.String(255), nullable= False)
    output = db.Column(db.String(255), nullable = False)
    runs = db.relationship('Results', backref='test_runner', lazy=True)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}
class Users(db.Model):
    email = db.Column(db.String(255), nullable = False, primary_key = True)
    name = db.Column(db.String(255), nullable = False)
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
    print(request.files)
    sys.stdout.flush()

    if(request.files.get('file', None)):
        files = request.files.getlist('file')
        resp = {"path" : []}
        for file in files:
            s3.Bucket('files').upload_fileobj(file,os.path.join(app.config["UPLOAD_FOLDER"],file.filename))
            resp["path"].append(os.path.join(app.config["UPLOAD_FOLDER"], file.filename))
        return jsonify(resp)
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
            lastupdated = currdate(), pre = request.json.get('pre', ""), post = request.json.get('post', ""), 
            command = request.json.get("command", ""), project = request.json.get("projectid", 1),input = request.json.get('input'),
            output=request.json.get('output') ) 
        db.session.add(test)
        db.session.flush()
        pid = test.pid
        db.session.commit()
        return jsonify({"test_id" : pid})
    if(request.json.get('type', None) == "project"):
        project = Projects(name=request.json.get("name"),course=request.json.get("course"),section=request.json.get("section", "")
        ,lastupdated=currdate(), prof = request.json.get("prof",""))
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
            if(Projects.query.filter(Projects.id == request.json.get('id')).first()):
                return jsonify(Projects.query.filter(Projects.id == request.json.get('id')).first().as_dict())
            else:
                return jsonify({"error" : True})

    if(request.json.get('type') == "results"):
        return jsonify([i.as_dict() for i in db.session.query(Running, Results, TestRunner, Projects,Status).join(Results, 
        Results.uuid == Running.uuid).join(TestRunner, Results.tests == TestRunner.pid
        ).join(Projects, Running.project == Projects.id, 
        ).join(Status, Results.status == Status.id).filter(Running.uuid == request.json.get('uuid')).all()])
    if(request.json.get('type') == "testcases"):
        return jsonify([i.as_dict() for i in TestRunner.query.filter(TestRunner.project == request.json.get('proj_id')).all()])
    if(request.json.get('type') == "running"):
        return jsonify([i.as_dict() for i in Running.query.all()])
    if(request.json.get("type") == "users"):
        return jsonify([i.as_dict() for i in Users.query.all()])
    return jsonify({"error":False})


@app.route('/new', methods = ['POST'])
def new():
    return jsonify({"uuid": uuid.uuid4()})

@app.route('/run', methods=["POST"])
def run():
    Running.query.filter(Running.time < (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")).delete()
    uuid = request.json.get('uuid') 
    proj_id = request.json.get("projectid")
    email = request.json.get("email")
    if(Running.query.filter(Running.uuid == uuid).first()):
        Running.query.filter(Running.uuid == uuid).delete()
        db.session.commit()
        running = Running(uuid = uuid, project = proj_id, email = email)
        db.session.add(running)
        db.session.commit()
        Results.query.filter(Results.uuid == uuid).delete()
        db.session.commit()
        for i in TestRunner.query.filter(TestRunner.project == proj_id).all():
            results = Results(uuid = uuid, status = request.json.get("status", 3), tests=i.pid, time = currdate())
            db.session.add(results)
            db.session.commit()
        return jsonify({"error" : False})

    else:
        running = Running(uuid = uuid, project = proj_id, email = email)
        db.session.add(running)
        db.session.commit()
        for i in TestRunner.query.filter(TestRunner.project == proj_id).all():
            results = Results(uuid = uuid, status = request.json.get("status", 3), tests=i.pid, time = currdate())
            db.session.add(results)
            db.session.commit()
        return jsonify({"error" : False})

@app.route('/static/<path>')
def serve(path):
    print(path)
    return s3.Object('files','/static/'+path).get()['Body'].read().decode("ascii")
@app.route('/edit', methods=["POST"])
def post():
    if(request.json.get("type") == "vote"):
        TestRunner.query.filter(TestRunner.pid == request.json.get("id")).ratings += 1
    return jsonify({"error" : False})
if(__name__ == "__main__"):
    
    with engine.connect() as con:
        #con.execute("SET FOREIGN_KEY_CHECKS = 0;drop table if exists running;drop table if exists projects;drop table if exists test_runner;SET FOREIGN_KEY_CHECKS = 1;")
        #con.execute("SET FOREIGN_KEY_CHECKS = 0;drop table if exists test_runner ;SET FOREIGN_KEY_CHECKS = 1;")
        db.create_all()
        print(con.execute("SHOW COLUMNS from running").all())
        print(con.execute("SHOW COLUMNS from test_runner").all())
        print(con.execute("SELECT * FROM test_runner").all())
        db.create_all()
    
    app.run()
