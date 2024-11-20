import os
import sys
import re
import time
import psutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QLineEdit, QPushButton, QTabWidget, QTreeView, QTableView, QHeaderView,
    QAbstractItemView, QMenu, QAction
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer, QItemSelectionModel, QPoint, Qt
from process import Proc
from filter_process import filter_process_by_name
from process_tree import get_process_tree

# Force PyQt to use X11 on Wayland systems to suppress the warning
os.environ["QT_QPA_PLATFORM"] = "xcb"


class ProcessViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Process Viewer")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize models for list and tree views
        self.list_model = QStandardItemModel()
        self.tree_model = QStandardItemModel()

        # Main container widget
        self.container = QWidget()
        self.setCentralWidget(self.container)
        self.layout = QHBoxLayout(self.container)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        self.layout.addWidget(self.tabs)

        # Initialize tabs
        self.init_process_tab()
        self.init_other_tabs()

        # Data storage
        self.previous_cpu_times = {}
        self.previous_update_time = time.time()
        self.previous_cpu_data = {}

        # Start periodic updates
        self.init_cpu_usage()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_process_data)
        self.timer.start(1000)

        # Filtering flag and regex pattern
        self.filter_regex = None

    def init_process_tab(self):
        # Process tab layout
        process_tab = QWidget()
        process_layout = QVBoxLayout(process_tab)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Enter regex for filtering processes")
        search_layout.addWidget(self.search_entry)

        search_button = QPushButton("Search")
        search_button.clicked.connect(self.on_search_click)
        search_layout.addWidget(search_button)
        process_layout.addLayout(search_layout)

        # Tabs for list and tree views
        process_views = QTabWidget()
        process_layout.addWidget(process_views)

        # List view
        self.list_view = QTableView()
        self.list_view.setModel(self.list_model)
        self.list_model.setHorizontalHeaderLabels(
            ["Name", "PID", "User", "Priority", "CPU %", "Memory %", "Disk Read (KB)", "Disk Write (KB)", "does exist", "virus total"]
        )
        self.list_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.list_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.list_view.horizontalHeader().setStretchLastSection(False)
        self.list_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.list_view.verticalHeader().setVisible(False)

        # Add right-click menu to the list view
        self.list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self.on_list_view_right_click)

        process_views.addTab(self.list_view, "List")

        # Tree view
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.tree_model)
        self.tree_model.setHorizontalHeaderLabels(["Name", "PID"])
        self.tree_view.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        process_views.addTab(self.tree_view, "Tree")

        # Add process tab to main tabs
        self.tabs.addTab(process_tab, "Processes")

    def init_other_tabs(self):
        # Placeholder tabs for other features
        for tab_name in ["Resources", "Network", "Users", "Advanced Features"]:
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            layout.addWidget(QPushButton(f"{tab_name} - Content goes here"))
            self.tabs.addTab(placeholder, tab_name)

    def init_cpu_usage(self):
        """Initialize CPU usage for all processes."""
        for proc in self.get_all_procs():
            try:
                self.previous_cpu_times[proc.pid] = proc.cpu_times()
            except Exception:
                pass

    def calculate_cpu_percent(self, proc):
        """Calculate CPU percent usage for a given process."""
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

    def update_process_data(self):
        """Update both list and tree views."""
        self.update_list_data()
        self.update_tree_data()

    def update_list_data(self):
        """Update the process list model."""
        selected_pids = self.get_selected_pids()

        self.list_model.removeRows(0, self.list_model.rowCount())

        all_procs = self.get_all_procs()

        if self.filter_regex:
            try:
                filtered_procs = filter_process_by_name(all_procs, self.filter_regex)
            except re.error:
                filtered_procs = []
        else:
            filtered_procs = all_procs

        for proc in filtered_procs:
            try:
                cpu_percent = self.calculate_cpu_percent(proc)
                data = [
                    proc.name(),
                    proc.pid,
                    proc.username(),
                    proc.nice(),
                    f'{cpu_percent:0>6.3f}%',
                    f'{proc.memory_percent():0>6.3f}%',
                    proc.io_counters().read_bytes / 1024,
                    proc.io_counters().write_bytes / 1024,
                    proc.does_exist,
                    proc.vt,
                ]
                self.list_model.appendRow([QStandardItem(str(item)) for item in data])
            except Exception:
                continue

        self.previous_update_time = time.time()
        self.restore_selected_pids(selected_pids)

        self.list_view.resizeRowsToContents()
        self.list_view.resizeColumnsToContents()

    def get_selected_pids(self):
        selected_indexes = self.list_view.selectionModel().selectedRows(1)
        selected_pids = []
        for index in selected_indexes:
            selected_pids.append(int(self.list_model.item(index.row(), 1).text()))
        return selected_pids

    def restore_selected_pids(self, selected_pids):
        for row in range(self.list_model.rowCount()):
            pid_item = self.list_model.item(row, 1)
            if pid_item and int(pid_item.text()) in selected_pids:
                index = self.list_model.indexFromItem(pid_item)
                self.list_view.selectionModel().select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)

    def update_tree_data(self):
        vertical_scroll_position = self.tree_view.verticalScrollBar().value()
        open_nodes = self.get_open_nodes()

        process_tree = get_process_tree(self.get_all_procs())

        def build_tree(parent_item, parent_pid):
            for proc in process_tree.get(parent_pid, []):
                child_item = QStandardItem(proc.name())
                child_pid_item = QStandardItem(str(proc.pid))
                parent_item.appendRow([child_item, child_pid_item])
                build_tree(child_item, proc.pid)

        self.tree_model.removeRows(0, self.tree_model.rowCount())
        self.tree_model.setHorizontalHeaderLabels(["Name", "PID"])

        for parent_pid, children in sorted(process_tree.items()):
            parent_proc = next((p for p in self.get_all_procs() if p.pid == parent_pid), None)
            if parent_proc:
                parent_item = QStandardItem(parent_proc.name())
                parent_pid_item = QStandardItem(str(parent_proc.pid))
                self.tree_model.appendRow([parent_item, parent_pid_item])
                build_tree(parent_item, parent_pid)

        self.restore_open_nodes(open_nodes)
        self.tree_view.verticalScrollBar().setValue(vertical_scroll_position)

    def get_all_procs(self):
        procs = []
        for p in psutil.process_iter():
            try:
                procs.append(Proc(p))
            except Exception:
                continue

        return procs

    def get_open_nodes(self):
        open_nodes = set()

        def collect_open_nodes(parent_index):
            if self.tree_view.isExpanded(parent_index):
                pid = int(self.tree_model.itemFromIndex(parent_index.siblingAtColumn(1)).text())
                open_nodes.add(pid)
                for row in range(self.tree_model.rowCount(parent_index)):
                    child_index = self.tree_model.index(row, 0, parent_index)
                    collect_open_nodes(child_index)

        for row in range(self.tree_model.rowCount()):
            index = self.tree_model.index(row, 0)
            collect_open_nodes(index)

        return open_nodes

    def restore_open_nodes(self, open_nodes):
        def expand_matching_nodes(parent_index):
            if not parent_index.isValid():
                return
            pid = int(self.tree_model.itemFromIndex(parent_index.siblingAtColumn(1)).text())
            if pid in open_nodes:
                self.tree_view.setExpanded(parent_index, True)
            for row in range(self.tree_model.rowCount(parent_index)):
                child_index = self.tree_model.index(row, 0, parent_index)
                expand_matching_nodes(child_index)

        for row in range(self.tree_model.rowCount()):
            index = self.tree_model.index(row, 0)
            expand_matching_nodes(index)

    def on_search_click(self):
        self.filter_regex = self.search_entry.text()
        self.update_list_data()

    def on_list_view_right_click(self, position: QPoint):
        indexes = self.list_view.selectionModel().selectedRows()
        if not indexes:
            return

        pid_index = indexes[0]
        pid = int(self.list_model.item(pid_index.row(), 1).text())

        proc = next((p for p in self.get_all_procs() if p.pid == pid), None)
        if not proc:
            return

        menu = QMenu(self.list_view)

        check_vt_action = QAction("Check with VirusTotal", self)
        check_vt_action.triggered.connect(lambda: (proc.check_process_with_vt(), self.update_process_data()))

        check_existence_action = QAction("Check File Existence", self)
        check_existence_action.triggered.connect(proc.is_file_exists)

        menu.addAction(check_vt_action)
        menu.addAction(check_existence_action)

        menu.exec_(self.list_view.viewport().mapToGlobal(position))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ProcessViewer()
    viewer.show()
    sys.exit(app.exec_())

