import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib
import os

# Load data
data = pd.read_csv('diabetes.csv')

# Features and target
X = data.drop('Outcome', axis=1)
y = data['Outcome']

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Pipeline
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('classifier', RandomForestClassifier(random_state=42))
])

# Train
pipeline.fit(X_train, y_train)

# Save model
model_bundle = {
    'pipeline': pipeline,
    'feature_names': list(X.columns)
}

os.makedirs('models', exist_ok=True)
joblib.dump(model_bundle, 'models/model.pkl')

print("Model trained and saved.")
