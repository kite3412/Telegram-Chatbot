# Gemini

from flask import Flask, request, render_template
import requests
import google.generativeai as genai1
from google import genai
import os
from dotenv import load_dotenv
import sqlite3
import datetime

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
gemini_telegram_token = os.getenv("GEMINI_TELEGRAM_TOKEN")

genai1.configure(api_key=gemini_api_key)
model = genai1.GenerativeModel("gemini-2.0-flash")
genmini_client = genai.Client(api_key=gemini_api_key)
genmini_model = "gemini-2.0-flash"

app = Flask(__name__)

first_time = 1

@app.route("/", methods=["Get", "Post"]) # start point
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

@app.route("/gemini",methods=["GET","POST"])
def gemini():
    return(render_template("gemini.html"))

@app.route("/gemini_reply",methods=["GET","POST"])
def gemini_reply():
    q = request.form.get("q")
    r = model.generate_content(q)
    r = r.text
    return(render_template("gemini_reply.html", r=r))

@app.route("/user_log",methods=["GET","POST"])
def user_log():
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute("select * from users")
    r=""
    for row in c:
        r= r+str(row)
    c.close()
    conn.close()
    return(render_template("user_log.html", r=r))

@app.route("/delete_log",methods=["GET","POST"])
def delete_log():
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute("delete from users")
    conn.commit()
    c.close()
    conn.close()
    return(render_template("delete_log.html"))

@app.route("/logout", methods=["Get", "Post"]) # start point
def logout():
    global first_time
    first_time = 1
    return(render_template("index.html"))

@app.route("/paynow",methods=["GET","POST"])
def paynow():
    return(render_template("paynow.html"))

@app.route("/prediction",methods=["GET","POST"])
def prediction():
    return(render_template("prediction.html"))

@app.route("/prediction_reply",methods=["GET","POST"])
def prediction_reply():
    q = float(request.form.get("q"))
    return(render_template("prediction_reply.html", r=90.2 + (-50.6*q)))

@app.route("/start_telegram",methods=["GET","POST"])
def start_telegram():

    domain_url = os.getenv('WEBHOOK_URL')

    # The following line is used to delete the existing webhook URL for the Telegram bot
    delete_webhook_url = f"https://api.telegram.org/bot{gemini_telegram_token}/deleteWebhook"
    requests.post(delete_webhook_url, json={"url": domain_url, "drop_pending_updates": True})
    
    # Set the webhook URL for the Telegram bot
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
        # Extract the chat ID and message text from the update
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"]

        if text == "/start":
            r_text = "Welcome to the Chatbot! Start asking your questions or type *quit* to exit."
        elif text == "quit":
            r_text = "Thanks you for using the Chatbot, bye."
        else:
            # Process the message and generate a response
            system_prompt = "Reply limits to 50 words"
            prompt = f"{system_prompt}\n\nUser Query: {text}"
            r = genmini_client.models.generate_content(
                model=genmini_model,
                contents=prompt
            )
            r_text = r.text
        
        # Send the response back to the user
        send_message_url = f"https://api.telegram.org/bot{gemini_telegram_token}/sendMessage"
        requests.post(send_message_url, data={"chat_id": chat_id, "text": r_text, parse_mode: "Markdown"})
    # Return a 200 OK response to Telegram
    # This is important to acknowledge the receipt of the message
    # and prevent Telegram from resending the message
    # if the server doesn't respond in time
    return('ok', 200)

if __name__ == "__main__":
    app.run()