from flask import Flask
from utils import update_after_input

app = Flask(__name__)

@app.route('/')
def home():
    update_after_input()
    return '추천번호 10개 자동 업데이트 완료!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)  # Render는 포트 10000 추천
