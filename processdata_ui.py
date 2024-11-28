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
from proc_sniffer import PacketCollector
from process import Proc
from socket_info import get_socket_info
from socket_geolocation_info import get_geolocation




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
        tabs.addTab(self.get_network_tab(), "Per-Process Networks")  # 使用新的方法返回的 UI

        self.setCentralWidget(tabs)

        self.timer = QTimer()

        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_proc_table)
        self.timer.start()

        self.timer.timeout.connect(self.update_so_table)  # 定时更新 SO 表格
        self.update_so_btn = QPushButton('Update SO Info', self)
        self.update_so_btn.clicked.connect(self.update_so_table)

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

    def filter_network_data(self):
        """根据正则表达式过滤网络数据"""
        regex = self.network_reg_line_edit.text()
        if not regex:
            return

        # 更新表格1 (SO 数据)
        filtered_so_data = [row for row in self.so_data if re.search(regex, str(row))]
        self.update_table(self.so_table, filtered_so_data)

        # 更新表格2 (File Descriptor 数据)
        filtered_fd_data = [row for row in self.fd_data if re.search(regex, str(row))]
        self.update_table(self.fd_table, filtered_fd_data)

    def update_table(self, table, data):
        """更新表格数据"""
        table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, col_data in enumerate(row_data):
                table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))

    def start_packet_collection(self):
        """开始收集数据包"""
        pid = 1234  # 替换为实际的 PID 或动态选择的进程
        self.packet_collector = PacketCollector(pid)  # 创建数据包收集器
        self.packet_collector.start_collection()  # 开始收集数据包

        # 定时器用于动态更新捕获的数据
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_packet_table)
        self.timer.start(1000)  # 每秒更新一次表格

    def stop_packet_collection(self):
        """停止收集数据包"""
        if hasattr(self, 'packet_collector'):
            self.packet_collector.stop_collection()  # 停止数据包收集
        if hasattr(self, 'timer'):
            self.timer.stop()  # 停止定时器

    def update_packet_table(self):
        """更新捕获内容表格"""
        packets = self.packet_collector.get_collected_packets()
        self.packet_table.setRowCount(len(packets))  # 更新表格行数
        for row_idx, packet in enumerate(packets):
            self.packet_table.setItem(row_idx, 0, QTableWidgetItem(packet["src_ip"]))
            self.packet_table.setItem(row_idx, 1, QTableWidgetItem(str(packet["src_port"])))
            self.packet_table.setItem(row_idx, 2, QTableWidgetItem(packet["dst_ip"]))
            self.packet_table.setItem(row_idx, 3, QTableWidgetItem(str(packet["dst_port"])))

    def update_so_table(self):
        """更新共享对象表格"""
        so_data = []  # 存储提取的共享对象数据
        for proc in self.procs:  # 遍历当前进程列表
            try:
                shared_objects = proc.get_shared_objects()
                for obj in shared_objects:
                    so_data.append((proc.pid, proc.name(), obj))  # 记录 PID、进程名称和共享对象路径
            except Exception:
                continue  # 忽略无法访问的进程

        # 更新表格内容
        self.so_table.setRowCount(len(so_data))
        for row_idx, row_data in enumerate(so_data):
            self.so_table.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0])))  # PID
            self.so_table.setItem(row_idx, 1, QTableWidgetItem(row_data[1]))  # Process Name
            self.so_table.setItem(row_idx, 2, QTableWidgetItem(row_data[2]))  # Shared Object

    def display_ip_info(self):
        """显示 IP 信息到表格"""
        try:
            # 获取当前网络连接的 TCP 和 UDP 信息
            tcp_info, udp_info = get_socket_info()
            combined_info = tcp_info + udp_info  # 合并 TCP 和 UDP 信息

            # 更新表格行数
            self.packet_table.setRowCount(len(combined_info))

            # 填充表格
            for row_idx, conn in enumerate(combined_info):
                local_address = conn[0] or "N/A"  # 本地地址
                remote_address = conn[1] or "N/A"  # 远程地址
                pid = conn[2] or "N/A"  # 进程 ID
                state_or_protocol = conn[3] if len(conn) > 3 else "UDP"  # 状态或协议

                # 获取地理位置信息
                geo_info = get_geolocation(remote_address.split(':')[0]) if remote_address != "N/A" else None
                location = geo_info["Location (Lat, Long)"] if geo_info else "Unknown"

                # 填充表格内容
                self.packet_table.setItem(row_idx, 0, QTableWidgetItem(local_address))
                self.packet_table.setItem(row_idx, 1, QTableWidgetItem(remote_address))
                self.packet_table.setItem(row_idx, 2, QTableWidgetItem(pid))
                self.packet_table.setItem(row_idx, 3, QTableWidgetItem(state_or_protocol))
                self.packet_table.setItem(row_idx, 4, QTableWidgetItem(location))
        except Exception as e:
            print(f"Error displaying IP information: {e}")


    def get_network_tab(self):
        # 创建搜索框和按钮
        self.network_reg_line_edit = QLineEdit(self)
        self.network_search_btn = QPushButton('search', self)

        self.network_reg_line_edit.editingFinished.connect(self.filter_network_data)
        self.network_search_btn.clicked.connect(self.filter_network_data)

        search_hbox = QHBoxLayout()
        search_hbox.addWidget(self.network_reg_line_edit)
        search_hbox.addWidget(self.network_search_btn)

        # 创建表格1 (显示 SO 数据相关内容)
        self.so_table = QTableWidget(self)
        so_headers = ['PID', 'Process Name', 'Shared Object']
        self.so_table.setColumnCount(len(so_headers))
        self.so_table.setHorizontalHeaderLabels(so_headers)
        self.so_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.so_table.verticalHeader().setVisible(False)

        # 创建表格2 (显示 File Descriptor 数据相关内容)
        self.fd_table = QTableWidget(self)
        fd_headers = ['PID', 'Process Name', 'FD', 'Type', 'Path']
        self.fd_table.setColumnCount(len(fd_headers))
        self.fd_table.setHorizontalHeaderLabels(fd_headers)
        self.fd_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.fd_table.verticalHeader().setVisible(False)

        # 创建三个按钮
        self.start_packet_btn = QPushButton('패킷수집 시작', self)
        self.stop_packet_btn = QPushButton('패킷수집 종료', self)
        self.ip_info_btn = QPushButton('IP정보', self)



        # 绑定事件
        self.start_packet_btn.clicked.connect(self.start_packet_collection)
        self.stop_packet_btn.clicked.connect(self.stop_packet_collection)
        self.ip_info_btn.clicked.connect(self.display_ip_info)

        btn_hbox = QHBoxLayout()
        btn_hbox.addWidget(self.start_packet_btn)
        btn_hbox.addWidget(self.stop_packet_btn)
        btn_hbox.addWidget(self.ip_info_btn)

        # 创建表格3 (显示捕获的内容)
        self.packet_table = QTableWidget(self)
        packet_headers = ['Local Address', 'Remote Address', 'PID', 'State/Protocol', 'Geolocation']
        self.packet_table.setColumnCount(len(packet_headers))
        self.packet_table.setHorizontalHeaderLabels(packet_headers)

        # 整合布局
        layout = QVBoxLayout()
        layout.addLayout(search_hbox)
        layout.addWidget(self.so_table)
        layout.addWidget(self.fd_table)
        layout.addLayout(btn_hbox)
        layout.addWidget(self.packet_table)

        network_tab_widget = QWidget()
        network_tab_widget.setLayout(layout)

        return network_tab_widget

    def filter_network_data(self):
        # 目前为空，稍后实现实际的过滤逻辑
        print("Filtering network data...")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ProcessViewer()
    viewer.show()
    sys.exit(app.exec_())

