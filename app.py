from datetime import datetime
import os
from flask import Flask, flash, jsonify, request, redirect, url_for,render_template
from werkzeug.utils import secure_filename
from flask import send_from_directory
from flask import current_app
import base64
import json
import cv2 as cv
from domains.enums import setting as appset
from Models.FileViewModels import UPLOAD_FOLDER,ARCHAVE_FILE,UPLOAD_THUMBNAIL_FOLDER,UPLOAD_FACES_FOLDER,ALLOWED_EXTENSIONS_MAGIC_NUMBER,ARCHIVE_PASSWORD,ALLOWED_EXTENSIONS
from Models import RedisORM,FileViewModels



app = Flask(__name__,template_folder="templates",static_url_path='/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ARCHAVE_FILE'] = ARCHAVE_FILE
app.config['UPLOAD_THUMBNAIL_FOLDER'] = UPLOAD_THUMBNAIL_FOLDER
app.config['UPLOAD_FACES_FOLDER'] = UPLOAD_FACES_FOLDER


########### Web Pages ############
redis1 = RedisORM.mRedis()._redis
mFile = FileViewModels.mFile(RedisDB=redis1,FlaskApp=app,current_app=current_app)



@app.route("/")
def site_map():

    if redis1.get("SuperUser") == None:
        return redirect(url_for('Wizard'))

    links = []
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods :#and has_no_empty_params(rule):
            #url = url_for(rule.endpoint,)
            params = rule.arguments
            links.append({"url":rule,"endpoint": rule.endpoint,"params":params})
    # links is now a list of url, endpoint tuples
    return render_template("index.html",links=links)




@app.route("/Wizard",methods=['GET','POST'])
def Wizard():
    if request.method == "GET":
        return render_template("wizard.html",list=["",ALLOWED_EXTENSIONS_MAGIC_NUMBER,])
    elif request.method == "POST":
        username= request.form.get('username')
        password= request.form.get('pass')
        password2= request.form.get('pass2')
        hashKey= request.form.get('inputhashKey')
        ext= request.form.get('extToHash').split('|')
        ext.pop()
        if any(item not in ALLOWED_EXTENSIONS_MAGIC_NUMBER for item in ext):
            
           return render_template("wizard.html",list=["O No !!! this is bad requsts",ALLOWED_EXTENSIONS_MAGIC_NUMBER,])
        
        if password != password2 or username == '':
            return render_template("wizard.html",list=["user name or password is wrong !",ALLOWED_EXTENSIONS_MAGIC_NUMBER,])

        
        redis1.set(appset.SuperUser,username)
        redis1.set(appset.SuperUserPassWord,password)
        redis1.set(appset.fileExtentionToHash,str.join("|" ,ext))
        if hashKey != '':
            redis1.set(appset.FileHashKey,hashKey)
        

        return  """{{status:200,msg:"setup complit successully "}}"""
        

    
########### Web Pages ############

@app.route('/repair', methods=['GET', 'POST'])
def repair_redis():
    mFile.checkDirectory()
    files =os.listdir(app.config['UPLOAD_FOLDER'])
    for file in files:
        
        if file.count('.')>0:
            if (redis1.get(str(file).split(".")[0]) or b'').decode("utf-8") != file :
                redis1.set(str(file).split(".")[0],str(file))
        else:
            if (redis1.get(str(file)) or b'').decode("utf-8") != file :
                redis1.set(str(file),str(file))

    return """{{status:200,msg:"success "}}"""



@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return """{{status:200,msg:"No selected file"}}"""
        
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return """{{status:200,msg:"No selected file"}}"""
        
        if mFile.checkDirectory() ==False:
            return """{{status:500,msg:"Some thing wrong"}}"""
        
        if file and mFile.allowed_file(file.filename):
            filename, justfileName = mFile.saveFileOnDirectory(file)
            if filename is None or justfileName is None:
                return """{{status:200,msg:"File extention has damaged"}}"""
            return jsonify(f"file_name:{justfileName}")
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''



### begin ### down load 

@app.route('/download/file/<path:filename>',endpoint='file', methods=['GET', 'POST'])
@app.route('/download/tumbnail/<path:filename>',endpoint='tumbnail', methods=['GET', 'POST'])
@app.route('/download/base64/<path:filename>',endpoint='base64', methods=['GET', 'POST'])
@app.route('/download/faces/<path:filename>',endpoint='faces', methods=['GET', 'POST'])
def download(filename:str):
    if "." in filename:
        return """{{status:200,msg:"wrong file name"}}"""
    orginalFileName = mFile.check_res_db(filename) 
    if (orginalFileName or "") == "":
        return """{{status:200,msg:"file not exits"}}"""
    uploadsurl = mFile.getUploadUrl()
    
    
    if request.endpoint.lower()=='tumbnail':
        tmpath,fName = mFile.GetThumbNail(orginalFileName)
        file = send_from_directory(tmpath,fName)
    elif request.endpoint.lower()=='file':
        file = send_from_directory(uploadsurl, str(orginalFileName))
    elif request.endpoint.lower() == "base64":
        with open(os.path.join(uploadsurl, str(orginalFileName)), "rb") as fh:
            file= base64.b64encode(fh.read())
    elif request.endpoint.lower() == "faces":
        address,fileName = getFacees(orginalFileName)
        file = send_from_directory(address, str(fileName))
    return file



@app.route('/all',methods = ["GET","POST"])
def getAllFileKeys():
    allkeys = redis1.keys("*")
    kes =[x.decode("utf-8") for x in allkeys ]
    return json.dumps(kes)
    #return "keys:[{0}]".format(kes)

    


def getFacees(fileName):
    #fileUrl =GetRealFileAddress(fileName=fileName)
    img  = cv.imread(mFile.getFileURL(fileName))
    face_cascade = cv.CascadeClassifier(cv.data.haarcascades + 'haarcascade_frontalface_default.xml')
    #eye_cascade = cv.CascadeClassifier(cv.data.haarcascades + 'haarcascade_eye.xml')
    
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    # Detect faces
    faces = face_cascade.detectMultiScale(gray, 1.1,4)
    #eyes = eye_cascade.detectMultiScale(gray, 1.1,4)
    # Draw rectangle around the faces
    for (x, y, w, h) in faces:
        cv.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
    # for (x, y, w, h) in eyes:
    #     cv.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
    
    faceFileAddress=os.path.join(app.config['UPLOAD_FACES_FOLDER'], fileName)
    cv.imwrite(faceFileAddress,img)
    return app.config['UPLOAD_FACES_FOLDER'],fileName


@app.after_request
def after_requst(response):
    print("Log>>>>>>>Some Requst on ",datetime.now(),response)
    return response

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=5055)