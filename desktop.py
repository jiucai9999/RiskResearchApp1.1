import webview
import subprocess
import sys
import os
import time

def start_streamlit():
    subprocess.Popen([
        sys.executable, "-m", "streamlit", "run",
        "app.py",
        "--server.headless=true",
        "--server.port=8501",
        "--browser.gatherUsageStats=false"
    ])

if __name__ == "__main__":
    start_streamlit()
    time.sleep(2)  # 等 Streamlit 起服务

    webview.create_window(
        "多品种交易风控与研究系统",
        "http://127.0.0.1:8501",
        width=1200,
        height=800
    )
    webview.start()
