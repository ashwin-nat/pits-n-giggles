from flask import Flask, render_template, jsonify
import random

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("hud.html")

@app.route("/data")
def get_data():
    # Simulated HUD data (replace with real telemetry data)
    return jsonify({"speed": random.randint(100, 300), "gear": random.randint(1, 8)})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
