import os
import sys
import re
import time
import psutil
import signal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QTableWidget, QTabBar,
    QWidget, QLineEdit, QPushButton, QTabWidget, QTreeView, QTableView, QHeaderView,
    QAbstractItemView, QMenu, QAction, QTableWidgetItem, QTreeWidget, QTreeWidgetItem,
    QLabel, QTextEdit,
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer, QItemSelectionModel, QPoint, Qt, QSize
from process import Proc
from filter_process import filter_process_by_name
from process_tree import get_process_tree
from PyQt5.QtGui import QPainter, QColor, QFont
from itertools import tee
from functools import reduce


class SettingTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_settings_tab()

    def init_settings_tab(self):
        layout = QVBoxLayout(self)

        # 창 제목
        title_label = QLabel("환경변수 설정")  # 상단 제목
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title_label)

        # 변수, 값 테이블
        self.env_table = QTableWidget(0, 2)  # 0행, 2열 테이블
        self.env_table.setHorizontalHeaderLabels(["변수", "값"])  # 열 이름
        self.env_table.horizontalHeader().setStretchLastSection(True)  # 마지막 열 확장
        self.env_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # 열 비율 조정
        self.env_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 편집 비활성화
        self.env_table.setSelectionBehavior(QTableView.SelectRows)  # 행 선택
        layout.addWidget(self.env_table)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        create_button = QPushButton("생성")
        modify_button = QPushButton("변경")
        delete_button = QPushButton("삭제")

        # 버튼 추가
        button_layout.addWidget(create_button)
        button_layout.addWidget(modify_button)
        button_layout.addWidget(delete_button)

        # 버튼 레이아웃 추가
        layout.addLayout(button_layout)

