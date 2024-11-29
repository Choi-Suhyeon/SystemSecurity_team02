import psutil
import time
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QTabWidget, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from process_resource_info import ProcessResourceInfo
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class realtime_graph(QTabWidget):
    def __init__(self):
        super().__init__()        
        # 그래프 객체 초기화
        self.resource_info = ProcessResourceInfo()
        self.init_threads()
        self.init_graphs()
        
        self.get_resource_tab()
    
    def init_threads(self):
        # CPU Thread
        self.cpu_thread = CPUThread()
        self.cpu_thread.cpu_signal.connect(self.update_cpu_info)
        self.cpu_thread.start()

        # Core Thread
        self.core_thread = CoreThread()
        self.core_thread.core_signal.connect(self.update_core_info)
        self.core_thread.start()

        # Memory Thread
        self.memory_thread = MemoryThread()
        self.memory_thread.memory_signal.connect(self.update_memory_info)
        self.memory_thread.start()

        # Disk Thread
        self.disk_thread = DiskThread()
        self.disk_thread.disk_signal.connect(self.update_disk_info)
        self.disk_thread.start()

        # Network Thread
        self.network_thread = NetworkThread()
        self.network_thread.network_signal.connect(self.update_network_info)
        self.network_thread.start()        

    def init_graphs(self):
        # 실시간 그래프 미리 초기화
        # 요약 예정
        # cpu 예정
        self.cpu_fig, self.cpu_ax = self.resource_info.cpu_realtime_graph()
        self.core_fig, self.core_ax = self.resource_info.core_realtime_graph()
        self.memory_fig, self.memory_ax = self.resource_info.memory_realtime_graph()
        self.disk_fig, self.disk_ax = self.resource_info.disk_realtime_graph()
        self.network_fig, self.network_ax = self.resource_info.network_realtime_graph()
        
        # 캔버스 생성
        self.cpu_canvas = FigureCanvas(self.cpu_fig)
        self.core_canvas = FigureCanvas(self.core_fig)
        self.memory_canvas = FigureCanvas(self.memory_fig)
        self.disk_canvas = FigureCanvas(self.disk_fig)
        self.network_canvas = FigureCanvas(self.network_fig)

    # 전체 탭 생성
    def get_resource_tab(self):
        self.addTab(self.create_summary_tab(), 'Summary')
        self.addTab(self.create_cpu_tab(), 'CPU')
        self.addTab(self.create_memory_tab(), 'Memory')
        self.addTab(self.create_disk_tab(), 'Disk')
        self.addTab(self.create_network_tab(), 'Network')
    
    # summary 탭
    def create_summary_tab(self):
        all_graph = ProcessResourceInfo()
        
        cpu_fig, cpu_ax = all_graph.cpu_realtime_graph()
        memory_fig, memory_ax = all_graph.memory_realtime_graph()
        disk_fig, disk_ax = all_graph.disk_realtime_graph()
        network_fig, network_ax = all_graph.network_realtime_graph()
        
        cpu_canvas = FigureCanvas(cpu_fig)
        memory_canvas = FigureCanvas(memory_fig)
        disk_canvas = FigureCanvas(disk_fig)
        network_canvas = FigureCanvas(network_fig)
        
        
        for fig, ax in [(cpu_fig, cpu_ax), (memory_fig, memory_ax), (disk_fig, disk_ax), (network_fig, network_ax)]:
            fig.subplots_adjust(left=0.01, right=0.9, top=0.85, bottom=0.15)  # 여백 조정
            ax.set_title(ax.get_title(), fontsize=14)

        for canvas in [cpu_canvas, memory_canvas, disk_canvas, network_canvas]:
            canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 크기 조정 가능
            canvas.setMaximumSize(1600, 250)  # 최대 크기
        
        summary_tab = QWidget()
        main_out_layout = QHBoxLayout()
        
        # 그래프 레이아웃
        summary_graph_layout = QVBoxLayout()
        
        summary_graph_layout.addStretch(1)
        summary_graph_layout.addWidget(cpu_canvas)
        summary_graph_layout.addSpacing(10)
        summary_graph_layout.addWidget(memory_canvas)
        summary_graph_layout.addSpacing(10)
        summary_graph_layout.addWidget(disk_canvas)
        summary_graph_layout.addSpacing(10)
        summary_graph_layout.addWidget(network_canvas)
        summary_graph_layout.addStretch(1)
        
        # 바깥 메인 레이아웃
        main_out_layout.addStretch(1)
        main_out_layout.addLayout(summary_graph_layout)
        main_out_layout.addStretch(3)
        
        # 탭에 추가
        summary_tab.setLayout(main_out_layout)
        return summary_tab
        
    # cpu, core 탭
    def create_cpu_tab(self):
        self.cpu_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 크기 조정 가능
        self.cpu_canvas.setMaximumSize(1600, 300)  # 최대 크기   
        self.core_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 크기 조정 가능
        self.core_canvas.setMaximumSize(1600, 300)  # 최대 크기        
        
        cpu_tab = QWidget()
        main_in_layout = QVBoxLayout()
        main_out_layout = QHBoxLayout()
        
        # 그래프 레이아웃
        cpu_core_graph_layout = QVBoxLayout()
        cpu_core_graph_layout.addSpacing(3)
        cpu_core_graph_layout.addWidget(self.cpu_canvas)
        cpu_core_graph_layout.addSpacing(12)
        cpu_core_graph_layout.addWidget(self.core_canvas)
        
        # 정보 레이아웃
        info_layout = QHBoxLayout()
        info_layout.setAlignment(Qt.AlignLeft)
        
        self.cpu_info_label = QLabel()
        self.cpu_info_label.setAlignment(Qt.AlignLeft)
        self.core_info_label = QLabel()
        self.core_info_label.setAlignment(Qt.AlignLeft)        
        
        info_layout.addWidget(self.cpu_info_label)
        info_layout.addSpacing(75)
        info_layout.addWidget(self.core_info_label)
        
        # 안쪽 메인 레이아웃
        main_in_layout.addStretch(1)
        main_in_layout.addLayout(cpu_core_graph_layout)
        main_in_layout.addSpacing(20)
        main_in_layout.addLayout(info_layout)
        main_in_layout.addStretch(1)
        
        # 바깥 메인 레이아웃
        main_out_layout.addStretch(1)
        main_out_layout.addLayout(main_in_layout)
        main_out_layout.addStretch(3)
        
        # 탭에 추가
        cpu_tab.setLayout(main_out_layout)
        return cpu_tab
    
    def update_cpu_info(self, cpu_percent):
        """ cpu 업데이트 """
        
        cpu_info_text = (
            "<b style='font-size:20px;'>CPU Info</b>"
            "<table style='border-collapse:collapse; width:100%; font-size:20px;'>"
            f"<tr><td style='padding-right:10px;'>Rate:</td><td>{cpu_percent:.1f} %</td></tr>"
            "</table>"
        )
        self.cpu_info_label.setText(cpu_info_text)

    def update_core_info(self, core_percent):
        """ core 업데이트 """
        
        core_info_text = (
            "<b style='font-size:20px;'>Core Info</b>"
            "<table style='border-collapse:collapse; width:100%; font-size:20px;'>"
        )

        for i, percent in enumerate(core_percent):
            core_info_text += (
                f"<tr>"
                f"<td style='padding-right:10px;'>Core {i + 1}:</td>"
                f"<td>{percent:.1f} %</td>"
                f"</tr>"
            )
        self.core_info_label.setText(core_info_text)    
    
    # memory, swap 탭
    def create_memory_tab(self):
        self.memory_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 크기 조정 가능
        self.memory_canvas.setMaximumSize(1600, 700)  # 최대 크기   
        
        memory_tab = QWidget()
        main_in_layout = QVBoxLayout()
        main_out_layout = QHBoxLayout()
        
        # 그래프 레이아웃
        memory_graph_layout = QHBoxLayout()
        memory_graph_layout.addWidget(self.memory_canvas)
        
        # 정보 레이아웃
        info_layout = QHBoxLayout()
        info_layout.setAlignment(Qt.AlignLeft)
        
        self.memory_info_label = QLabel()
        self.memory_info_label.setAlignment(Qt.AlignLeft)
        self.swap_info_label = QLabel()
        self.swap_info_label.setAlignment(Qt.AlignLeft)        
        
        info_layout.addWidget(self.memory_info_label)
        info_layout.addSpacing(75)
        info_layout.addWidget(self.swap_info_label)
    
        # 안쪽 메인 레이아웃
        main_in_layout.addStretch(1)
        main_in_layout.addLayout(memory_graph_layout)
        #main_in_layout.addSpacing(10)
        main_in_layout.addLayout(info_layout)
        main_in_layout.addStretch(1)

        # 바깥 메인 레이아웃
        main_out_layout.addStretch(1)
        main_out_layout.addLayout(main_in_layout)
        main_out_layout.addStretch(3)
        
        # 탭에 추가
        memory_tab.setLayout(main_out_layout)
        return memory_tab
    
    def update_memory_info(self, info):
        """ memory, swap 업데이트 """
        
        # 메모리 부분
        memory_used = info["memory"]["used"]
        memory_total = info["memory"]["total"]
        memory_percent = info["memory"]["percent"]
        memory_cached = info["memory"]["cached"]
        
        memory_info_text = (
            "<b style='font-size:20px;'>Memory Info</b>"
            "<table style='border-collapse:collapse; width:100%; font-size:20px;'>"
            f"<tr><td style='padding-right:10px;'>Usage:</td><td>{memory_used:.1f} / {memory_total:.1f} GB [ {memory_percent:.1f} % ]</td></tr>"
            f"<tr><td style='padding-right:10px;'>Cache:</td><td>{memory_cached:.1f} GB</td></tr>"
            "</table>"
        )
        self.memory_info_label.setText(memory_info_text)

        # 스왑 부분
        swap_used = info["swap"]["used"]
        swap_total = info["swap"]["total"]
        swap_percent = info["swap"]["percent"]
        swap_in = info["swap"]["sin"]
        swap_out = info["swap"]["sout"]

        swap_info_text = (
            "<b style='font-size:20px';>Swap Info</b>"
            "<table style='border-collapse:collapse; width:100%; font-size:20px;'>"
            f"<tr><td style='padding-right:10px;'>Usage:</td><td>{swap_used:.1f} / {swap_total:.1f} GB [ {swap_percent:.1f} % ]</td></tr>"
            f"<tr><td style='padding-right:10px;'>Swap IN:</td><td>{swap_in:.1f} GB</td></tr>"
            f"<tr><td style='padding-right:10px;'>Swap OUT:</td><td>{swap_out:.1f} GB</td></tr>"
            "</table>"
        )
        self.swap_info_label.setText(swap_info_text)
    
    # disk 탭
    def create_disk_tab(self):
        self.disk_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 크기 조정 가능
        self.disk_canvas.setMaximumSize(1600, 700)  # 최대 크기   
        
        disk_tab = QWidget()
        main_in_layout = QVBoxLayout()
        main_out_layout = QHBoxLayout()

        # 그래프 레이아웃
        disk_graph_layout = QHBoxLayout()
        disk_graph_layout.addWidget(self.disk_canvas)

        # 정보 레이아웃
        info_layout = QHBoxLayout()
        info_layout.setAlignment(Qt.AlignLeft)

        self.disk_usage_info_label = QLabel()
        self.disk_usage_info_label.setAlignment(Qt.AlignLeft)
        self.disk_io_info_label = QLabel()
        self.disk_io_info_label.setAlignment(Qt.AlignLeft)

        info_layout.addWidget(self.disk_usage_info_label)
        info_layout.addSpacing(75)
        info_layout.addWidget(self.disk_io_info_label)

        # 안쪽 메인 레이아웃
        main_in_layout.addStretch(1)
        main_in_layout.addLayout(disk_graph_layout)
        #main_in_layout.addSpacing(10)
        main_in_layout.addLayout(info_layout)
        main_in_layout.addStretch(1)

        # 바깥 메인 레이아웃
        main_out_layout.addStretch(1)
        main_out_layout.addLayout(main_in_layout)
        main_out_layout.addStretch(3)

        # 탭에 추가
        disk_tab.setLayout(main_out_layout)
        return disk_tab
    
    def update_disk_info(self, info):
        """ disk 업데이트 """
        
        disk_used = info["disk_usage"]["used"]
        disk_total = info["disk_usage"]["total"]
        disk_percent = info["disk_usage"]["percent"]

        disk_usage_info_text = (
            "<b style='font-size:20px';>Disk Usage Info</b>"
            "<table style='border-collapse:collapse; width:100%; font-size:20px;'>"
            f"<tr><td style='padding-right:10px;'>Usage:</td><td>{disk_used:.1f} / {disk_total:.1f} GB [ {disk_percent:.1f} % ]</td></tr>"
            "</table>"
        )
        self.disk_usage_info_label.setText(disk_usage_info_text)

        read_c = self.auto_units(info["disk_io"]["read_count"])[:-2]
        write_c = self.auto_units(info["disk_io"]["write_count"])[:-2]
        read_b_speed = self.auto_units(info["disk_io"]["read_bytes_speed"])
        write_b_speed = self.auto_units(info["disk_io"]["write_bytes_speed"])
        
        disk_io_info_text = (
            "<b style='font-size:20px;'>Disk I/O Info</b>"
            "<table style='border-collapse:collapse; width:100%; font-size:20px;'>"
            f"<tr><td style='padding-right:10px;'>Read Count:</td><td>{read_c}</td></tr>"
            f"<tr><td style='padding-right:10px;'>Write Count:</td><td>{write_c}</td></tr>"
            f"<tr><td style='padding-right:10px;'>Read Bytes Speed:</td><td>{read_b_speed}</td></tr>"
            f"<tr><td style='padding-right:10px;'>Write Bytes Speed:</td><td>{write_b_speed}</td></tr>"
            "</table>"
        )
        self.disk_io_info_label.setText(disk_io_info_text)

    # network 탭
    def create_network_tab(self):
        self.network_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 크기 조정 가능
        self.network_canvas.setMaximumSize(1600, 700)  # 최대 크기   
        
        network_tab = QWidget()
        main_in_layout = QVBoxLayout()
        main_out_layout = QHBoxLayout()

        # 그래프 레이아웃
        network_graph_layout = QHBoxLayout()
        network_graph_layout.addWidget(self.network_canvas)

        # 정보 레이아웃
        info_layout = QHBoxLayout()
        info_layout.setAlignment(Qt.AlignLeft)

        self.network_usage_info_label = QLabel()
        self.network_usage_info_label.setAlignment(Qt.AlignLeft)
        self.network_speed_info_label = QLabel()
        self.network_speed_info_label.setAlignment(Qt.AlignLeft)

        info_layout.addWidget(self.network_usage_info_label)
        info_layout.addSpacing(75)
        info_layout.addWidget(self.network_speed_info_label)

        # 안쪽 메인 레이아웃
        main_in_layout.addStretch(1)
        main_in_layout.addLayout(network_graph_layout)
        #main_in_layout.addSpacing(10)
        main_in_layout.addLayout(info_layout)
        main_in_layout.addStretch(1)

        # 바깥 메인 레이아웃
        main_out_layout.addStretch(1)
        main_out_layout.addLayout(main_in_layout)
        main_out_layout.addStretch(3)

        # 탭에 추가
        network_tab.setLayout(main_out_layout)
        return network_tab

    def update_network_info(self, info):
        """ network 업데이트 """

        bytes_sent = self.auto_units(info["bytes_sent"])[:-2]
        bytes_recv = self.auto_units(info["bytes_recv"])[:-2]
        network_usage_info_text = (
            "<b style='font-size:20px;'>Network Usage Info</b>"
            "<table style='border-collapse:collapse; width:100%; font-size:20px;'>"
            f"<tr><td style='padding-right:10px;'>Sent Bytes:</td><td>{bytes_sent}</td></tr>"
            f"<tr><td style='padding-right:10px;'>Recv Bytes:</td><td>{bytes_recv}</td></tr>"
            "</table>"
        )
        self.network_usage_info_label.setText(network_usage_info_text)


        sent_speed = self.auto_units(info["sent_speed"])
        recv_speed = self.auto_units(info["recv_speed"])
        network_speed_info_text = (
            "<b style='font-size:20px;'>Network Speed Info</b>"
            "<table style='border-collapse:collapse; width:100%; font-size:20px;'>"
            f"<tr><td style='padding-right:10px;'>Sent Speed:</td><td>{sent_speed}</td></tr>"
            f"<tr><td style='padding-right:10px;'>Recv Speed:</td><td>{recv_speed}</td></tr>"
            "</table>"
        )
        self.network_speed_info_label.setText(network_speed_info_text)

    def auto_units(self, num):
        for unit in ['B/s','KiB/s','MiB/s','GiB/s','TiB/s','PiB/s','EiB/s','ZiB/s']:
            if (abs(num) < 1024.0):
                return "%.1f %s" % (num, unit)
            num /= 1024.0
        return "%.1f %s" % (num, 'Yi')
        
    def closeEvent(self, event):
        """
        창이 닫힐 때 스레드 종료.
        """
        # 리소스 업데이트 종료
        self.cpu_thread.terminate()
        self.core_thread.terminate()
        self.memory_thread.terminate()
        self.disk_thread.terminate()
        self.network_thread.terminate()
        
        # 그래프 종료
        self.resource_info.stop_thread()
        event.accept()

# ---------------------- QThread Classes ---------------------- #
class CPUThread(QThread):
    cpu_signal = pyqtSignal(float)

    def run(self):
        while True:
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_signal.emit(cpu_percent)

class CoreThread(QThread):
    core_signal = pyqtSignal(list)

    def run(self):
        while True:
            core_percent = psutil.cpu_percent(interval=1, percpu=True)
            self.core_signal.emit(core_percent)

class MemoryThread(QThread):
    memory_signal = pyqtSignal(dict)

    def run(self):
        while True:
            memory_usage = psutil.virtual_memory()
            swap_usage = psutil.swap_memory()
            
            info = {
                "memory": {
                    "used": memory_usage.used / (1000 ** 3),  # GB 단위로 변환
                    "total": memory_usage.total / (1000 ** 3),
                    "percent": memory_usage.percent,
                    "cached" : memory_usage.cached / (1000 ** 3)
                },
                "swap": {
                    "used": swap_usage.used / (1000 ** 3),
                    "total": swap_usage.total / (1000 ** 3),
                    "percent": swap_usage.percent,
                    "sin" : swap_usage.sin / (1000 ** 3),
                    "sout" : swap_usage.sout / (1000 ** 3)
                }
            }
        
            self.memory_signal.emit(info)
            time.sleep(1)

class DiskThread(QThread):
    disk_signal = pyqtSignal(dict)

    def run(self):
        disk_io = psutil.disk_io_counters()
        read1 = disk_io.read_bytes
        write1 = disk_io.write_bytes
        
        while True:
            time.sleep(1)
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            read2 = disk_io.read_bytes
            write2 = disk_io.write_bytes
            
            info = {
                "disk_usage": {
                    "used" : disk_usage.used / (1000 ** 3),
                    "total" : disk_usage.total / (1000 ** 3),                
                    "percent": disk_usage.percent
                },
                "disk_io": {
                    "read_count" : disk_io.read_count,
                    "write_count" : disk_io.write_count,                
                    "read_bytes_speed": read2 - read1,
                    "write_bytes_speed": write2 - write1
                }
            }
            
            read1 = read2
            write1 = write2
            
            self.disk_signal.emit(info)

class NetworkThread(QThread):
    network_signal = pyqtSignal(dict)

    def run(self):
        network_usage = psutil.net_io_counters()
        sent1 = network_usage.bytes_sent
        write1 = network_usage.bytes_recv
        
        while True:
            time.sleep(1)
            network_usage = psutil.net_io_counters()
            sent2 = network_usage.bytes_sent
            write2 = network_usage.bytes_recv
            
            network_info = {
                "bytes_sent" : sent2,
                "bytes_recv" : write2,
                "sent_speed" : sent2 - sent1,
                "recv_speed" : write2 - write1
            }
            
            sent1 = sent2
            write1 = write2
            
            self.network_signal.emit(network_info)
