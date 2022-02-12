from flask import Flask,request, jsonify
import gunicorn
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table, Enum
from sqlalchemy.types import TEXT
import os
from flask_cors import CORS
from MySQLdb import _mysql

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

class TestRunner(db.Model):
    pid = db.Column(db.Integer,nullable=False, primary_key=True)
    ratings = db.Column(db.Integer)
    author = db.Column(db.String(255), nullable = False)
    name  = db.Column(db.String(255), nullable=False)
    lastupdated = db.Column(db.DATETIME)
    pre = db.Column(db.String(255), nullable = False)
    post = db.Column(db.String(255), nullable = False)
    command = db.Column(db.String(255), nullable = False)
    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}
class Users(db.Model):
    email = db.Column(db.String(255), nullable = False, primary_key = True)
    name = db.Column(db.Integer, nullable = False)
    tests = db.Column(db.TEXT, nullable = False)
    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

@app.route('/create', methods = ['POST'])
def create():
    print(request.files)
    if('file' in request.files):
        file = request.files['file']
        file.save(os.path.join(app.config["UPLOAD_FOLDER"]), file.filename)
        return jsonify({"path" : os.path.join(app.config["UPLOAD_FOLDER"])})
    if(request.json.get('type', None) == "user"):
        db.session.add(Users(email = request.json.get('email', "N/A"), name = request.json.get('name', "N/A"), tests= ""))
        db.session.commit()
        return jsonify({"error" : False})
    if(request.json.get('type', None) == "testcase"):
        db.session.add(TestRunner(
            ratings = request.json.get('rating', None), author = request.json.get('author', 'John Doe'), name = request.json.get('name', 'N/A'),
            lastupdated = request.json.get('date', None), pre = request.json.get('pre', ""), post = request.json.get('post', ""), 
            command = request.json.get("command", "") ))
        return jsonify({"error" : False})
    return jsonify({"error" : True})



@app.route('/tests', methods=['POST'])
def tests():
    print(request.json.get('name',None))
    if(request.json.get('name',None) == 'all'):
        return jsonify([i.as_dict() for i in db.session.query(TestRunner).all()])
    if(request.json.get('name', None)):
        return jsonify([i.as_dict() for i in db.session.query(TestRunner).filter(name=request.json.get("name")).first()])
    if(request.json.get('id', None)):
        return jsonify([i.as_dict() for i in db.session.query(TestRunner).filter(pid = request.json.get("id").first())])
    return jsonify({"error":False})
@app.route('/users', methods = ['POST'])
def users():
    if(request.json.get('name', None) != None):
        tests = Users.query.filter_by(email=request.json.get('email')).first()["tests"].split(" ")
    return jsonify({"error" : False})


if(__name__ == "__main__"):
    '''
    with engine.connect() as con:
        print(con.execute("SELECT * FROM information_schema.tables").fetchall())
    '''
    app.run()
