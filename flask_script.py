from flask import Flask, request
import os
import subprocess
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

SERVER_DIR = str(os.getenv("SERVER_DIR"))
TOKEN = str(os.getenv("MC_LAUNCH_TOKEN"))

@app.route('/start-server', methods=['POST'])
def start_server():
    if request.json.get("token") != TOKEN:
        return "Unauthorized", 403

    try:
        subprocess.Popen(
            ["java", "-Xmx4G", "-Xms2G", "-jar", "server.jar", "nogui"],
            cwd=SERVER_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return "Server started", 200
    except Exception as e:
        return f"Failed to start server: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)