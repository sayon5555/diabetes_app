# app.py
import os
import json
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth

from flask_sqlalchemy import SQLAlchemy
import joblib
import numpy as np
import pandas as pd
import pytesseract
from PIL import Image

# Configure Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

from utils import parse_prescription_text, probability_to_category, suggest_foods

# === Config ===
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(APP_ROOT, "models", "model.pkl")
UPLOAD_FOLDER = os.path.join(APP_ROOT, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = "replace_this_with_a_strong_random_key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)



# === MySQL / SQLAlchemy config - change user/password/host/db ===
DB_USER = "root"
DB_PASS = "nopass"
DB_HOST = "localhost"
DB_NAME = "diabetes_app"
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# === DB models ===
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True)
    password_hash = db.Column(db.String(255), nullable=False)

class Record(db.Model):
    __tablename__ = 'records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    input_json = db.Column(db.Text)
    prescription_text = db.Column(db.Text)
    prediction_prob = db.Column(db.Float)
    category = db.Column(db.String(20))
    suggested_foods = db.Column(db.Text)

# === Load model ===
model_bundle = joblib.load(MODEL_PATH)
pipeline = model_bundle['pipeline']
feature_names = model_bundle['feature_names']

# Helper: require login decorator (simple)
def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')


# === Signup/Login ===
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form.get('email')
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
            return redirect(url_for('signup'))
        user = User(username=username, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash("Signup success. Please login.", "success")
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/bmi_calculator')
@login_required
def bmi_calculator():
    return render_template('bmi_calculator.html')

# Upload prescription image
@app.route('/upload', methods=['GET','POST'])
@login_required
def upload():
    if request.method == 'POST':
        f = request.files.get('prescription')
        if not f:
            flash("No file uploaded", "warning")
            return redirect(url_for('upload'))
        filename = secure_filename(f.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(filepath)
        # Run OCR
        try:
            text = pytesseract.image_to_string(Image.open(filepath))
        except Exception as e:
            text = ''
            flash("OCR processing failed: " + str(e), "danger")
        # parse
        parsed = parse_prescription_text(text)

        # Check for explicit risk mentions in the text
        text_lower = text.lower()
        if 'very high' in text_lower or 'veryhigh' in text_lower:
            prob = 0.95
            category = "Very High Risk"
            feats = {}  # Empty features for explicit risk mentions
        elif 'high' in text_lower and 'risk' in text_lower:
            prob = 0.85
            category = "High Risk"
            feats = {}  # Empty features for explicit risk mentions
        elif 'medium' in text_lower and 'risk' in text_lower:
            prob = 0.55
            category = "Medium Risk"
            feats = {}  # Empty features for explicit risk mentions
        elif 'low' in text_lower and 'risk' in text_lower:
            prob = 0.25
            category = "Low Risk"
            feats = {}  # Empty features for explicit risk mentions
        else:
            # Try to map parsed values to model features (best-effort)
            # We'll build a feature vector with zeros for missing features
            feats = {}
            # default all features to 0
            for fn in feature_names:
                feats[fn] = 0.0

            # Enhanced mapping from parsed data to model features
            mapping = {
                'glucose': ['glucose'],
                'hba1c': ['hba1c', 'a1c'],
                'blood_pressure': ['bloodpressure', 'bp'],
                'bmi': ['bmi'],
                'age': ['age'],
                'insulin': ['insulin'],
                'skin_thickness': ['skinthickness', 'skin_thickness'],
                'pregnancies': ['pregnancies', 'pregnancy'],
                'diabetes_pedigree_function': ['diabetespedigreefunction', 'pedigree']
            }

            for parsed_key, model_keys in mapping.items():
                if parsed_key in parsed:
                    value = parsed[parsed_key]
                    # Handle blood pressure tuple
                    if parsed_key == 'blood_pressure' and isinstance(value, tuple):
                        # Use systolic pressure for BloodPressure feature
                        value = value[0]

                    for fn in feature_names:
                        fn_lower = fn.lower().replace(' ', '')
                        if any(model_key in fn_lower for model_key in model_keys):
                            feats[fn] = float(value)
                            break

            # Build dataframe and predict
            X = pd.DataFrame([feats], columns=feature_names)
            prob = float(pipeline.predict_proba(X)[:,1][0])
            category = probability_to_category(prob)
        foods = suggest_foods(category)
        # Save record
        rec = Record(
            user_id = session['user_id'],
            input_json = json.dumps(feats),
            prescription_text = text,
            prediction_prob = prob,
            category = category,
            suggested_foods = json.dumps(foods)
        )
        db.session.add(rec)
        db.session.commit()
        return render_template('result.html', prob=prob, category=category, foods=foods)
    return render_template('upload.html')

# Manual entry (form)
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/manual', methods=['GET', 'POST'])
@login_required
def manual():
    if request.method == 'POST':
        # read form fields; we read whatever numeric inputs named same as feature names
        input_vals = {}
        errors = []
        all_zero = True

        # Validation ranges for each feature
        validation_ranges = {
            'Pregnancies': (0, 20),
            'Glucose': (0, 500),
            'BloodPressure': (0, 300),
            'SkinThickness': (0, 100),
            'Insulin': (0, 1000),
            'BMI': (0, 100),
            'DiabetesPedigreeFunction': (0, 2.5),
            'Age': (0, 120),
            'HbA1c': (0, 20)
        }

        for fn in feature_names:
            v = request.form.get(fn, '').strip()
            if not v:
                input_vals[fn] = 0.0
                continue
            try:
                val = float(v)
                if fn in validation_ranges:
                    min_val, max_val = validation_ranges[fn]
                    if not (min_val <= val <= max_val):
                        errors.append(f"{fn}: Value {val} is out of range ({min_val}-{max_val})")
                        input_vals[fn] = 0.0
                    else:
                        input_vals[fn] = val
                        if val != 0:
                            all_zero = False
                else:
                    input_vals[fn] = val
                    if val != 0:
                        all_zero = False
            except ValueError:
                errors.append(f"{fn}: Invalid number format '{v}'")
                input_vals[fn] = 0.0

        if errors:
            for error in errors:
                flash(error, "danger")
            return redirect(url_for('manual'))

        if all_zero:
            flash("Warning: All values are zero. Prediction may not be accurate.", "warning")

        X = pd.DataFrame([input_vals], columns=feature_names)
        prob = float(pipeline.predict_proba(X)[:,1][0])
        category = probability_to_category(prob)
        foods = suggest_foods(category)

        rec = Record(
            user_id = session['user_id'],
            input_json = json.dumps(input_vals),
            prescription_text = None,
            prediction_prob = prob,
            category = category,
            suggested_foods = json.dumps(foods)
        )
        db.session.add(rec)
        db.session.commit()
        return render_template('result.html', prob=prob, category=category, foods=foods)
    # GET -> display manual entry form (with feature inputs)
    return render_template('manual_form.html', feature_names=feature_names)

if __name__ == '__main__':
    # create tables if not exists
    with app.app_context():
        db.create_all()
    app.run(debug=True)
