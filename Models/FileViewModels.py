import os
from datetime import datetime
from werkzeug.utils import secure_filename
import binascii
import random 
import zipfile
from domains.enums import setting as appset
import cv2 as cv
import redis
# from flask import current_app
# from app import app as app
# from app import redis1 as redis1
# class mFile:


UPLOAD_FOLDER = 'uploads'
UPLOAD_THUMBNAIL_FOLDER = 'uploads/thumbnail'
UPLOAD_FACES_FOLDER = 'uploads/Faces'
ARCHAVE_FILE = 'uploads/archive.zip'
ARCHIVE_PASSWORD = b"dsdy8271@#&^$&(!@#ayan0928S#B"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_EXTENSIONS_MAGIC_NUMBER = {'txt':'EF BB BF'
                                    , 'pdf':'25 50 44 46 2D'
                                    , 'png':'89 50 4E 47 0D 0A 1A 0A'
                                    , 'jpg':'FF D8 FF E0'
                                    , 'jpeg':'FF D8 FF'
                                    , 'gif':'47 49 46 38 37 61'}



class mFile():

    _redisDB :redis.Redis = None
    _app = None
    _current_app = None

    def __init__(self,RedisDB,FlaskApp,current_app) -> None:
        self._redisDB = RedisDB
        self._app = FlaskApp
        self._current_app = current_app

    

    def saveFileOnDirectory(self,file):
        filename = secure_filename(file.filename)
        justfileName ,filename = self.getSecureFileName(file.filename)
                #path = current_app.root_path+"/"+app.config['UPLOAD_FOLDER']+
        filePath = os.path.join(self._current_app.root_path,self._app.config['UPLOAD_FOLDER'], filename)
        file.save(filePath)
        self.compress_File(filePath=os.path.join(self._app.config['UPLOAD_FOLDER'] ,filename) )
        if self.checkFileRealExtention(fileName=filePath):
            #self._redisDB.set(justfileName,filename)
            #toto: set hash key for save full path of file
            # self._redisDB.hsetnx(justfileName,key="filePath",value=filePath)
            mapping=dict()
            mapping["RealFileName"]=filename
            mapping["FilePath"]=filePath
            self._redisDB.hset(justfileName,mapping=mapping)
            self.EncryptFile(justfileName)
            return filename,justfileName
        else:
            os.remove(filePath)
            return None,None
    def getUploadUrl(self):
        uploadsurl = os.path.join(self._current_app.root_path,self._app.config['UPLOAD_FOLDER'])
        return uploadsurl
    def getFileURL(self,fileName):
        return os.path.join(self.getUploadUrl(), str(fileName))
    def getArchiveUrl(self):
        #archiveFile = os.path.join(current_app.root_path, app.config['ARCHAVE_FILE'])
        return self._app.config['ARCHAVE_FILE']
    def GetRealFileAddress(self,fileName):
        realfileName=self.check_res_db(filename=fileName)
        fileUrl = self.getFileURL(realfileName)
        return fileUrl
    def check_res_db(self,filename):
        orginalFileName = self._redisDB.hget(filename,"RealFileName")
        orginalFileName = orginalFileName.decode("utf-8")
        return orginalFileName
    def compress_File(self,filePath):
        try:
            if(self.checkArchiveFile() == False ):
                return
            with zipfile.ZipFile(self.getArchiveUrl(), "a") as zf:
                zf.write(filePath)
                zf.setpassword(ARCHIVE_PASSWORD)
                zf.close()
            return True
        except Exception as ex:
            print(ex)
            return False
    def getSecureFileName(self,orginalFileName:str):
        filename = datetime.now().strftime('%Y%m%d%H%M%S') + str(random.randint(0,100000))
        return filename,filename +"."+ orginalFileName.split(".")[1]
    def GetThumbNail(self,fileName):
        """get file Name as input and  return path and file Name as output """
        try:
            filepath = self.getFileURL(fileName)
            img = cv.imread(filepath)
            thumbNailSize=(100,100)
            imRes = cv.resize(img,thumbNailSize,interpolation=cv.INTER_CUBIC)
            thumbFilePath=os.path.join(self._app.config['UPLOAD_THUMBNAIL_FOLDER'], fileName)
            cv.imwrite( thumbFilePath,imRes)
            return self._app.config['UPLOAD_THUMBNAIL_FOLDER'] , fileName
        except:
            return None,None
    def allowed_file(self,filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    def checkFileRealExtention(self,fileName):
        fileExt = self.getFileFileExtention(fileName)
        magicNum = ALLOWED_EXTENSIONS_MAGIC_NUMBER[fileExt]
        with open(fileName, mode='rb') as file: # b is important -> binary
            fileContent = file.read()
            header = str(binascii.hexlify(fileContent))[2:-1]
        if header.startswith(magicNum.lower().replace(' ','')):
            return True
        else:
            return False
    def getFileFileExtention(self,file):
        if '.' in file:
            return file and file.split(".")[1]
        else:
            realFileName =self._redisDB.hget(file,"RealFileName").decode("utf-8")
            return realFileName and realFileName.split(".")[1]
    def checkDirectory(self):
        try:
            if not os.path.exists(self._app.config['UPLOAD_FOLDER']):
                os.makedirs(self._app.config['UPLOAD_FOLDER'])
            if not os.path.exists(self._app.config['UPLOAD_THUMBNAIL_FOLDER']):
                os.makedirs(self._app.config['UPLOAD_THUMBNAIL_FOLDER'])
            if not os.path.exists(self._app.config['UPLOAD_FACES_FOLDER']):
                os.makedirs(self._app.config['UPLOAD_FACES_FOLDER'])
            True
        except:
            return False
    def checkArchiveFile(self):
        try:
            if not os.path.exists(self._app.config['ARCHAVE_FILE']):
                open(self._app.config['ARCHAVE_FILE'],"w")
            return True
        except Exception as ex:
            print(ex)
            return False
    def EncryptFile(self,fileName):
        if self._redisDB.get(appset.FileHashKey) != None:
            extsMustHash = self._redisDB.get(appset.fileExtentionToHash).decode("utf-8") 
            if self.getFileFileExtention(fileName) in str(extsMustHash).split("|"):
                self._redisDB.publish("HashChannel",fileName)