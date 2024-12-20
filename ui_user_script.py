import os
import sys
import re
import time
import psutil
import signal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QTableWidget, QTabBar,
    QWidget, QLineEdit, QPushButton, QTabWidget, QTreeView, QTableView, QHeaderView,
    QAbstractItemView, QMenu, QAction, QTableWidgetItem, QLabel, QTextEdit, QFileDialog
)

from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer, QItemSelectionModel, QPoint, Qt, QSize
from process import Proc
from filter_process import filter_process_by_name
from process_tree import get_process_tree
from PyQt5.QtGui import QPainter, QColor, QFont
from itertools import tee

from user_script_runner import run_user_script


class UserDefinedScriptTab(QWidget):
    def __init__(self):
        self.file_path = 'Unknown'

        super().__init__()
        self.init_user_script_tab()

    def init_user_script_tab(self):
        layout = QVBoxLayout(self)

        button_layout = QHBoxLayout()

        new_button = QPushButton("new")
        new_button.clicked.connect(self.new_file)
        button_layout.addWidget(new_button)

        open_button = QPushButton("open")
        open_button.clicked.connect(self.open_file)
        button_layout.addWidget(open_button)

        save_button = QPushButton("save")
        save_button.clicked.connect(self.save_file)
        button_layout.addWidget(save_button)

        run_button = QPushButton("run")
        run_button.clicked.connect(self.run_code)
        button_layout.addWidget(run_button)
        
        layout.addLayout(button_layout)

        code_editor_label = QLabel("Script Editor")
        code_editor_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        layout.addWidget(code_editor_label)

        self.code_editor = QTextEdit()
        self.code_editor.setPlaceholderText("-- Write Lua Script")
        layout.addWidget(self.code_editor)

        result_label = QLabel("Output Window")
        result_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        layout.addWidget(result_label)

        self.result_viewer = QTextEdit()
        self.result_viewer.setPlaceholderText("")
        self.result_viewer.setReadOnly(True)
        layout.addWidget(self.result_viewer)

        self.file_info_label = QLabel(f"Current : {self.file_path}")
        self.file_info_label.setStyleSheet("color: gray;")
        layout.addWidget(self.file_info_label)


    def run_code(self):
        code = self.code_editor.toPlainText() 
        output = run_user_script(code)
        self.result_viewer.setText(output)

    def new_file(self):
        self.file_path = 'Unknown'
        self.file_info_label.setText(f'Current : {self.file_path}')
        self.code_editor.setPlainText('')
        self.result_viewer.setText('')
        

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Lua Files (*.lua);;All Files (*)")

        if file_path:
            self.file_path = file_path
            self.file_info_label.setText(f'Current : {self.file_path}')

            with open(self.file_path, 'r') as f:
                self.code_editor.setPlainText(f.read())

    def save_file(self):
        if self.file_path != 'Unknown':
            with open(self.file_path, 'w') as f:
                f.write(self.code_editor.toPlainText())
        else:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Lua Files (*.lua);;All Files (*)")

            if file_path:
                self.file_path = file_path
                self.file_info_label.setText(f'Current : {self.file_path}')

                with open(self.file_path, 'w') as f:
                    f.write(self.code_editor.toPlainText())

        
