import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Input, LSTM, Dense, Bidirectional, Attention
from utils import authenticate_google

def train_and_update():
    # Google Sheets 인증 및 데이터 로딩
    client = authenticate_google()
    sheet_url = 'https://docs.google.com/spreadsheets/d/1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo/edit#gid=0'
    sheet = client.open_by_url(sheet_url).worksheet('ActualNumbers')
    data = pd.DataFrame(sheet.get_all_records())

    numbers_series = data['ActualNumbers'].apply(lambda x: list(map(int, x.split(','))))
    flattened_numbers = np.array([num for sublist in numbers_series for num in sublist])

    moving_avg = pd.Series(flattened_numbers).rolling(window=5).mean().bfill()
    diff_numbers = np.diff(flattened_numbers, prepend=flattened_numbers[0])

    features = np.column_stack((flattened_numbers, moving_avg, diff_numbers))

    # 데이터 스케일링
    scaler = MinMaxScaler()
    features_scaled = scaler.fit_transform(features)

    window_size = 20
    X, y = [], []
    for i in range(len(features_scaled) - window_size):
        X.append(features_scaled[i:i + window_size])
        y.append(features_scaled[i + window_size, 0])

    X, y = np.array(X), np.array(y)

    # 모델 정의 및 학습
    input_layer = Input(shape=(window_size, features_scaled.shape[1]))
    lstm_out = Bidirectional(LSTM(128, activation='relu', return_sequences=True))(input_layer)
    attention_out = Attention()([lstm_out, lstm_out])
    attention_last_step = attention_out[:, -1, :]
    dense_out = Dense(64, activation='relu')(attention_last_step)
    output_layer = Dense(1)(dense_out)

    model = Model(inputs=input_layer, outputs=output_layer)
    model.compile(optimizer='adam', loss='mse')
    model.fit(X, y, epochs=50, batch_size=32)

    # 모델 저장
    model.save('model/model.h5')

    # 예측 수행
    predictions = model.predict(X)
    predictions_inverse = scaler.inverse_transform(
        np.column_stack((predictions, np.zeros((len(predictions), 2))))
    )[:, 0]

    # Google Sheets에 예측값 업데이트
    predicted_sheet = client.open_by_url(sheet_url).worksheet('Predicted')
    latest_round = int(data['Round'].iloc[-1]) + 1
    numbers_str = ",".join(map(str, predictions_inverse.flatten().round().astype(int)[:10]))
    predicted_sheet.append_row([latest_round, numbers_str], value_input_option='USER_ENTERED')

    # 상태 업데이트
    status_sheet = client.open_by_url(sheet_url).worksheet('Status')
    status_sheet.update('A2', latest_round)
