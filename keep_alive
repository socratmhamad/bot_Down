
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1 style="text-align: center; font-family: Arial; margin-top: 50px;">
        ✅ البوت يعمل بنجاح!
    </h1>
    <div style="text-align: center;">
        <a href="https://t.me/YourBot" style="text-decoration: none; color: #0088cc; font-family: Arial;">
            اضغط هنا للدردشة مع البوت
        </a>
    </div>
    """

def run():
    app.run(host='0.0.0.0', port=8080, debug=False)

def keep_alive():
    server = Thread(target=run)
    server.start()
