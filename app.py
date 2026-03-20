from flask import Flask, render_template, request, redirect
import sqlite3, requests, os, json, re
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

def get_db():
    return sqlite3.connect("database.db")

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def call_ai(subject, text):
    prompt = f"""
과목: {subject}
암기할 내용: {text}

위 내용을 기억하기 쉽게 재미있는 스토리로 만들어줘.
스토리는 3~5문장으로 작성해줘.
JSON 형식으로만 답해줘. 코드블록 없이 순수 JSON만:
{{
  "story": "여기에 스토리"
}}
"""
    res = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('XAI_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "grok-4-1-fast",
            "max_tokens": 1000,
            "stream": False,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        }
    )

    print("API 응답:", res.json())

    raw = res.json()["choices"][0]["message"]["content"]
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)

@app.route("/", methods=["GET", "POST"])
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM subjects")
    subjects = cur.fetchall()
    conn.close()

    if request.method == "POST":
        subject = request.form["subject"]
        text = request.form["text"]
        result = call_ai(subject, text)
        return render_template("result.html", story=result["story"], subject=subject, text=text)

    return render_template("index.html", subjects=subjects)

@app.route("/subjects", methods=["GET", "POST"])
def subjects():
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        if name.strip():
            cur.execute("INSERT INTO subjects (name) VALUES (?)", (name,))
            conn.commit()

    cur.execute("SELECT id, name FROM subjects")
    data = cur.fetchall()
    conn.close()
    return render_template("subjects.html", subjects=data)

@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM subjects WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/subjects")

if __name__ == "__main__":
    app.run(debug=True)