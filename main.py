import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from flask import Flask
import numpy as np
import pandas as pd
from utils import fetch_latest_data, update_predictions, update_status
import joblib
from tensorflow.keras.models import load_model

app = Flask(__name__)

model = load_model('model.keras', compile=False)
scaler = joblib.load('scaler.save')

# 이하 기존 코드 유지

def preprocess(new_numbers):
    moving_avg = pd.Series(new_numbers).rolling(window=5).mean().bfill().values
    diff_numbers = np.diff(new_numbers, prepend=new_numbers[0])
    features = np.column_stack((new_numbers, moving_avg, diff_numbers))
    features_scaled = scaler.transform(features)
    window_size = 20
    return np.array([features_scaled[-window_size:]])

def postprocess(predictions):
    predictions_inverse = []
    for i in range(predictions.shape[1]):
        inverse_scaled = scaler.inverse_transform(
            np.column_stack((predictions[:, i], np.zeros((predictions.shape[0], 2))))
        )[:, 0]
        predictions_inverse.append(inverse_scaled[0])
    predicted_numbers = np.round(predictions_inverse).astype(int)
    predicted_numbers = np.clip(predicted_numbers, 1, 70)
    
    unique_predicted_numbers = []
    for num in predicted_numbers:
        if num not in unique_predicted_numbers:
            unique_predicted_numbers.append(num)
        if len(unique_predicted_numbers) == 10:
            break
    
    while len(unique_predicted_numbers) < 10:
        rand_num = np.random.randint(1, 71)
        if rand_num not in unique_predicted_numbers:
            unique_predicted_numbers.append(rand_num)
            
    return unique_predicted_numbers

@app.route("/", methods=["GET"])
def home():
    round_no, latest_numbers = fetch_latest_data()
    X_input = preprocess(latest_numbers)
    predictions = model.predict(X_input)
    predicted_numbers = postprocess(predictions)
    update_predictions(round_no + 1, predicted_numbers)
    return f"✅ {round_no + 1}회차 예측 완료: {predicted_numbers}", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
