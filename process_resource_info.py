import psutil as pu
import time
import threading

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class ProcessResourceInfo():
    def __init__(self):
        self.core_num = pu.cpu_count() # 코어 수
        self.interval = 0.2
    
    def print_system_usage(self):
        '''
        [explain]
            cpu, memory, swap, disk 전체 사용량 모두 출력 (삭제해도 무방한 함수)
        [param] 
            void
        [return]
            void
        '''

        while True:
            total_cpu_percent = pu.cpu_percent()           # 전체 CPU 사용량
            core_percent = pu.cpu_percent(percpu=True)     # 코어 당 사용량
            memory_usage = pu.virtual_memory()             # 메모리 사용량
            swap_usage = pu.swap_memory()                  # 스왑 사용량
            disk_io_usage = pu.disk_io_counters()          # 디스크 사용량

            print("\033[H\033[J")  # 터미널 화면을 지움 (실시간 업데이트 시 유용)
            print(f"Total CPU Usage: {total_cpu_percent}%")
            print("Each Core Usage:")
            for i in range(self.core_num):
                print(f"core {i+1}: {core_percent[i]}%")

            print(f"Total Memory Usage: {memory_usage.used / (1000 ** 3):.2f} GB / {memory_usage.total / (1000 ** 3):.2f} GB [{memory_usage.percent}%]")
            print(f"Total Swap Usage: {swap_usage.used / (1000 ** 3):.2f} GB / {swap_usage.total / (1000 ** 3):.2f} GB [{swap_usage.percent}%]")
            print(f"Total Disk I/O: Read={disk_io_usage.read_bytes / (1000 ** 3):.2f} GB, Write={disk_io_usage.write_bytes / (1000 ** 3):.2f} GB")
            
            time.sleep(self.interval)  # interval 초 동안 대기 후 정보 갱신

    def print_cpu_usage(self):
        '''
        [explain]
            실시간 cpu 전체 사용량 및 코어 당 사용량을 출력
        [param] 
            void
        [return]
            void
        '''
        
        while True:
            total_cpu_percent = pu.cpu_percent()           # 전체 CPU 사용량
            core_percent = pu.cpu_percent(percpu=True)     # 코어 당 사용량

            print("\033[H\033[J")
            print(f"Total CPU Usage: {total_cpu_percent}%")
            print("Each Core Usage:")
            for i in range(self.core_num):
                print(f"core {i+1}: {core_percent[i]}%")
            
            time.sleep(self.interval)
        
    def print_memory_usage(self):
        '''
        [explain]
            실시간 memory 전체 사용량을 출력
        [param] 
            void
        [return]
            void
        '''
        
        while True:
            memory_usage = pu.virtual_memory()  # 메모리 사용량 갱신
            print("\033[H\033[J")
            print(f"Total Memory Usage: {memory_usage.used / (1000 ** 3):.2f} GB / {memory_usage.total / (1000 ** 3):.2f} GB [{memory_usage.percent}%]")
            time.sleep(self.interval)
        
    def print_swap_usage(self):
        '''
        [explain]
            실시간 swap 전체 사용량을 출력
        [param] 
            void
        [return]
            void
        '''
        
        while True:
            swap_usage = pu.swap_memory()  # 스왑 사용량 갱신
            print("\033[H\033[J")
            print(f"Total Swap Usage: {swap_usage.used / (1000 ** 3):.2f} GB / {swap_usage.total / (1000 ** 3):.2f} GB [{swap_usage.percent}%]")
            time.sleep(self.interval)
        
    def print_disk_usage(self):
        '''
        [explain]
            실시간 disk i/o 전체 사용량을 출력
        [param] 
            void
        [return]
            void
        '''
        
        while True:
            disk_io_usage = pu.disk_io_counters()  # 디스크 I/O 사용량 갱신
            print("\033[H\033[J")
            print(f"Total Disk I/O: Read={disk_io_usage.read_bytes / (1000 ** 3):.2f} GB, Write={disk_io_usage.write_bytes / (1000 ** 3):.2f} GB")
            time.sleep(self.interval)
        
    def __memory_usage_graph(self, i, time_data, usage_data, line):
        '''
        [explain]
            실시간 데이터 업데이트 함수
        [param]
            i : 실시간 그래프 함수에서 필수로 넣는 실행 횟수값 (필수 사용 X)
            x_data : 시간축 데이터 60초를 0.2초씩 나눔
            y_data : 메모리 사용량 데이터
        [return]
            line : 업데이트된 그래프 선
        '''
        
        memory_percent = pu.virtual_memory().percent
        usage_data.append(memory_percent)
        
        time_data = time_data[-301:]
        usage_data = usage_data[-301:]
        
        line.set_data(time_data, usage_data)

        return line
    
    def memory_realtime_graph(self):
        '''
        [explain]
            실시간 메모리 사용량 데이터 그래프 출력 함수
        [param] 
            void
        [return]
            void
        '''
        
        fig, ax = plt.subplots(figsize=(16, 7))
        time_data, usage_data = [i * 0.2 for i in range(301)], [0]*301
        line, = ax.plot(time_data, usage_data, lw=2)

        ax.set_xticklabels([str(60 - i) for i in range(0, 61, 10)])
        ax.set_ylim(0, 100)
        ax.set_xlabel("Time")
        ax.set_ylabel("Memory Usage (%)")
        ax.set_title("Real-time Memory Usage")

        ani = FuncAnimation(fig, self.__memory_usage_graph, fargs=(time_data, usage_data, line), interval=200, cache_frame_data=False)
        plt.show()


ex_1 = ProcessResourceInfo()
system_usage_thread = threading.Thread(target=ex_1.print_system_usage)
system_usage_thread.daemon = True  # 메인 스레드가 종료되면 이 스레드도 자동 종료됨
system_usage_thread.start()

process1 = ex_1.memory_realtime_graph()
