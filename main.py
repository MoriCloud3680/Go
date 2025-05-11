from flask import Flask
from train import train_and_update  # 수정된 import 문

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    try:
        train_and_update()
        return "✅ 모델 학습 및 업데이트 완료", 200
    except Exception as e:
        return f"❌ 오류 발생: {str(e)}", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
