from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Cortex AI Bot is running!"

def keep_alive():
    t = Thread(target=app.run, args=("0.0.0.0", 8080))
    t.start()
