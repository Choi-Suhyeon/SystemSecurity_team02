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
    QFileDialog,
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer, QItemSelectionModel, QPoint, Qt, QSize
from process import Proc
from filter_process import filter_process_by_name
from process_tree import get_process_tree
from PyQt5.QtGui import QPainter, QColor, QFont
from itertools import tee
from functools import reduce
from snapshot import save_snapshot

class ProcessTab(QTabWidget):
    def __init__(self):
        super().__init__()

        self.procs = list()
        self.procs_user = dict()
        self.regex = str()
        self.cpu_count = psutil.cpu_count()

        self.update_proc_objs()

        self.timer = QTimer()

        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_proc_table)
        self.timer.timeout.connect(self.update_proc_users_table)
        self.timer.timeout.connect(self.update_proc_tree_table)
        self.timer.start()

        self.addTab(self.get_list_view_tab(), 'List')
        self.addTab(self.get_users_view_tab(), 'Users')
        self.addTab(self.get_tree_view_tab(), 'Tree')
        
    def update_proc_objs(self):
        def get_username(proc):
            try:
                return proc.username()
            except:
                return 'Unknown'

        def dict_update(dct, key, val):
            if key not in dct:
                dct[key] = [val]
            else:
                dct[key].append(val)

            return dct

        pid_set      = set(i.pid for i in self.procs)
        pi1, pi2     = tee(psutil.process_iter())
        new_pids_set = set(i.pid for i in pi1)

        new_items = list()
        del_items = list(pid_set - new_pids_set)

        for p in pi2:
            try:
                if p.pid not in pid_set:
                    item = Proc(p)
                    self.procs.append(item)
                    new_items.append(item)
            except:
                continue

        self.procs = [i for i in self.procs if i.pid in new_pids_set]

        if not self.procs_user:
            self.procs_user = reduce(lambda acc, p: dict_update(acc, get_username(p), p), self.procs, dict())
        else:
            for d in del_items:
                for k in self.procs_user.keys():
                    if d in self.procs_user[k]:
                        self.procs_user[k].remove(d)

            for n in new_items:
                dict_update(self.procs_user, get_username(n), n)


    def get_list_view_tab(self):
        result = QWidget()
        hbox = QHBoxLayout()

        self.reg_line_edit = QLineEdit(result)
        self.filter_btn    = QPushButton('filter', result)
        self.snapshot_btn  = QPushButton('save snapshot', result)

        self.reg_line_edit.editingFinished.connect(self.filter_process)
        self.filter_btn.clicked.connect(self.filter_process)
        self.snapshot_btn.clicked.connect(self.save_snapshot)

        hbox.addWidget(self.reg_line_edit)
        hbox.addWidget(self.filter_btn)
        hbox.addWidget(self.snapshot_btn)

        var_names = [
            'obj', 'name', 'pid', 'user', 'priority', 'cpu (%)', 
            'memory (%)',  'Disk Read (KB)', 'Disk Write (KB)', 
            'does exist', 'virus total',
        ]

        self.proc_table = QTableWidget(result)
        self.proc_table.setColumnCount(len(var_names))

        self.proc_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.proc_table.verticalHeader().setVisible(False)
        self.proc_table.setHorizontalHeaderLabels(var_names)
        self.proc_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.proc_table.customContextMenuRequested.connect(self.showContextMenu)
        self.proc_table.hideColumn(0)
        self.update_proc_table()

        vbox = QVBoxLayout(result)

        vbox.addLayout(hbox)
        vbox.addWidget(self.proc_table)

        result.setLayout(vbox)

        return result

    def get_users_view_tab(self):
        var_names = [
            'user', 'name', 'pid', 'priority', 'cpu (%)', 
            'memory (%)',  'Disk Read (KB)', 'Disk Write (KB)', 
        ]

        self.proc_table_user = QTreeWidget()
        self.proc_table_user.setColumnCount(len(var_names))
        self.proc_table_user.setHeaderLabels(var_names)
        self.update_proc_users_table()

        vbox = QVBoxLayout()
        vbox.addWidget(self.proc_table_user)

        result = QWidget()
        result.setLayout(vbox)

        return result

    def get_tree_view_tab(self):
        var_names = [
            'user', 'name', 'pid', 'priority', 'cpu (%)', 
            'memory (%)',  'Disk Read (KB)', 'Disk Write (KB)', 
        ]

        self.proc_table_tree = QTreeWidget()
        self.proc_table_tree.setColumnCount(len(var_names))
        self.proc_table_tree.setHeaderLabels(var_names)
        self.update_proc_tree_table()

        vbox = QVBoxLayout()
        vbox.addWidget(self.proc_table_tree)

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
                proc_hidden = QTableWidgetItem()
                proc_hidden.setData(Qt.UserRole, proc)
                # cpu_percent = self.calculate_cpu_percent(proc)
                self.proc_table.setItem(row_cnt, 0, QTableWidgetItem(proc_hidden))
                self.proc_table.setItem(row_cnt, 1, QTableWidgetItem(proc.name()))
                self.proc_table.setItem(row_cnt, 2, QTableWidgetItem(str(proc.pid)))
                self.proc_table.setItem(row_cnt, 3, QTableWidgetItem(proc.username()))
                self.proc_table.setItem(row_cnt, 4, QTableWidgetItem(str(proc.nice())))
                self.proc_table.setItem(row_cnt, 5, QTableWidgetItem(f'{proc.cpu_percent(0)/self.cpu_count:0>6.3f}%'))
                self.proc_table.setItem(row_cnt, 6, QTableWidgetItem(f'{proc.memory_percent():0>6.3f}%'))
                self.proc_table.setItem(row_cnt, 7, QTableWidgetItem(str(proc.io_counters().read_bytes / 1024)))
                self.proc_table.setItem(row_cnt, 8, QTableWidgetItem(str(proc.io_counters().write_bytes / 1024)))
                self.proc_table.setItem(row_cnt, 9, QTableWidgetItem(proc.does_exist)) # proc.does_exist
                self.proc_table.setItem(row_cnt, 10, QTableWidgetItem(proc.vt)) # proc.vt
                row_cnt += 1

            except Exception:
                continue
                
    def update_proc_users_table(self):
        def save_tree_state(tree_widget):
            state = {}
            root = tree_widget.invisibleRootItem()
            stack = [(root, [])]
            while stack:
                item, path = stack.pop()
                if item.isExpanded():
                    state[tuple(path)] = True
                for i in range(item.childCount()):
                    stack.append((item.child(i), path + [i]))
            return state

        def restore_tree_state(tree_widget, state):
            root = tree_widget.invisibleRootItem()
            stack = [(root, [])]
            while stack:
                item, path = stack.pop()
                if tuple(path) in state:
                    item.setExpanded(True)
                for i in range(item.childCount()):
                    stack.append((item.child(i), path + [i]))

        scroll_position = self.proc_table_user.verticalScrollBar().value()
        tree_state = save_tree_state(self.proc_table_user)

        self.proc_table_user.clear() 

        for user in sorted(self.procs_user.keys()):
            try:
                user_item = QTreeWidgetItem(self.proc_table_user)
                user_item.setText(0, user)

                for proc in self.procs_user[user]:
                    try:
                        proc_item = QTreeWidgetItem(user_item)
                        proc_item.setText(1, proc.name())
                        proc_item.setText(2, str(proc.pid))
                        proc_item.setText(3, str(proc.nice()))
                        proc_item.setText(4, f'00.000%')
                        proc_item.setText(5, f'{proc.memory_percent():0>6.3f}%')
                        proc_item.setText(6, str(proc.io_counters().read_bytes / 1024))
                        proc_item.setText(7, str(proc.io_counters().write_bytes / 1024))
                    except Exception:
                        continue
            except Exception:
                continue

        restore_tree_state(self.proc_table_user, tree_state)
        self.proc_table_user.verticalScrollBar().setValue(scroll_position)

    def update_proc_tree_table(self):
        def save_tree_state(tree_widget):
            state = {}
            root = tree_widget.invisibleRootItem()
            stack = [(root, [])]
            while stack:
                item, path = stack.pop()
                if item.isExpanded():
                    state[tuple(path)] = True
                for i in range(item.childCount()):
                    stack.append((item.child(i), path + [i]))
            return state

        def restore_tree_state(tree_widget, state):
            root = tree_widget.invisibleRootItem()
            stack = [(root, [])]
            while stack:
                item, path = stack.pop()
                if tuple(path) in state:
                    item.setExpanded(True)
                for i in range(item.childCount()):
                    stack.append((item.child(i), path + [i]))

        scroll_position = self.proc_table_tree.verticalScrollBar().value()
        tree_state = save_tree_state(self.proc_table_tree)

        self.proc_table_tree.clear() 
        
        process_tree = get_process_tree(self.procs)

        def set_item(proc_tree, super_elem, parent_pid = None):
            if parent_pid is None:
                parent_pid  = min(proc_tree.keys())
                procs       = proc_tree.pop(parent_pid)
                item        = QTreeWidgetItem(super_elem)

                item.setText(1, '')
                item.setText(2, '0')
                item.setText(3, '')
                item.setText(4, '')
                item.setText(5, '')
                item.setText(6, '')
                item.setText(7, '')
            else:
                procs = proc_tree.pop(parent_pid)
                item = super_elem
               
            for p in procs:
                try:
                    child_item = QTreeWidgetItem(item)
                    child_item.setText(1, p.name())
                    child_item.setText(2, str(p.pid))
                    child_item.setText(3, str(p.nice()))
                    child_item.setText(4, f'{p.cpu_percent(0)/5:0>6.3f}%')
                    child_item.setText(5, f'{p.memory_percent():0>6.3f}%')
                    child_item.setText(6, str(p.io_counters().read_bytes / 1024))
                    child_item.setText(7, str(p.io_counters().write_bytes / 1024))
                except Exception:
                    child_item = QTreeWidgetItem(item)
                    child_item.setText(1, '')
                    child_item.setText(2, str(p.pid))
                    child_item.setText(3, '')
                    child_item.setText(4, '')
                    child_item.setText(5, '')
                    child_item.setText(6, '')
                    child_item.setText(7, '')

                if p.pid in proc_tree.keys():
                    set_item(proc_tree, child_item, p.pid)

        set_item(process_tree, self.proc_table_tree)
        restore_tree_state(self.proc_table_tree, tree_state)
        self.proc_table_tree.verticalScrollBar().setValue(scroll_position)


    def filter_process(self):
        self.regex = self.reg_line_edit.text()

    def showContextMenu(self, pos: QPoint):
        selected_row = self.proc_table.indexAt(pos).row()

        if selected_row < 0:
            return

        self.proc_table.selectRow(selected_row)  

        context_menu = QMenu(self)
        priority_menu = QMenu('change priority', self)

        process_kill_action    = QAction('kill process', self)
        check_existence_action = QAction('check file existence', self)
        check_vt_action        = QAction('check with virus total', self)

        priority_up_action   = QAction('increase priority', self)
        priority_down_action = QAction('decrease priority', self)

        process_kill_action.triggered.connect(lambda: os.kill(int(self.proc_table.item(selected_row, 2).text()), signal.SIGTERM))
        check_existence_action.triggered.connect(lambda: self.proc_table.item(selected_row, 0).data(Qt.UserRole).is_file_exists())
        check_vt_action.triggered.connect(lambda: self.proc_table.item(selected_row, 0).data(Qt.UserRole).check_process_with_vt())

        priority_up_action.triggered.connect(lambda: self.proc_table.item(selected_row, 0).data(Qt.UserRole).increase_priority())
        priority_down_action.triggered.connect(lambda: self.proc_table.item(selected_row, 0).data(Qt.UserRole).decrease_priority())

        priority_menu.addAction(priority_up_action)
        priority_menu.addAction(priority_down_action)

        context_menu.addAction(process_kill_action)
        context_menu.addMenu(priority_menu)
        context_menu.addAction(check_existence_action)
        context_menu.addAction(check_vt_action)
        context_menu.exec_(self.proc_table.viewport().mapToGlobal(pos))

    def save_snapshot(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Open File", "", "All Files (*)")

        if not file_path:
            return

        save_snapshot([Proc(i) for i in psutil.process_iter()], file_path)

