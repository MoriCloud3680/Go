from flask import Flask
from utils import update_after_input

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    update_after_input()   # 명시적으로 호출
    return "GA 모델이 실행되었습니다.", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
