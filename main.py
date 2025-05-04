from flask import Flask
from utils import run_ga_and_save

app = Flask(__name__)

@app.route('/')
def home():
    run_ga_and_save()
    return '번호 생성 완료!'

if __name__ == '__main__':
    app.run()
