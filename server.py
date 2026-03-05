from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import os
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 사용자별 사용기록 저장 (DB로 교체 가능)
users = {}

TRIAL_LIMIT = 15
TRIAL_DAYS = 7

def check_user(email):
    now = datetime.now()

    if email not in users:
        users[email] = {
            "count": 0,
            "start": now
        }

    user = users[email]

    # 7일 초과 체크
    if now - user["start"] > timedelta(days=TRIAL_DAYS):
        return False, "⛔ 체험 기간 7일이 종료되었습니다.\n\n👉 지금 바로 정식 구독으로 업그레이드하세요."

    # 15회 초과 체크
    if user["count"] >= TRIAL_LIMIT:
        return False, "⛔ 무료 15회 사용이 모두 소진되었습니다.\n\n🚀 업그레이드하여 무제한 창작을 시작하세요."

    user["count"] += 1
    return True, None


@app.route("/generate-novel", methods=["POST"])
def generate_novel():
    try:
        data = request.json
        topic = data.get("topic")
        email = data.get("email")

        if not topic or not email:
            return jsonify({"error": "필수값 누락"}), 400

        allowed, message = check_user(email)
        if not allowed:
            return jsonify({"error": message}), 403

        prompt = f"""
당신은 노벨 문학상 수상급 소설가입니다.

주제: {topic}

요구사항:
- 강렬한 도입
- 감정 묘사 깊이
- 생생한 대화
- 반전 구조
- 최소 1200자 이상
- 마지막에 여운

전문 작가 수준으로 작성하십시오.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9
        )

        result = response.choices[0].message.content

        return jsonify({
            "result": result,
            "remaining": TRIAL_LIMIT - users[email]["count"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return "Novel Generator Server Running"
