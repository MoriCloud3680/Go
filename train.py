# Colab에서 Google Sheets 연동 Attention LSTM 모델 세부 튜닝 (Render 환경변수 사용)

# 패키지 설치
!pip install numpy pandas statsmodels tensorflow keras gspread oauth2client

# 라이브러리 임포트
import os
import json
import numpy as np
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, LSTM, Dense, Bidirectional, Attention

# Google Sheets 인증 (Render의 환경변수 사용)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
client = gspread.authorize(creds)

# Google Sheets 데이터 로딩
sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo/edit#gid=0').worksheet('ActualNumbers')
data = sheet.get_all_records()
df = pd.DataFrame(data)

# 데이터 전처리 및 특성공학
numbers_series = df['ActualNumbers'].apply(lambda x: list(map(int, x.split(','))))
flattened_numbers = np.array([num for sublist in numbers_series for num in sublist])

moving_avg = pd.Series(flattened_numbers).rolling(window=5).mean().bfill()
diff_numbers = np.diff(flattened_numbers, prepend=flattened_numbers[0])

features = np.column_stack((flattened_numbers, moving_avg, diff_numbers))

# 데이터 스케일링
scaler = MinMaxScaler()
features_scaled = scaler.fit_transform(features)

# 튜닝된 파라미터
window_size = 20

X, y = [], []
for i in range(len(features_scaled) - window_size):
    X.append(features_scaled[i:i + window_size])
    y.append(features_scaled[i + window_size, 0])

X, y = np.array(X), np.array(y)

# 세부 튜닝된 Attention LSTM 모델
input_layer = Input(shape=(window_size, features_scaled.shape[1]))
lstm_out = Bidirectional(LSTM(128, activation='relu', return_sequences=True))(input_layer)
attention_out = Attention()([lstm_out, lstm_out])
attention_last_step = attention_out[:, -1, :]
dense_out = Dense(64, activation='relu')(attention_last_step)
output_layer = Dense(1)(dense_out)

model = Model(inputs=input_layer, outputs=output_layer)
model.compile(optimizer='adam', loss='mse')

# 튜닝된 학습 조건
model.fit(X, y, epochs=50, batch_size=32)

# 예측 및 Google Sheets에 업데이트
predictions = model.predict(X)
predictions_inverse = scaler.inverse_transform(np.column_stack((predictions, np.zeros((len(predictions), 2)))))[:, 0]

predicted_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo/edit#gid=0').worksheet('Predicted')
latest_round = int(df['Round'].iloc[-1]) + 1
numbers_str = ",".join(map(str, predictions_inverse.flatten().round().astype(int)[:10]))
predicted_sheet.append_row([latest_round, numbers_str], value_input_option='USER_ENTERED')

status_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo/edit#gid=0').worksheet('Status')
status_sheet.update('A2', latest_round)

print("Optimized Attention LSTM Predictions:", predictions_inverse.flatten()[:20])
