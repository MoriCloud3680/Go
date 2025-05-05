import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# 전역변수로 최근 생성한 회차 기록
last_generated_round = None

# 👉 구글 인증 함수 (이미 사용중인 코드 유지해!)
def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # 환경변수에서 JSON 키 로드
    google_credentials_json = os.getenv('GOOGLE_CREDENTIALS')

    # JSON 문자열을 dict로 파싱
    credentials_dict = json.loads(google_credentials_json)

    # 인증 설정
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)

    return client

# 👉 현재 최신 회차 가져오기 (B2 셀 기준)
def fetch_current_round():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    round_no = sheet.acell('B2').value
    return int(round_no)

# 👉 GA 모델 실행 및 F10 시트 업데이트 (기존 사용 코드 유지!)
def update_after_input():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    f10_sheet = client.open_by_key(sheet_id).worksheet("F10")

    today_date = datetime.now().strftime('%Y-%m-%d')
    round_no = fetch_current_round()
    tag = "GA 자동생성"

    # 여기에 너가 실제 사용하는 GA 로직을 그대로 유지해
    numbers = "01,02,03,04,05"  # GA 생성 로직의 결과값으로 대체!

    f10_sheet.insert_row([today_date, round_no, tag, numbers], 2, value_input_option="USER_ENTERED")

@app.route("/", methods=["GET"])
def home():
    global last_generated_round

    current_round = fetch_current_round()

    if current_round != last_generated_round:
        try:
            update_after_input()
            last_generated_round = current_round
            return f"✅ {current_round}회차 신규 조합 생성 완료.", 200
        except Exception as e:
            return f"❌ GA 모델 실행 중 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ 이미 {current_round}회차 조합 생성 완료됨. 추가 생성하지 않음.", 200

# 👉 디버깅용 추가 라우트 (필요하면 유지)
@app.route("/debug_sheet")
def debug_sheet():
    try:
        client = authenticate_google()
        sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
        sheet = client.open_by_key(sheet_id).worksheet("F10")
        sheet.append_row(["2025-05-05", "999999", "DebugTest", "01,02,03,04,05"], value_input_option="USER_ENTERED")
        return "✅ 직접 추가 성공", 200
    except Exception as e:
        return f"❌ 직접 추가 실패: {str(e)}", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
