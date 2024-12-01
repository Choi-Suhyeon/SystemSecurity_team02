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
    QLabel,
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer, QItemSelectionModel, QPoint, Qt, QSize
from process import Proc
from filter_process import filter_process_by_name
from process_tree import get_process_tree
from PyQt5.QtGui import QPainter, QColor, QFont
from itertools import tee
from functools import reduce

from ui_resource_graph import RealtimeGraph
from ui_process import ProcessTab
from ui_user_script import UserDefinedScriptTab
from ui_process_detail import ProcessDetailTab


class ProcessViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Process Viewer')
        self.setGeometry(300, 300, 1200, 900)

        tabs = QTabWidget()
        network_tab = QWidget()

        tabs.setTabPosition(QTabWidget.West)
        tabs.addTab(ProcessTab(), 'Processes')
        tabs.addTab(RealtimeGraph(), 'Resources')
        tabs.addTab(ProcessDetailTab(), 'Process Detail')
        tabs.addTab(UserDefinedScriptTab(), 'User Script')

        self.setCentralWidget(tabs)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ProcessViewer()
    viewer.show()
    sys.exit(app.exec_())

