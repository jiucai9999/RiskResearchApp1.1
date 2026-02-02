import sys
import os
import sqlite3
import json
import statistics
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QComboBox, QDoubleSpinBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QGroupBox
)

# ===============================
# 数据库
# ===============================
APP_NAME = "RiskResearchApp"
db_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", APP_NAME)
os.makedirs(db_dir, exist_ok=True)
DB_PATH = os.path.join(db_dir, "trades.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time TEXT,
    product TEXT,
    entry REAL,
    stop REAL,
    target REAL,
    position REAL,
    rr REAL,
    result REAL
)
""")
conn.commit()

# ===============================
# 主窗口
# ===============================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多品种交易风控与研究系统")
        self.resize(1000, 700)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # ===== 品类 =====
        top = QHBoxLayout()
        top.addWidget(QLabel("交易品类"))

        self.product = QComboBox()
        self.product.addItems(["黄金", "股票", "基金", "ETF"])
        top.addWidget(self.product)

        layout.addLayout(top)

        # ===== 风控 =====
        risk_box = QGroupBox("下单前风控")
        risk_layout = QHBoxLayout(risk_box)

        self.entry = QDoubleSpinBox()
        self.entry.setPrefix("入场 ")
        self.entry.setMaximum(1e9)

        self.stop = QDoubleSpinBox()
        self.stop.setPrefix("止损 ")
        self.stop.setMaximum(1e9)

        self.target = QDoubleSpinBox()
        self.target.setPrefix("止盈 ")
        self.target.setMaximum(1e9)

        risk_layout.addWidget(self.entry)
        risk_layout.addWidget(self.stop)
        risk_layout.addWidget(self.target)

        self.calc_btn = QPushButton("计算风控")
        self.calc_btn.clicked.connect(self.calc_risk)
        risk_layout.addWidget(self.calc_btn)

        layout.addWidget(risk_box)

        # ===== 结果 =====
        self.result_label = QLabel("仓位: - | 盈亏比: -")
        layout.addWidget(self.result_label)

        # ===== 保存 =====
        self.save_btn = QPushButton("保存交易")
        self.save_btn.clicked.connect(self.save_trade)
        layout.addWidget(self.save_btn)

        # ===== 表格 =====
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["时间", "品类", "入场", "止损", "止盈", "盈亏"]
        )
        layout.addWidget(self.table)

        self.load_recent()

    def calc_risk(self):
        entry = self.entry.value()
        stop = self.stop.value()
        target = self.target.value()

        if entry == stop:
            QMessageBox.warning(self, "错误", "止损不能等于入场")
            return

        loss = abs(entry - stop)
        position = 1000 / loss
        rr = abs(target - entry) / loss

        self.result_label.setText(f"仓位: {position:.2f} | 盈亏比: {rr:.2f}")
        self._position = position
        self._rr = rr

    def save_trade(self):
        cursor.execute(
            """
            INSERT INTO trades
            (time, product, entry, stop, target, position, rr, result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.product.currentText(),
                self.entry.value(),
                self.stop.value(),
                self.target.value(),
                getattr(self, "_position", 0),
                getattr(self, "_rr", 0),
                0
            )
        )
        conn.commit()
        self.load_recent()

    def load_recent(self):
        self.table.setRowCount(0)
        for row in cursor.execute(
            "SELECT time, product, entry, stop, target, result FROM trades ORDER BY id DESC LIMIT 10"
        ):
            r = self.table.rowCount()
            self.table.insertRow(r)
            for c, v in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))


# ===============================
# 启动
# ===============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
