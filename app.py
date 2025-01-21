from flask import Flask, render_template, request, redirect, url_for, flash,jsonify
from flask_login import UserMixin, LoginManager, login_required, logout_user, current_user, login_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, HiddenField
from wtforms.validators import ValidationError, InputRequired, Length
from flask_wtf.file import FileField, FileAllowed
from werkzeug.utils import secure_filename
from wtforms.validators import Email
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
from bson import ObjectId
from PIL import Image
from io import BytesIO
import numpy as np
import secrets
import os
import facetrk as ftk;
import face_recognition
import cv2
import json
import base64

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/facemeet'
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = 'UserImages'
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
faceDetector = ftk.facedetector()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, user_dict):
        self.id = str(user_dict['_id'])
        self.username = user_dict['username']
        self.image = user_dict.get('image', None)

@login_manager.user_loader
def load_user(user_id):
    user_dict = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user_dict:
        return User(user_dict)
    return None


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "username"})
    email = EmailField(validators=[InputRequired(), Length(min=6, max=50)], render_kw={"placeholder": "email"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "password"})
    image = HiddenField(validators=[InputRequired()])
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = mongo.db.users.find_one({'username': username.data})
        if existing_user_username:
            flash("The Username already exists. Please choose a different one.")
            raise ValidationError("The Username already exists. Please choose a different one.")

    def validate_email(self, email):
        existing_user_email = mongo.db.users.find_one({'email': email.data})
        if existing_user_email:
            flash("An account with this email already exists.")
            raise ValidationError("An account with this email already exists.")

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "password"})
    submit = SubmitField("Login")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_dict = mongo.db.users.find_one({'username': form.username.data.lower()})
        if user_dict and bcrypt.check_password_hash(user_dict['password'], form.password.data):
            user = User(user_dict)
            login_user(user)
            return render_template('lobby.html', form=form)
        else:
            flash("Incorrect credentials")
            return render_template('login.html', form=form)

    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        if form.image.data:
            image = form.image.data
            filename = secure_filename(f"{form.username.data.lower()}.{image.filename.split('.')[-1]}")
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            img = cv2.imread(image_path)
            if img is not None and img.size>0:
                img, bbox = faceDetector.find_faces(img)
                if img is not None and img.size > 0:
                    new_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    face_encodings = face_recognition.face_encodings(new_img)
                    if face_encodings:
                        face_encoding = face_encodings[0]
                    else:
                        flash('No face detected. Please make sure your face is clearly visible and try again.')
                        return render_template('register.html', form=form)

        print(face_encoding)
        mongo.db.users.insert_one({'username': form.username.data.lower(), 'email': form.email.data, 'password': hashed_password, 'image': image_path if form.image.data else None, 'face_encoding': face_encoding.tolist() if face_encoding is not None else None})
        print('User added to the database')
        user_dict = mongo.db.users.find_one({'username': form.username.data.lower()})
        user = User(user_dict)
        login_user(user)
        return redirect(url_for('lobby'))
    return render_template('register.html', form=form)

@app.route('/findUser',methods=['POST'])
def findUser():
    try:
        data = request.get_json()
        username = data['username']
        password = data['password']
        print(username + ' ' + password)
        user_dict = mongo.db.users.find_one({'username':username})
        if user_dict:
            return jsonify({'message':'found user'})
        else :
            flash("No user found")
            return jsonify({'message':'No user found'})
    except Exception as e:
        return jsonify({'message': 'Error processing image', 'error': str(e)})

        

@app.route('/verifyFace', methods=['POST'])
def verifyFace():
    try:
        data = request.get_json()
        image_data = data.get('image')
        username = data.get('name')
        user_dict = mongo.db.users.find_one({'username': username.lower()})

        if user_dict is None:
            flash("User not found")
            return redirect(url_for('login'))

        user_encoding = user_dict['face_encoding']

        if image_data:
            image_bytes = base64.b64decode(image_data.split(',')[1])
            img = Image.open(BytesIO(image_bytes))
            img = np.array(img)

            if img is not None and img.shape[0] > 0 and img.shape[1] > 0:  
                img, bbox = faceDetector.find_faces(img)
                if img is None:
                    return jsonify({'error': 'No Face Detected'})
                if img.size > 0: 
                    new_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    face_encodings = face_recognition.face_encodings(new_img)
                    # _, processed_image_bytes = cv2.imencode('.png', new_img)
                    # processed_image_base64 = base64.b64encode(processed_image_bytes).decode('utf-8')
                    if face_encodings:
                        face_encoding = face_encodings[0]
                    else:
                        return jsonify({'error':'Image not Accepted'})
                    
                    faceMatch = face_recognition.compare_faces([user_encoding],face_encoding,0.4)
                    if faceMatch[0]:
                        source = data.get('source', 'login') 
                        if source == 'login':
                            return jsonify({'message': 'Face Verified', 'faceMatch': True, 'redirect': 'lobby'})
                        elif source == 'lobby':
                            return jsonify({'message': 'Face Verified', 'faceMatch': True, 'redirect': 'room'})
                        else:
                            return jsonify({'message': 'Invalid source for face verification'})
                    else:
                        return jsonify({'message': 'Face not verified', 'faceMatch': False, 'redirect': 'login'})  # Redirect to login for unsuccessful face match
                  
            else:
                return jsonify({'msg': 'Empty Image Array'})

        else:
            return jsonify({'error': 'No image data found'})
    except Exception as e:
        return jsonify({'message': 'Error processing image', 'error': str(e)})

def generate_room_id():
    return secrets.token_urlsafe(8)

@app.route('/detectFace', methods=['POST'])
def detect_face():
    try:
        data = request.get_json()
        image_data = data.get('image')
        if image_data:
            image_bytes = base64.b64decode(image_data.split(',')[1])
            img = Image.open(BytesIO(image_bytes))
            img = np.array(img)

            if img is not None and img.shape[0] > 0 and img.shape[1] > 0:  
                img, bbox = faceDetector.find_faces(img)
                if img is None:
                    return jsonify({'error': 'No Face Detected'})
                if img.size > 0: 
                    new_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    face_encodings = face_recognition.face_encodings(new_img)
                    _, processed_image_bytes = cv2.imencode('.png', new_img)
                    processed_image_base64 = base64.b64encode(processed_image_bytes).decode('utf-8')
                    if face_encodings:
                        face_encoding = face_encodings[0]
                    else:
                        return jsonify({'error':'Image not Accepted','processed_image':processed_image_base64})
                    return jsonify({'message': 'Image accepted', 'processed_image': processed_image_base64})
                  
            else:
                return jsonify({'msg': 'Empty Image Array'})

        else:
            return jsonify({'error': 'No image data found'})
    except Exception as e:
        return jsonify({'message': 'Error processing image', 'error': str(e)})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/lobby')
@login_required
def lobby():
    return render_template('lobby.html')

@app.route('/room/<int:room_id>')
@login_required
def room(room_id):
    return render_template('room.html', room_id=room_id)

if __name__ == '__main__':
    app.run(debug=True)
