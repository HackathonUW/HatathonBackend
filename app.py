from flask import Flask,request, jsonify
import gunicorn
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table, Enum
from sqlalchemy.types import TEXT
import os
from flask_cors import CORS

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
    ratings = db.Column(db.Integer, nullable=False)
    author = db.Column(db.String(255), nullable = False)

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
    if(request.json.get('type', None) == "user"):
        db.session.add(Users(email = request.json.get('email', "N/A"), name = request.json.get('name', "N/A"), tests= ""))
        db.session.commit()
        return jsonify({"error" : False})
    if('file' in request.files):
        file = request.files['file']
        file.save(os.path.join(app.config["UPLOAD_FOLDER"]), file.filename)
        return jsonify({"path" : os.path.join(app.config["UPLOAD_FOLDER"])})

@app.route('/tests', methods=['POST'])
def tests():
    print(request.json.get('name',None))
    if(request.json.get('name',None) == 'all'):
        for i in db.session.query(TestRunner).all():
            print(i)
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
    print(app.url_map)
    app.run()
