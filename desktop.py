import webview
import threading
import time
import launcher

def start_streamlit():
    launcher.main()

if __name__ == "__main__":
    threading.Thread(target=start_streamlit, daemon=True).start()
    time.sleep(2)  # 等 Streamlit 启动
    webview.create_window(
        "多品种交易风控与研究系统",
        "http://127.0.0.1:8501",
        width=1200,
        height=800
    )
    webview.start()