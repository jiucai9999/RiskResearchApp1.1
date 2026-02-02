import subprocess
import sys
import os

def main():
    # 防止 PyInstaller 重复拉起
    if os.environ.get("STREAMLIT_LAUNCHED") == "1":
        return
    os.environ["STREAMLIT_LAUNCHED"] = "1"

    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(base_dir, "app.py")

    subprocess.Popen(
        [
            sys.executable,
            "-m", "streamlit", "run", app_path,

            # ===== C：安全与桌面模式关键参数 =====
            "--server.address=127.0.0.1",
            "--server.port=8501",
            "--server.headless=true",
            "--server.runOnSave=false",
            "--server.fileWatcherType=none",
            "--browser.gatherUsageStats=false",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

if __name__ == "__main__":
    main()