#!/usr/bin/python3.7
#region --Import Packages--
import atexit
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from twilio.twiml.messaging_response import MessagingResponse
import os
import boto3, botocore
#endregion

#region --Initialize App, MySQL, AWS --
app = Flask(__name__)
mysql = MySQL()

# MySQL configurations
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_DB'] = 'LectureHub_DB'
app.config['UPLOAD_FOLDER'] = './files'
#app.config['MYSQL_DATABASE_PASSWORD'] = ''
#app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# AWS Config TODO: Remove token from repo and prompt entry from cmd line
S3_BUCKET                 = "lecturehub" #os.environ.get("S3_BUCKET_NAME")
S3_KEY                    = "AKIAIJKMZ3EZF4PP7IFQ" #os.environ.get("S3_ACCESS_KEY")
S3_SECRET                 = "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" #os.environ.get("S3_SECRET_ACCESS_KEY")
S3_LOCATION               = 'http://{}.s3.amazonaws.com/'.format(S3_BUCKET)
s3 = boto3.client(
   "s3",
   aws_access_key_id=S3_KEY,
   aws_secret_access_key=S3_SECRET
)
#endregion

'''
Application helper functions
'''
#Param: unique user id (int) Return: descriptive name of user (string)
#Get name of the user given unique user identifier
def getUserName(uid):
    struid = str(uid)
    cur = mysql.connection.cursor()
    sqlCommand = f"SELECT name from Userdata where id = \"{struid}\""
    cur.execute(sqlCommand)
    users = cur.fetchall()
    return users[0][0]

#Param: file (file-like object) bucket_name (string) acl (string) 
#Return: public url to file on AWS lecturehub bucket
#S3 Integration Helper
def upload_file_to_s3(file, bucket_name, acl="public-read"):
    s3.upload_fileobj(
        file,
        bucket_name,
        file.filename,
        ExtraArgs={
            "ACL": acl,
            "ContentType": file.content_type
        }
    )
    return "{}{}".format(S3_LOCATION, file.filename)

#Param: unique user id (int) Return: descriptive university name (string)
#Get name of the user's university given unique user identifier
def getUniversityName(uid):
    struid = str(uid)
    cur = mysql.connection.cursor()
    sqlCommand =  f"SELECT university FROM Userdata where id = \"{struid}\""
    cur.execute(sqlCommand)
    university = cur.fetchall()
    return university[0][0]

#Param: filename (string) Return: boolean
#Allowed Filename Helper - Checks if filename is allowed to be uploaded
def allowed_file(filename):
    UNALLOWED_EXTENSIONS = set(['exe','bash','php','py'])
    return '.' in filename and \
        not (filename.rsplit('.', 1)[1].lower() in UNALLOWED_EXTENSIONS)

#Param: userid (int) courseid (string) url (string) Return: response (json)
#Refactor code to add file URI to database into helper
def add_file_to_uploadedfiles(userid, courseid, url):
    response = {"status": False}
    cur = mysql.connection.cursor()

    #Check if course exists, if not add new course
    sqlCommand = f"SELECT university FROM Userdata where id = \"{userid}\""
    cur.execute(sqlCommand)
    university = cur.fetchall()[0][0]

    #Check for existing course
    cur.execute(f"SELECT id FROM Courseinfo where UniversityName = \"{university}\" AND CourseID = \"{courseid}\"")
    course = cur.fetchall()

    if(len(course) == 0):
        sqlCommand = f"INSERT INTO Courseinfo (UniversityName, Courseid) VALUES (\"{university}\", \"{courseid}\")"
        cur.execute(sqlCommand)    
        mysql.connection.commit()  
        cur.execute(f"SELECT id FROM Courseinfo where UniversityName = \"{university}\" AND CourseID = \"{courseid}\"")
        course = cur.fetchall()
    
    #Insert file
    uniqueCourseID = course[0][0]
    sqlCommand = f"INSERT INTO UploadedFiles (path, userID, thumbsup, thumbsdown, uniqueCourseID) VALUES (\"{url}\", \"{userid}\", \"0\", \"0\", \"{uniqueCourseID}\")"
    cur.execute(sqlCommand)
    mysql.connection.commit()

    #Indicate response
    response = {"status": True}
    return response

'''
Backend routes are implemented below:
'''

#Login user
@app.route('/login', methods=["POST"])
def login_user():
    #Create default, false response
    response = {"status" : False, "id": -1}

    try:
        #Get login credentials
        email = request.json['email'] #TODO: Change these to what the json actually is
        password = request.json['password']
        #Query for row of userdata
        cur = mysql.connection.cursor()
        
        sqlCommand = f"SELECT id,name FROM Userdata where email = \"{email}\" AND password = \"{password}\""
        cur.execute(sqlCommand)

        users = cur.fetchall()
        #Error out if there is no user
        if len(users) != 0:
            response = {"status" : True, "id": users[0][0], "name": users[0][1]}
    except:
        response = {"status" : False, "id": -2}

    finally:
        return jsonify(response)   

#Register new user
@app.route('/register', methods=["POST"])
def register_user():
    
    try:
        response = {"status" : False}

        email = request.json['email']
        password = request.json['password']
        name = request.json['first'] + " " +  request.json['last']

        cur = mysql.connection.cursor()
        #Check for existing user
        cur.execute(f"SELECT id FROM Userdata where email = \"{email}\"")
        user = cur.fetchall()

        if (len(user) > 0):
            response = {"status" : False}
        elif (".edu" in email) and (len(user) == 0):
            temp = email.split('@')
            temp = temp[-1].split('.')
            university = temp[-2]
            sqlCommand = f"INSERT INTO Userdata (email, password, university, name) VALUES (\"{email}\", \"{password}\", \"{university}\", \"{name}\")"
            cur.execute(sqlCommand)
            mysql.connection.commit()
            response = {"status" : True}
    except:
        response = {"status" : False}
    finally:
        return jsonify(response)

#File Upload Route
@app.route('/uploadfile', methods=['POST'])
def upload_file(): 
    userID = request.json['userid']
    url = request.json['fileurl']
    courseID = request.json['cid']

    #Call refactored addfile function
    return jsonify(add_file_to_uploadedfiles(userID, courseID, url))

#Mobile File Upload Route
@app.route('/mobileUpload', methods=['POST'])
def mobile_upload():
    #Fetch AWS url from boto helper
    print(request.form)
    pdf = request.files['pdf_uploaded']
    pdf.filename = secure_filename(pdf.filename)
    url = upload_file_to_s3(pdf, S3_BUCKET)
    print(url)
    #Fetch userID and cid from json param
    userID = request.form['userid']
    courseID = request.form['cid']
    print(userID)

    #Call refactored addfile function
    return jsonify(add_file_to_uploadedfiles(userID, courseID, url))

#Course Info Route
@app.route('/addCourse', methods=['POST'])
def add_course():
    courseID = request.json['cid']
    userID = request.json['id']
    university = getUniversityName(userID)
    
    #Query for row of userdata
    cur = mysql.connection.cursor()

    #Check for existing course
    cur.execute(f"SELECT Courseid FROM Courseinfo where UniversityName = \"{university}\" AND CourseID = \"{courseID}\"")
    course = cur.fetchall()

    if (len(course) != 0):
        response = {"status" : False}
        return jsonify(response)
    
    sqlCommand = f"INSERT INTO Courseinfo (UniversityName, Courseid) VALUES (\"{university}\", \"{courseID}\")"
    cur.execute(sqlCommand)
    mysql.connection.commit()
    response = response = {"status" : True}
    return jsonify(response)

#Get List of Courses
@app.route('/courseCatalog', methods=['POST'])
def get_catalog():
    userID = request.json['id']
    university = getUniversityName(userID)

    #Query for row of userdata
    cur = mysql.connection.cursor()

    #Get catalog of courses at the university
    cur.execute(f"SELECT CourseID FROM Courseinfo where UniversityName = \"{university}\"")
    course = cur.fetchall()

    catalog = []
    for coursecode in course:
        catalog.append({"code" : coursecode[0]})

    return jsonify({"courses" : catalog})

#File Download Route
@app.route('/retrieveFile', methods=['POST'])
def retrieve_file():
    response = {"status" : False, "fileURL" : "-1"}

    courseID = request.json['cid']
    userID = request.json['userid']
    cur = mysql.connection.cursor()
    universityName = getUniversityName(userID)

    command = f"SELECT id from Courseinfo where CourseID = \"{courseID}\" AND UniversityName = \"{universityName}\""
    cur.execute(command)

    uniqueCourseIDs = cur.fetchall()   

    if len(uniqueCourseIDs) > 0:
        uniqueCourseID = uniqueCourseIDs[0][0]
        command = f"SELECT userID, path, thumbsUp, thumbsDown, id from UploadedFiles where uniqueCourseID = \"{uniqueCourseID}\""
        cur.execute(command)
        files = cur.fetchall()
        
        if len(files) != 0:
            filesReturn = [] 
            for f in files:
                creatorName = getUserName(f[0])
                fileData = {"id" : f[0], "path" : f[1], "thumbsUp" : f[2], "thumbsDown": f[3], "creator": creatorName, "uniqueid": f[4]}      
                filesReturn.append(fileData)
            response = {"status" : True, "fileData" : filesReturn}

    return jsonify(response)

#Rating System TODO: Hook frontend into rating system
#region rating system routes ---UNIMPLEMENTED---
@app.route('/incrementRating', methods=['POST'])
def incrementRating():
    response = {"status" : False, "thumbsUp" : None}

    fileID = request.json['fileid']
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT thumbsUp from UploadedFiles where id = \"{fileID}\"")
    currentFile = cur.fetchall()
    if len(currentFile) > 0:
        currentValue = currentFile[0][0]
        cur.execute(f"UPDATE UploadedFiles SET thumbsUp = \"{currentValue + 1}\" id = \"{fileID}\"")
        mysql.connection.commit()
        response = {"status" : True, "thumbsUp" : currentValue + 1}
    
    return jsonify(response)

@app.route('/decrementRating', methods=['POST'])
def decrementRating():
    response = {"status" : False, "thumbsDown" : None}

    fileID = request.json['fileid']
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT thumbsDown from UploadedFiles where id = \"{fileID}\"")
    currentFile = cur.fetchall()
    if len(currentFile) > 0:
        currentValue = currentFile[0][0]
        cur.execute(f"UPDATE UploadedFiles SET thumbsDown = \"{currentValue + 1}\" id = \"{fileID}\"")
        mysql.connection.commit()
        response = {"status" : True, "thumbsDown" : currentValue + 1}
    
    return jsonify(response)

@app.route('/getRating', methods=['POST'])
def getRating():
    response = {"status" : False, "thumbsUp": None, "thumbsDown" : None}

    fileID = request.json['fileid']
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT thumbsUp, thumbsDown from UploadedFiles where id = \"{fileID}\"")
    currentFile = cur.fetchall()
    if len(currentFile) > 0:
        currentValues = currentFile[0]
        response = {"status" : True, "thumbsUp" : currentValues[0], "thumbsDown": currentValues[1]}
    
    return jsonify(response)

#MARK - Twillio API
@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():

    # Get user response
    reply = request.values.get('Body', None)

    # Start our response
    resp = MessagingResponse()

    # Add a message
    if reply == 'GIVE LEGAL INFO':
        resp.message("Hello I am lawyer here is 311 stuff: (311 Stuff)")
    elif reply != 'START':
        resp.message("Not a valid response.")

    return str(resp)
#endregion