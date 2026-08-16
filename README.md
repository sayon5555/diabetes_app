# Diabetes Prediction App

A Flask web application for predicting diabetes risk based on user input or prescription OCR.

## Features

- User registration and login
- Manual data entry for prediction
- Prescription image upload with OCR
- Machine learning model for risk assessment
- Food suggestions based on risk category
- Database storage of predictions

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Install Tesseract OCR (required for prescription image processing):
   - **Windows**: Install via winget:
     ```
     winget install --id UB-Mannheim.TesseractOCR
     ```
   - **macOS**: Install via Homebrew:
     ```
     brew install tesseract
     ```
   - **Linux**: Install via package manager:
     ```
     sudo apt-get install tesseract-ocr  # Ubuntu/Debian
     sudo yum install tesseract          # CentOS/RHEL
     ```

3. Train the model:
   ```
   python train_model.py
   ```

4. Set up MySQL database:
   - Create a database named `diabetes_app`
   - Update DB credentials in `app.py`

5. Run the app:
   ```
   python app.py
   ```

## Usage

- Register/Login
- Upload prescription or enter data manually
- View prediction and food suggestions

## Technologies

- Flask
- SQLAlchemy
- Scikit-learn
- Tesseract OCR
- Bootstrap (for styling)
