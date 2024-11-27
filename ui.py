import os
import sys
import re
import time
import psutil
import signal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QTableWidget, QTabBar,
    QWidget, QLineEdit, QPushButton, QTabWidget, QTreeView, QTableView, QHeaderView,
    QAbstractItemView, QMenu, QAction, QTableWidgetItem, QLabel, QTextEdit  # QTextEdit 추가
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

        # 프로세스 정보 초기화
        self.procs = []
        self.regex = ''

        # 메인 레이아웃과 중앙 위젯 설정
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # 탭 위젯 추가
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        self.tabs.addTab(self.get_process_tab(), 'Processes')

        # 유저 스크립트 탭 추가
        self.tabs.addTab(self.init_user_script_tab(), "User Script")  # 유저 스크립트 탭 생성

        self.tabs.addTab(QWidget(), "Resources")
        self.tabs.addTab(QWidget(), "Per-Process Networks")

        # 설정 탭 추가 (탭 버튼 숨김)
        self.tabs.addTab(self.init_settings_tab(), "")  # 설정 탭 생성, 탭 이름 비움
        self.tabs.tabBar().setTabVisible(self.tabs.count() - 1, False)  # 설정 탭 숨기기

        main_layout.addWidget(self.tabs)

        # 설정 버튼 추가
        self.add_settings_button(main_layout)  # Settings 버튼 생성 및 추가

        # 타이머 설정
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
        pid_set = set(i.pid for i in self.procs)
        pi1, pi2 = tee(psutil.process_iter())
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
        self.filter_btn = QPushButton('filter', self)

        self.reg_line_edit.editingFinished.connect(self.filter_process)
        self.filter_btn.clicked.connect(self.filter_process)

        hbox = QHBoxLayout()

        hbox.addWidget(self.reg_line_edit)
        hbox.addWidget(self.filter_btn)

        var_names = [
            'obj', 'name', 'pid', 'user', 'priority', 'cpu (%)',
            'memory (%)', 'Disk Read (KB)', 'Disk Write (KB)',
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

        filtered_procs = filtered if self.regex and (
            filtered := filter_process_by_name(self.procs, self.regex)) is not None else self.procs
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
                self.proc_table.setItem(row_cnt, 9, QTableWidgetItem(''))  # proc.does_exist
                self.proc_table.setItem(row_cnt, 10, QTableWidgetItem(''))  # proc.vt
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

        process_kill_action = QAction('kill process', self)
        check_existence_action = QAction('check file existence', self)
        check_vt_action = QAction('check with virus total', self)

        process_kill_action.triggered.connect(
            lambda: os.kill(int(self.proc_table.item(selected_row, 2).text()), signal.SIGTERM))
        # check_existence_action.triggered.connect()
        # check_vt_action.triggered.connect()

        context_menu.addAction(process_kill_action)
        # context_menu.addAction(check_existence_action)
        # context_menu.addAction(check_vt_action)
        context_menu.exec_(self.proc_table.viewport().mapToGlobal(pos))

    # 유저 스크립트 초기화
    def init_user_script_tab(self):
        self.user_script_tab = QWidget()
        layout = QVBoxLayout(self.user_script_tab)

        # 상단 버튼 레이아웃
        button_layout = QHBoxLayout()

        # 파일 열기 버튼
        open_button = QPushButton("파일 열기")
        open_button.setIcon(self.style().standardIcon(QPushButton().style().SP_DialogOpenButton))  # 아이콘 추가
        button_layout.addWidget(open_button)

        # 파일 저장 버튼
        save_button = QPushButton("파일 저장")
        save_button.setIcon(self.style().standardIcon(QPushButton().style().SP_DialogSaveButton))  # 아이콘 추가
        button_layout.addWidget(save_button)

        # 실행 버튼
        run_button = QPushButton("실행")
        run_button.setIcon(self.style().standardIcon(QPushButton().style().SP_MediaPlay))  # 아이콘 추가
        button_layout.addWidget(run_button)

        # 초기화 버튼
        reset_button = QPushButton("초기화")
        reset_button.setIcon(self.style().standardIcon(QPushButton().style().SP_BrowserReload))  # 아이콘 추가
        button_layout.addWidget(reset_button)

        layout.addLayout(button_layout)

        # 현재 파일 정보 텍스트
        file_info_label = QLabel("현재파일 : example_script.m | 파일 유형 : Matlab(.m)")
        file_info_label.setStyleSheet("font-size: 14px; color: gray;")
        layout.addWidget(file_info_label)

        # 코드 편집기 영역
        code_editor_label = QLabel("코드 편집기")
        code_editor_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        layout.addWidget(code_editor_label)

        code_editor = QTextEdit()
        code_editor.setPlaceholderText("// 사용자 코드 작성 영역")
        layout.addWidget(code_editor)

        # 실행 결과 영역
        result_label = QLabel("실행 결과")
        result_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        layout.addWidget(result_label)

        result_viewer = QTextEdit()
        result_viewer.setPlaceholderText("// 실행 결과 표시 영역(텍스트 or 그래프)")
        result_viewer.setReadOnly(True)
        layout.addWidget(result_viewer)

        # 하단 상태 표시줄
        status_label = QLabel("상태 : 준비 완료")
        status_label.setStyleSheet("font-size: 14px; color: gray; margin-top: 10px;")
        layout.addWidget(status_label)

        return self.user_script_tab

    def init_settings_tab(self):
        self.settings_tab = QWidget()
        layout = QVBoxLayout(self.settings_tab)

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

        return self.settings_tab

    # 설정 버튼
    def add_settings_button(self, layout):
        # Settings 버튼
        settings_button = QPushButton("Settings")
        settings_button.setFixedSize(QSize(100, 40))
        settings_button.clicked.connect(self.navigate_to_settings)  # Settings 탭 이동 연결

        # 버튼 배치
        bottom_layout = QVBoxLayout()
        bottom_layout.addStretch()
        bottom_layout.addWidget(settings_button)

        layout.addLayout(bottom_layout)

    def open_settings(self):
        print("Settings button clicked!")  # Settings 버튼 동작 구현

    def navigate_to_user_script(self):
        user_script_index = self.tabs.indexOf(self.user_script_tab)
        if user_script_index != -1:
            self.tabs.setCurrentIndex(user_script_index)

    def navigate_to_settings(self):
        # 숨겨진 설정 탭으로 이동
        settings_index = self.tabs.indexOf(self.settings_tab)
        if settings_index != -1:
            self.tabs.setCurrentIndex(settings_index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ProcessViewer()
    viewer.show()
    sys.exit(app.exec_())
