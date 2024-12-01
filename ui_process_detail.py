import os
import sys
import re
import time
import psutil
import signal
import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QTableWidget, QTabBar,
    QWidget, QLineEdit, QPushButton, QTabWidget, QTreeView, QTableView, QHeaderView,
    QAbstractItemView, QMenu, QAction, QTableWidgetItem, QTreeWidget, QTreeWidgetItem,
    QLabel, QGridLayout, QScrollArea,
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer, QItemSelectionModel, QPoint, Qt, QSize
from process import Proc
from filter_process import filter_process_by_name
from process_tree import get_process_tree
from PyQt5.QtGui import QPainter, QColor, QFont
from itertools import tee
from functools import reduce
from process_sniffer import PacketSniffer
from socket_geolocation_info import get_geolocation

class ProcessDetailTab(QWidget):
    def __init__(self):
        super().__init__()
        
        self.sniffer = None 

        search_hbox = QHBoxLayout()
        grid_packet = QGridLayout()

        grid_packet.setHorizontalSpacing(15)

        self.pid_line_edit = QLineEdit(self)
        self.btn_search = QPushButton('search')

        self.pid_line_edit.editingFinished.connect(self.search_pid)
        self.pid_line_edit.setPlaceholderText('pid')
        self.btn_search.clicked.connect(self.search_pid)

        search_hbox.addWidget(self.pid_line_edit)
        search_hbox.addWidget(self.btn_search)

        self.btn_start_packet_capture = QPushButton('start packet capture', self)
        self.btn_stop_packet_capture  = QPushButton('stop packet capture', self)
        self.btn_get_location_info    = QPushButton('locate via IP', self)

        self.btn_stop_packet_capture.setEnabled(False)
        self.btn_get_location_info.setEnabled(False)

        self.btn_start_packet_capture.clicked.connect(self.start_packet_capture)
        self.btn_stop_packet_capture.clicked.connect(self.stop_packet_capture)
        self.btn_get_location_info.clicked.connect(self.get_location_info)

        grid_packet.addWidget(QLabel(''), 0, 0)
        grid_packet.addWidget(QLabel(''), 0, 1)
        grid_packet.addWidget(QLabel(''), 0, 2)
        grid_packet.addWidget(self.btn_start_packet_capture, 0, 3)
        grid_packet.addWidget(self.btn_stop_packet_capture, 0, 4)
        grid_packet.addWidget(self.btn_get_location_info, 0, 5)

        lbl_so_file = QLabel('so Files', self)
        lbl_file_descripter = QLabel('File Descriptors', self)
        lbl_packet_capture = QLabel('Packet Capture', self)

        lbl_so_file.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        lbl_file_descripter.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        lbl_packet_capture.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")

        self.lbl_so = QLabel('no data')
        self.lbl_fd = QLabel('no data')

        self.lbl_so.setAlignment(Qt.AlignTop)
        self.lbl_fd.setAlignment(Qt.AlignTop)
        self.lbl_so.setStyleSheet("background-color: white;")
        self.lbl_fd.setStyleSheet("background-color: white;")

        scroll_area_so = QScrollArea()
        scroll_area_fd = QScrollArea()

        scroll_area_so.setWidget(self.lbl_so)
        scroll_area_fd.setWidget(self.lbl_fd)
        scroll_area_so.setWidgetResizable(True)
        scroll_area_fd.setWidgetResizable(True)
        scroll_area_so.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area_fd.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area_so.setStyleSheet("QScrollArea { background-color: white; border: 1px solid gray; }")
        scroll_area_fd.setStyleSheet("QScrollArea { background-color: white; border: 1px solid gray; }")

        self.tbl_packet_capture = QTableWidget(0, 6, self)
        self.tbl_packet_capture.setHorizontalHeaderLabels(("src ip", "src port", "dst ip", "dst port", "protocol", "time"))
        self.tbl_packet_capture.setSelectionBehavior(self.tbl_packet_capture.SelectRows)

        self.lbl_location = QLabel('location info')
        scroll_area_loc = QScrollArea()

        self.lbl_location.setStyleSheet("background-color: white;")
        self.lbl_location.setContentsMargins(10, 10, 10, 10)
        self.lbl_location.setAlignment(Qt.AlignTop)
        scroll_area_loc.setWidgetResizable(True)
        scroll_area_loc.setWidget(self.lbl_location)
        scroll_area_loc.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area_loc.setStyleSheet("QScrollArea { background-color: white; border: 1px solid gray; }")

        hbox_packet = QHBoxLayout()

        hbox_packet.addWidget(self.tbl_packet_capture)
        hbox_packet.addWidget(scroll_area_loc)
        hbox_packet.setStretchFactor(self.tbl_packet_capture, 2)
        hbox_packet.setStretchFactor(scroll_area_loc, 1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_packet_table)

        vbox = QVBoxLayout()

        vbox.addLayout(search_hbox)
        vbox.addWidget(lbl_so_file)
        vbox.addWidget(scroll_area_so)
        vbox.addWidget(lbl_file_descripter)
        vbox.addWidget(scroll_area_fd)
        vbox.addWidget(lbl_packet_capture)
        vbox.addLayout(grid_packet)
        vbox.addLayout(hbox_packet)

        self.setLayout(vbox)

    def search_pid(self):
        try:
            self.proc = Proc(int(self.pid_line_edit.text()))
            self.sniffer = PacketSniffer(self.proc.pid)
            so_files  = self.proc.get_shared_objects()
            fds       = self.proc.get_handles_info()[1]

        except Exception as e:
            print('exception')
            print(e)
            return

        self.lbl_so.setText('\n'.join(so_files))
        self.lbl_fd.setText('\n'.join(fds))

    def start_packet_capture(self):
        self.btn_start_packet_capture.setEnabled(False) 
        self.btn_get_location_info.setEnabled(False)
        self.btn_stop_packet_capture.setEnabled(True)

        self.tbl_packet_capture.clearContents()
        self.sniffer.start_sniffing()
        self.timer.start(1000)

    def stop_packet_capture(self):
        self.sniffer.stop_sniffing()
        self.timer.stop()

        self.btn_stop_packet_capture.setEnabled(False)
        self.btn_start_packet_capture.setEnabled(True) 
        self.btn_get_location_info.setEnabled(True)

    def get_location_info(self):
        selected_row = self.tbl_packet_capture.currentRow()

        src_ip = self.tbl_packet_capture.item(selected_row, 0).text()
        dst_ip = self.tbl_packet_capture.item(selected_row, 2).text()
        src    = get_geolocation(src_ip)
        dst    = get_geolocation(dst_ip)

        print(f'{src=}')
        print(f'{dst=}')

        if src is None or dst is None:
            return

        result = '[source]\n'
        result += '\n'.join(f'{k}: {v}' for k, v in src.items())
        result += '\n\n[destination]\n'
        result += '\n'.join(f'{k}: {v}' for k, v in dst.items())

        self.lbl_location.setText(result)

    def update_packet_table(self):
        if self.sniffer is None:
            return

        packets       = self.sniffer.get_packets()
        existing_rows = set()

        for row in range(self.tbl_packet_capture.rowCount()):
            existing_rows.add((
                self.tbl_packet_capture.item(row, 0).text(),
                self.tbl_packet_capture.item(row, 1).text(),
                self.tbl_packet_capture.item(row, 2).text(),
                self.tbl_packet_capture.item(row, 3).text(),
                self.tbl_packet_capture.item(row, 4).text(),
                self.tbl_packet_capture.item(row, 5).text(),
            ))

        for packet in packets:
            packet_data = (
                packet["src_ip"],
                str(packet["src_port"]),
                packet["dest_ip"],
                str(packet["dest_port"]),
                packet["protocol"],
                datetime.datetime.fromtimestamp(packet["timestamp"]).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            )
            if packet_data not in existing_rows:
                row_position = self.tbl_packet_capture.rowCount()
                self.tbl_packet_capture.insertRow(row_position)

                self.tbl_packet_capture.setItem(row_position, 0, QTableWidgetItem(packet["src_ip"]))
                self.tbl_packet_capture.setItem(row_position, 1, QTableWidgetItem(str(packet["src_port"])))
                self.tbl_packet_capture.setItem(row_position, 2, QTableWidgetItem(packet["dest_ip"]))
                self.tbl_packet_capture.setItem(row_position, 3, QTableWidgetItem(str(packet["dest_port"])))
                self.tbl_packet_capture.setItem(row_position, 4, QTableWidgetItem(packet["protocol"]))
                self.tbl_packet_capture.setItem(row_position, 5, QTableWidgetItem(packet_data[5]))

