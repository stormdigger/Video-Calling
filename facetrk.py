
import cv2
import mediapipe as mp
import keyboard
import numpy as np 
import os
import face_recognition

class facedetector():
    def __init__(self, minConVal= 0.5):
        self.minConVal = minConVal
        self.mpFacedetection = mp.solutions.face_detection
        self.faceDetection = self.mpFacedetection.FaceDetection(self.minConVal)
        
    def find_faces(self,img,draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        self.results = self.faceDetection.process(imgRGB)
        
        bboxes = []

        if self.results.detections:
            for id, detection in enumerate(self.results.detections):
                bboxC = detection.location_data.relative_bounding_box
                ih, iw, ic = img.shape
                
                bbox = int(bboxC.xmin * iw), int(bboxC.ymin * ih), \
                    int(bboxC.width * iw), int(bboxC.height * ih)
                (x,y,w,h) = bbox

                bboxes.append([bbox, detection.score])
                img = self.border(img, bbox)
                cv2.putText(img, f'{int(detection.score[0]*100)}%',(bbox[0],bbox[1]-20),cv2.FONT_HERSHEY_SCRIPT_COMPLEX,1,(0,0,255),3)
        
            return img, bboxes
        else :
            return None,None
    
    def border(self, img, bbox, ln = 30, t = 5, rt = 2):
        x, y, w, h = bbox
        x1, y1 = x + w , y + h
        bordercolor = (0,255,0)
        corners = (200,0,0)
        cv2.rectangle(img, bbox, bordercolor, rt)
        cv2.line(img,(x,y),(x+ln,y),corners,t)
        cv2.line(img,(x,y),(x,y+ln),corners,t) # TOP-LEFT
        cv2.line(img,(x1,y),(x1-ln,y),corners,t)
        cv2.line(img,(x1,y),(x1,y+ln),corners,t) # TOP-RIGHT
        cv2.line(img,(x,y1),(x+ln,y1),corners,t)
        cv2.line(img,(x,y1),(x,y1-ln),corners,t) # BOTTOM-LEFT
        cv2.line(img,(x1,y1),(x1-ln,y1),corners,t)
        cv2.line(img,(x1,y1),(x1,y1-ln),corners,t) # BOTTOM-RIGHT
        return img

class FaceRecognizer():
    def trainImgs(self, images):
        dataList = []
        for img in images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            train = face_recognition.face_encodings(img)[0]
            dataList.append(train)
        return dataList

    def recognize(self, img, trainImgList, names, name, faceDistance):
        name="Unknown"
        reducedImg = cv2.resize(img, (0,0),None,0.25,0.25)
        reducedImg = cv2.cvtColor(reducedImg, cv2.COLOR_BGR2RGB)
        
        facesCurFrame = face_recognition.face_locations(reducedImg)
        encode = face_recognition.face_encodings(reducedImg, facesCurFrame)

        for encodeFace, faceLoc in zip(encode, facesCurFrame):
            matches = face_recognition.compare_faces(trainImgList,encodeFace)
            faceDis = face_recognition.face_distance(trainImgList,encodeFace)
            print(faceDis)
            matchIndex = np.argmin(faceDis)
            faceDistance = faceDis
            print(matchIndex)
            if matches[matchIndex]:
                name = names[matchIndex].upper()
                y1,x2,y2,x1 = faceLoc
                y1,x2,y2,x1 = y1*4,x2*4,y2*4,x1*4
                cv2.rectangle(img,(x1,y1),(x2,y2),(0,255,0),2)
                cv2.rectangle(img, (x1,y2-35), (x2,y2), (0,255,0),cv2.FILLED)
                cv2.putText(img, name, (x1+6,y2-6), cv2.FONT_HERSHEY_COMPLEX, 1, (255,255,255),2)
        return img, name, faceDistance

class FaceMeshDetector():

    def __init__(self,staticMode=False):
        self.mpFaceMesh = mp.solutions.face_mesh
        self.mpDraw = mp.solutions.drawing_utils
        self.facemesh = self.mpFaceMesh.FaceMesh(max_num_faces=1,refine_landmarks=True)  
        self.drawSpecm = self.mpDraw.DrawingSpec(thickness=1,circle_radius=1,color=(0,255,0))
        self.drawSpecb = self.mpDraw.DrawingSpec(thickness=1,circle_radius=2,color=(0,0,255))

    # mesh on the video
    def mesh(self,img):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.result = self.facemesh.process(imgRGB)
        if self.result.multi_face_landmarks:
            for faceLMS in self.result.multi_face_landmarks:
                self.mpDraw.draw_landmarks(img, faceLMS, self.mpFaceMesh.FACEMESH_IRISES,self.drawSpecm,self.drawSpecm)

        else:
            faceLMS = []
        return img, faceLMS

    #mesh without the video
    def bmesh(self, img, names, faceDistance, name):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.result = self.facemesh.process(imgRGB)
        ih, iw, ic = img.shape
        cv2.rectangle(img, (0,0), (iw,ih), (0,0,0),cv2.FILLED)
        if self.result.multi_face_landmarks:
            for faceLMS in self.result.multi_face_landmarks:
                # cv2.putText(img, "Known-faces : " + str(names), (10,400), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255))
                # cv2.putText(img, "Face-distances : " + str(faceDistance), (10,420), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255))
                # cv2.putText(img, "Best Match : " + name, (10,440), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255))
                self.mpDraw.draw_landmarks(img, faceLMS, self.mpFaceMesh.FACEMESH_TESSELATION,self.drawSpecb,self.drawSpecb)
        return img
