# Gemini

from flask import Flask, request, render_template
import google.generativeai as genai
import os
from dotenv import load_dotenv
import sqlite3
import datetime

load_dotenv()

gemini_api_key = os.getenv("gemini_api_key")

genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

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

if __name__ == "__main__":
    app.run()