from flask import Flask, request
import os
import subprocess
from dotenv import load_dotenv
from threading import Thread

load_dotenv()

app = Flask(__name__)

SERVER_DIR = str(os.getenv("SERVER_DIR"))
TOKEN = str(os.getenv("MC_LAUNCH_TOKEN"))

print("SERVER_DIR =", SERVER_DIR)
print("TOKEN =", TOKEN)

def launch_server():
    try:
        print(f"[Thread] Launching server from: {SERVER_DIR}")
        subprocess.Popen(
            ["cmd.exe", "/c", "run.bat"],
            cwd=SERVER_DIR,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print("[Thread] Server process launched.")
    except Exception as e:
        print(f"[Thread ERROR] Failed to start server: {e}")

@app.route('/start-server', methods=['POST'])
def start_server():
    print("Received /start-server POST")
    data = request.json
    print("Request JSON:", data)

    if data.get("token") != TOKEN:
        print("Invalid token:", data.get("token"))
        return "Unauthorized", 403

    Thread(target=launch_server).start()
    return "Server starting...", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, threaded=True)