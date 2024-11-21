import os
import sys
import re
import time
import psutil
import signal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QTableWidget, QTabBar,
    QWidget, QLineEdit, QPushButton, QTabWidget, QTreeView, QTableView, QHeaderView,
    QAbstractItemView, QMenu, QAction, QTableWidgetItem
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer, QItemSelectionModel, QPoint, Qt, QSize
from process import Proc
from filter_process import filter_process_by_name
from process_tree import get_process_tree
from PyQt5.QtGui import QPainter, QColor, QFont
from itertools import tee


class ProcessViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Process Viewer')
        self.setGeometry(300, 300, 1100, 600)

        tabs = QTabWidget()
        resource_tab = QWidget()
        network_tab = QWidget()

        self.procs = list()
        self.regex = str()
        # self.previous_cpu_times = {}
        # self.previous_cpu_data = {}

        self.update_proc_objs()
        # self.init_cpu_usage()

        tabs.setTabPosition(QTabWidget.West)
        tabs.addTab(self.get_process_tab(), 'Processes')
        tabs.addTab(resource_tab, "Resources")
        tabs.addTab(network_tab, "Per-Process Networks")

        self.setCentralWidget(tabs)

        self.timer = QTimer()

        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_proc_table)
        self.timer.start()

    def init_cpu_usage(self):
        for proc in self.procs:
            try:
                self.previous_cpu_times[proc.pid] = proc.cpu_times()
            except Exception:
                pass

    def update_proc_objs(self):
        pid_set      = set(i.pid for i in self.procs)
        pi1, pi2     = tee(psutil.process_iter())
        new_pids_set = set(i.pid for i in pi1)

        for p in pi2:
            try:
                if p.pid not in pid_set:
                    self.procs.append(Proc(p))
            except:
                continue

        self.procs = [i for i in self.procs if i.pid in new_pids_set]

    def get_process_tab(self):
        inner_tabs = QTabWidget()
        tree_tab = QWidget()

        inner_tabs.addTab(self.get_list_view_tab(), 'List View')
        inner_tabs.addTab(tree_tab, 'Tree View')

        return inner_tabs

    def get_list_view_tab(self):
        self.reg_line_edit = QLineEdit(self)
        self.filter_btn    = QPushButton('filter', self)

        self.reg_line_edit.editingFinished.connect(self.filter_process)
        self.filter_btn.clicked.connect(self.filter_process)

        hbox = QHBoxLayout()

        hbox.addWidget(self.reg_line_edit)
        hbox.addWidget(self.filter_btn)

        var_names = [
            'obj', 'name', 'pid', 'user', 'priority', 'cpu (%)', 
            'memory (%)',  'Disk Read (KB)', 'Disk Write (KB)', 
            'does exist', 'virus total',
        ]

        self.proc_table = QTableWidget(self)
        self.proc_table.setColumnCount(len(var_names))

        self.proc_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.proc_table.verticalHeader().setVisible(False)
        self.proc_table.setHorizontalHeaderLabels(var_names)
        self.proc_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.proc_table.customContextMenuRequested.connect(self.showContextMenu)
        self.proc_table.hideColumn(0)
        self.update_proc_table()

        vbox = QVBoxLayout()

        vbox.addLayout(hbox)
        vbox.addWidget(self.proc_table)

        result = QWidget()
        result.setLayout(vbox)

        return result

    def update_proc_table(self):
        self.update_proc_objs()

        filtered_procs = filtered if self.regex and (filtered := filter_process_by_name(self.procs, self.regex)) is not None else self.procs
        row_cnt = 0

        self.proc_table.setRowCount(len(filtered_procs))
        
        for proc in filtered_procs:
            try:
                # cpu_percent = self.calculate_cpu_percent(proc)
                self.proc_table.setItem(row_cnt, 0, QTableWidgetItem(str(proc)))
                self.proc_table.setItem(row_cnt, 1, QTableWidgetItem(proc.name()))
                self.proc_table.setItem(row_cnt, 2, QTableWidgetItem(str(proc.pid)))
                self.proc_table.setItem(row_cnt, 3, QTableWidgetItem(proc.username()))
                self.proc_table.setItem(row_cnt, 4, QTableWidgetItem(str(proc.nice())))
                self.proc_table.setItem(row_cnt, 5, QTableWidgetItem(f'00.000%'))
                self.proc_table.setItem(row_cnt, 6, QTableWidgetItem(f'{proc.memory_percent():0>6.3f}%'))
                self.proc_table.setItem(row_cnt, 7, QTableWidgetItem(str(proc.io_counters().read_bytes / 1024)))
                self.proc_table.setItem(row_cnt, 8, QTableWidgetItem(str(proc.io_counters().write_bytes / 1024)))
                self.proc_table.setItem(row_cnt, 9, QTableWidgetItem('')) # proc.does_exist
                self.proc_table.setItem(row_cnt, 10, QTableWidgetItem('')) # proc.vt
                row_cnt += 1

            except Exception:
                continue

    def calculate_cpu_percent(self, proc):
        try:
            current_time = time.time()
            if proc.pid not in self.previous_cpu_times:
                self.previous_cpu_times[proc.pid] = proc.cpu_times()
                return 0.0

            # Fetch previous CPU times and calculate deltas
            prev_times = self.previous_cpu_times[proc.pid]
            curr_times = proc.cpu_times()
            delta_user = curr_times.user - prev_times.user
            delta_system = curr_times.system - prev_times.system
            delta_time = current_time - self.previous_update_time

            # Update previous times
            self.previous_cpu_times[proc.pid] = curr_times
            if delta_time > 0:
                return 100.0 * (delta_user + delta_system) / (psutil.cpu_count() * delta_time)
            else:
                return 0.0
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0

    def filter_process(self):
        self.regex = self.reg_line_edit.text()

    def showContextMenu(self, pos: QPoint):
        selected_row = self.proc_table.indexAt(pos).row()

        if selected_row < 0:
            return

        self.proc_table.selectRow(selected_row)  

        context_menu = QMenu(self)

        process_kill_action    = QAction('kill process', self)
        check_existence_action = QAction('check file existence', self)
        check_vt_action        = QAction('check with virus total', self)

        process_kill_action.triggered.connect(lambda: os.kill(int(self.proc_table.item(selected_row, 2).text()), signal.SIGTERM))
        # check_existence_action.triggered.connect()
        # check_vt_action.triggered.connect()

        context_menu.addAction(process_kill_action)
        # context_menu.addAction(check_existence_action)
        # context_menu.addAction(check_vt_action)
        context_menu.exec_(self.proc_table.viewport().mapToGlobal(pos))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ProcessViewer()
    viewer.show()
    sys.exit(app.exec_())

