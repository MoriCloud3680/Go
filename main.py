from flask import Flask
import os
from utils import run_ga_and_save

app = Flask(__name__)

@app.route('/')
def home():
    run_ga_and_save()
    return '번호 생성 완료!'

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # 이 부분 필수 추가!
    app.run(host='0.0.0.0', port=port)
