# How to Run the Diabetes App

1. **Set up Python Virtual Environment**
   - Open a command prompt and navigate to the `diabetes_app` directory.
   - Create a virtual environment:
     ```
     python -m venv venv
     ```
   - Activate the virtual environment:
     - On Windows CMD:
       ```
       venv\Scripts\activate
       ```
     - On PowerShell:
       ```
       .\venv\Scripts\Activate.ps1
       ```

2. **Install Dependencies**
   - With the virtual environment activated, run:
     ```
     pip install -r requirements.txt
     ```

3. **Set up MySQL Database**
   - Install and start the MySQL server if not already installed.
   - Login to MySQL and create the database and user:
     ```sql
     CREATE DATABASE diabetes_app;
     CREATE USER 'root'@'localhost' IDENTIFIED BY 'nopass';
     GRANT ALL PRIVILEGES ON diabetes_app.* TO 'root'@'localhost';
     FLUSH PRIVILEGES;
     ```
   - Verify MySQL server is running and accessible.

4. **Run the Flask Application**
   - In the activated virtual environment and inside `diabetes_app` directory, run:
     ```
     python app.py
     ```
   - This starts the Flask development server at http://127.0.0.1:5000/

5. **Access the Web App**
   - Open your browser and go to:
     ```
     http://127.0.0.1:5000/
     ```

---

Ensure Tesseract OCR is installed on your system at:
```
C:\Program Files\Tesseract-OCR\tesseract.exe
```
as required by the app for prescription image text extraction.

If you encounter any issues, please verify the above steps, especially MySQL connectivity and Python environment setup.
