import psutil as pu
import time
from threading import Thread, Event
from queue import Queue
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class ProcessResourceInfo():
    def __init__(self):
        self.core_num = pu.cpu_count()  # 코어 수
        
        # cpu x축과 queue
        self.cpu_data = [0] * 301
        self.cpu_queue = Queue(maxsize=1)
        
        # core x축과 queue
        self.core_data = [[0] * 301 for _ in range(self.core_num)]
        self.core_queue = Queue(maxsize=1)
        
        # disk, net x축
        self.disk_read, self.disk_write = [0] * 301, [0] * 301
        self.net_sent, self.net_recv = [0] * 301, [0] * 301
        
        self.disk_ylabel = ""
        self.net_ylabel = ""

        self.stop_event = Event()
        self.cpu_thread = Thread(target=self.__update_cpu, daemon=True)
        self.core_thread = Thread(target=self.__update_core, daemon=True)
        self.disk_net_thread = Thread(target=self.__update_disk_network, daemon=True)
        
        self.cpu_thread.start()
        self.core_thread.start()
        self.disk_net_thread.start()
    
    def stop_thread(self):
        """
        CPU 계산 스레드 종료.
        """
        self.stop_event.set()
        
        self.cpu_thread.join()
        self.core_thread.join()
        self.disk_net_thread.join()
    
    # 데이터 업데이트 영역
    def __update_cpu(self):
        """
        실시간으로 전체 CPU 사용량 데이터를 업데이트
        """
        while not self.stop_event.is_set():
            cpu_usage = pu.cpu_percent(interval=0.8)  # 전체 CPU 사용량
            if not self.cpu_queue.full():
                self.cpu_queue.put(cpu_usage)
            
    def __update_core(self):
        """
        실시간으로 코어별 CPU 사용량 데이터를 업데이트
        """
        while not self.stop_event.is_set():
            core_percent = pu.cpu_percent(interval=0.8, percpu=True)
            if not self.core_queue.full():
                self.core_queue.put(core_percent)
                
    def __update_memory(self, i, memory_data, swap_data, line_memory, line_swap):
        """
        실시간 메모리 및 스왑 메모리 데이터 업데이트 함수
        """
        # 메모리와 스왑 메모리 사용량 데이터 가져오기
        memory_percent = pu.virtual_memory().percent
        swap_percent = pu.swap_memory().percent

        # 데이터 추가
        memory_data.append(memory_percent)
        memory_data.pop(0)
        line_memory.set_ydata(memory_data)
        
        swap_data.append(swap_percent)
        swap_data.pop(0)
        line_swap.set_ydata(swap_data)

        return [line_memory, line_swap]
    
    def __update_disk_network(self):
        disk_counters = pu.disk_io_counters()
        net_counters = pu.net_io_counters()
        
        read1 = disk_counters.read_bytes
        write1 = disk_counters.write_bytes
        sent1 = net_counters.bytes_sent
        recv1 = net_counters.bytes_recv

        self.disk_ylabel = self.auto_units_ylabel(read1)
        
        while not self.stop_event.is_set():
            time.sleep(0.2)
            disk_counters = pu.disk_io_counters()
            net_counters = pu.net_io_counters()
            
            read2 = disk_counters.read_bytes
            write2 = disk_counters.write_bytes
            sent2 = net_counters.bytes_sent
            recv2 = net_counters.bytes_recv
            
            self.disk_read.append(self.auto_units_number(read2 - read1))
            self.disk_read.pop(0)
            self.disk_write.append(self.auto_units_number(write2 - write1))
            self.disk_write.pop(0)
            self.net_sent.append((sent2 - sent1) / 1024)
            self.net_sent.pop(0)
            self.net_recv.append((recv2 - recv1) / 1024)
            self.net_recv.pop(0)
            
            read1 = read2
            write1 = write2
            sent1 = sent2
            recv1 = recv2
            
            
    
    # 실시간 그래프 영역
    def cpu_realtime_graph(self):
        """
        실시간 전체 CPU 사용량 그래프 생성
        """
        fig, ax = plt.subplots(figsize=(16, 7))
        time_data = [i * 0.2 for i in range(301)]  # X축 시간 데이터


        line_cpu, = ax.plot(time_data, self.cpu_data, lw=0.75, label="CPU Usage (%)")

        # X축 설정
        ax.set_xticks([i for i in range(0, 61, 10)])
        ax.set_xticklabels([f"{60 - i}s" for i in range(0, 61, 10)])

        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda value, pos: f"{int(value)} %" if value != 0 else "")
        )
        ax.yaxis.set_label_position("right")
        ax.yaxis.tick_right()

        ax.grid(True)
        ax.set_ylim(0, 100)
        ax.set_xlim(0, 60)
        ax.set_title("CPU Usage", loc="left", fontsize=18)

        # 범례 추가
        ax.legend(loc="upper left")

        # 여백 없애기
        plt.subplots_adjust(left=0.01, right=0.9, top=0.9, bottom=0.1)
        
        def animate(i):
            try:
                cpu_usage = self.cpu_queue.get_nowait()
            except:
                cpu_usage = self.cpu_data[-1]
                
            self.cpu_data.append(cpu_usage)  # 새 데이터 추가
            self.cpu_data.pop(0)  # 오래된 데이터 제거
            
            line_cpu.set_ydata(self.cpu_data)
            return [line_cpu]
        
        # 애니메이션 생성
        self.cpu_ani = FuncAnimation(fig, animate, interval=200, cache_frame_data=False, blit=True)

        return fig, ax
    
    def core_realtime_graph(self):
        """
        실시간 코어별 CPU 사용량 그래프 생성
        """
        fig, ax = plt.subplots(figsize=(16, 7))
        time_data = [i * 0.2 for i in range(301)]  # X축 시간 데이터

        # 코어별 데이터 라인 생성
        core_lines = [
            ax.plot(time_data, self.core_data[i], lw=0.75, label=f"Core {i + 1}")[0]
            for i in range(self.core_num)
        ]

        # X축 설정
        ax.set_xticks([i for i in range(0, 61, 10)])
        ax.set_xticklabels([f"{60 - i}s" for i in range(0, 61, 10)])

        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda value, pos: f"{int(value)} %" if value != 0 else "")
        )
        ax.yaxis.set_label_position("right")
        ax.yaxis.tick_right()

        ax.grid(True)
        ax.set_ylim(0, 100)
        ax.set_xlim(0, 60)
        ax.set_title("CPU Usage per Core", loc="left", fontsize=18)

        # 범례 추가
        ax.legend(loc="upper left", ncol=2)

        # 여백 없애기
        plt.subplots_adjust(left=0.01, right=0.9, top=0.9, bottom=0.1)

        def animate(i):
            try:
                core_percent = self.core_queue.get_nowait()
            except:
                core_percent = [core[-1] for core in self.core_data]
                
            for k, (core_usage, line) in enumerate(zip(core_percent, core_lines)):
                self.core_data[k].append(core_usage)  # 새 데이터 추가
                self.core_data[k].pop(0)  # 오래된 데이터 제거 
                line.set_ydata(self.core_data[k])      
   
            return core_lines

        # 애니메이션 생성
        self.core_ani = FuncAnimation(fig, animate, interval=200, cache_frame_data=False, blit=True)

        return fig, ax

    def memory_realtime_graph(self):
        """
        실시간 메모리 및 스왑 메모리 그래프 생성 (메모리/스왑 각각 표시)
        """
        fig, ax = plt.subplots(figsize=(16, 7))
        time_data = [i * 0.2 for i in range(301)]  # X축 시간 데이터
        memory_data, swap_data = [0]*301, [0]*301

        line_memory, = ax.plot(time_data, memory_data, lw=0.75, label="Memory Usage (%)")
        line_swap, = ax.plot(time_data, swap_data, lw=0.75, label="Swap Usage (%)")

        # X축 설정
        ax.set_xticks([i for i in range(0, 61, 10)])
        ax.set_xticklabels([f"{60 - i}s" for i in range(0, 61, 10)])

        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda value, pos: f"{int(value)} %" if value != 0 else "")
        )
        ax.yaxis.set_label_position("right")
        ax.yaxis.tick_right()

        ax.grid(True)
        ax.set_ylim(0, 100)
        ax.set_xlim(0, 60)
        ax.set_title("Memory and Swap Usage", loc="left", fontsize=18)

        # 범례 추가
        ax.legend(loc="upper left")

        # 여백없애기
        plt.subplots_adjust(left=0.01, right=0.9, top=0.9, bottom=0.1)

        # 애니메이션 생성
        self.memory_swap_ani = FuncAnimation(
            fig,
            self.__update_memory,
            fargs=(memory_data, swap_data, line_memory, line_swap),
            interval=200,
            cache_frame_data=False,
            blit=True
        )

        return fig, ax

    def disk_realtime_graph(self):
        """
        실시간 디스크 IO 그래프 생성 (읽기/쓰기 각각 표시)
        """
        fig, ax = plt.subplots(figsize=(16, 7))
        time_data = [i * 0.2 for i in range(301)]  # X축 시간 데이터

        # 두 개의 선(line) 생성
        line_read, = ax.plot(time_data, self.disk_read, lw=0.75, label="Read IO")
        line_write, = ax.plot(time_data, self.disk_write, lw=0.75, label="Write IO")

        ax.set_xticks([i for i in range(0, 61, 10)])
        ax.set_xticklabels([f"{60 - i}s" for i in range(0, 61, 10)])

        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, pos: f"{value:.1f} {self.disk_ylabel}" if value != 0 else ""))
        ax.yaxis.set_label_position("right")
        ax.yaxis.tick_right()
        
        ax.grid(True)
        ax.set_ylim(0, 1000)
        ax.set_xlim(0, 60)
        ax.set_title("Disk I/O", loc="left", fontsize=18)

        # 범례 추가
        ax.legend(loc="upper left")
        
        plt.subplots_adjust(left=0.01, right=0.9, top=0.9, bottom=0.1)
        
        def animate(i):
            line_read.set_ydata(self.disk_read)
            line_write.set_ydata(self.disk_write)
            
            return [line_read, line_write]

        self.disk_ani = FuncAnimation(fig, animate, interval=200, cache_frame_data=False, blit=True)

        return fig, ax

    def network_realtime_graph(self):
        """
        실시간 네트워크 송수신량 그래프 생성 (송신/수신 각각 표시)
        """

        fig, ax = plt.subplots(figsize=(16, 7))
        time_data = [i * 0.2 for i in range(301)]  # X축 시간 데이터

        # 송신/수신 선 생성
        line_sent, = ax.plot(time_data, self.net_sent, lw=0.75, label="Sent")
        line_recv, = ax.plot(time_data, self.net_recv, lw=0.75, label="Received")

        # 그래프 설정
        ax.set_xticks([i for i in range(0, 61, 10)])
        ax.set_xticklabels([f"{60 - i}s" for i in range(0, 61, 10)])

        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, pos: f"{value:.1f} KiB/s" if value != 0 else ""))
        ax.yaxis.set_label_position("right")
        ax.yaxis.tick_right()

        ax.grid(True)
        ax.set_ylim(0, 1500)
        ax.set_xlim(0, 60)
        ax.set_title("Network Traffic", loc="left", fontsize=18)

        # 범례 추가
        ax.legend(loc="upper left")
        
        plt.subplots_adjust(left=0.01, right=0.9, top=0.9, bottom=0.1)
        
        def animate(i):
            line_sent.set_ydata(self.net_sent)
            line_recv.set_ydata(self.net_recv)
            return [line_sent, line_recv]

        # FuncAnimation 설정: 송신/수신 데이터를 업데이트
        self.network_ani = FuncAnimation(fig,  animate,  interval=200,  cache_frame_data=False, blit=True)

        return fig, ax

    def auto_units_number(self, num):
        for unit in ['B/s', 'KiB/s', 'MiB/s', 'GiB/s', 'TiB/s', 'PiB/s', 'EiB/s', 'ZiB/s']:
            if abs(num) < 1024.0:
                return num
            num /= 1024.0
        return num
            
    def auto_units_ylabel(self, num):
        for unit in ['B/s', 'KiB/s', 'MiB/s', 'GiB/s', 'TiB/s', 'PiB/s', 'EiB/s', 'ZiB/s']:
            if abs(num) < 1024.0:
                return "%s" % (unit)
            num /= 1024.0
        return "%s" % ('Yi')


# 예시: 주기적으로 시스템 자원 사용량을 딕셔너리로 가져오기
'''
if __name__ == "__main__":
    resource_info = ProcessResourceInfo()
    fig, ax = resource_info.cpu_realtime_graph()
    plt.show()
'''