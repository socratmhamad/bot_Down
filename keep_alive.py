from flask import Flask,render_template
from threading import Thread
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0',port=8080)


def keep_alive():
    t = Thread(target= run)
    t.start()

        
    )
#threading.Thread(target=app.run, kwargs={'host':'0.0.0.0','port':8080}).start()