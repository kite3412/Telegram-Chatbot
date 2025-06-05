from flask import Flask, request, render_template
import requests
from google import genai
import os
from dotenv import load_dotenv
import sqlite3
import datetime

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
gemini_telegram_token = os.getenv("GEMINI_TELEGRAM_TOKEN")

gemini_client = genai.Client(api_key=gemini_api_key)
gemini_model = "gemini-2.0-flash"

app = Flask(__name__)

first_time = 1

@app.route("/", methods=["Get", "Post"])
def index():
    return(render_template("index.html"))

@app.route("/main", methods=["Get", "Post"])
def main():
    global first_time
    if first_time == 1:
        name = request.form.get("q")
        t = datetime.datetime.now()
        conn = sqlite3.connect('user.db')
        c = conn.cursor()
        c.execute("insert into users(name, timestamp) values(?,?)", (name, t))
        conn.commit()
        c.close()
        conn.close()
        first_time = 0
    return(render_template("main.html"))

@app.route("/user_log",methods=["GET","POST"])
def user_log():
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute("select * from users")
    logs = c.fetchall()
    c.close()
    conn.close()
    return(render_template("user_log.html", logs=logs))

@app.route("/delete_log",methods=["GET","POST"])
def delete_log():
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute("delete from users")
    conn.commit()
    c.close()
    conn.close()
    return(render_template("delete_log.html"))

@app.route("/logout", methods=["Get", "Post"])
def logout():
    global first_time
    first_time = 1
    return(render_template("index.html"))

@app.route("/start_telegram",methods=["GET","POST"])
def start_telegram():

    domain_url = os.getenv('WEBHOOK_URL')

    delete_webhook_url = f"https://api.telegram.org/bot{gemini_telegram_token}/deleteWebhook"
    requests.post(delete_webhook_url, json={"url": domain_url, "drop_pending_updates": True})
    
    set_webhook_url = f"https://api.telegram.org/bot{gemini_telegram_token}/setWebhook?url={domain_url}/telegram"
    webhook_response = requests.post(set_webhook_url, json={"url": domain_url, "drop_pending_updates": True})
    print('webhook:', webhook_response)
    if webhook_response.status_code == 200:
        return(render_template("telegram_success.html"))
    else:
        return(render_template("telegram_fail.html"))

@app.route("/telegram",methods=["GET","POST"])
def telegram():
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"]

        if str.lower(text) == "/start":
            r_text = "Welcome to the Chatbot! Start asking your first question or type *quit* to exit."
        elif str.lower(text) == "quit":
            r_text = "Thanks you for using the Chatbot, bye."
        else:
            system_prompt = "Reply limits to 100 words"
            prompt = f"{system_prompt}\n\nUser Query: {text}"
            r = gemini_client.models.generate_content(
                model=gemini_model,
                contents=prompt
            )
            r_text = r.text
        
        send_message_url = f"https://api.telegram.org/bot{gemini_telegram_token}/sendMessage"
        requests.post(send_message_url, data={"chat_id": chat_id, "text": r_text, "parse_mode": "Markdown"})
        
    return('ok', 200)

if __name__ == "__main__":
    app.run()