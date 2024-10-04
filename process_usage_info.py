import psutil as pu
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class Process_Resource_Info():
    def __init__(self):
        self.total_cpu_percent = pu.cpu_percent()           # 전체 CPU 사용량
        self.core_percent = pu.cpu_percent(percpu=True)     # 코어 당 사용량
        self.core_num = pu.cpu_count()                      # 코어 수
        self.memory_usage = pu.virtual_memory()             # 메모리 사용량
        self.swap_usage = pu.swap_memory()                  # 스왑 사용량
        self.disk_io_usage = pu.disk_io_counters()          # 디스크 사용량
    
    def print_system_usage(self):
        '''
        [explain]
            cpu, memory, swap, disk 전체 사용량 모두 출력 (삭제해도 무방한 함수)
        [param] 
            void
        [return]
            void
        '''

        print(f"Total CPU Usage: {self.total_cpu_percent}%")
        print("Each Core Usage:")
        for i in range(self.core_num):
            print(f"core {i+1}: {self.core_percent[i]}%")
            
        print(f"Total Memory Usage: {self.memory_usage.used / (1000 ** 3):.2f} GB / {self.memory_usage.total / (1000 ** 3):.2f} GB [{self.memory_usage.percent}%]")
        print(f"Total Swap Usage: {self.swap_usage.used / (1000 ** 3):.2f} GB / {self.swap_usage.total / (1000 ** 3):.2f} GB [{self.swap_usage.percent}%]")
        print(f"Total Disk I/O: Read={self.disk_io_usage.read_bytes / (1000 ** 3):.2f} GB, Write={self.disk_io_usage.write_bytes / (1000 ** 3):.2f} GB")

    def print_cpu_usage(self):
        '''
        [explain]
            interval 시간 동안의 평균 cpu 전체 사용량 및 코어 당 사용량을 출력
        [param] 
            void
        [return]
            void
        '''
        
        print(f"Total CPU Usage: {self.total_cpu_percent}%")
        print("Each Core Usage:")
        for i in range(self.core_num):
            print(f"core {i+1}: {self.core_percent[i]}%")
        
    def print_memory_usage(self):
        '''
        [explain]
            memory 전체 사용량을 출력
        [param] 
            void
        [return]
            void
        '''
        
        print(f"Total Memory Usage: {self.memory_usage.used / (1000 ** 3):.2f} GB / {self.memory_usage.total / (1000 ** 3):.2f} GB [{self.memory_usage.percent}%]")
        
    def print_swap_usage(self):
        '''
        [explain]
            swap 전체 사용량을 출력
        [param] 
            void
        [return]
            void
        '''
        
        print(f"Total Swap Usage: {self.swap_usage.used / (1000 ** 3):.2f} GB / {self.swap_usage.total / (1000 ** 3):.2f} GB [{self.swap_usage.percent}%]")
        
    def print_disk_usage(self):
        '''
        [explain]
            disk i/o 전체 사용량을 출력
        [param] 
            void
        [return]
            void
        '''
        
        print(f"Total Disk I/O: Read={self.disk_io_usage.read_bytes / (1000 ** 3):.2f} GB, Write={self.disk_io_usage.write_bytes / (1000 ** 3):.2f} GB")
        
    def memory_usage_graph(self, i, time_data, usage_data, line):
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

        ax.set_xlim(0, 60)
        ax.set_xticks(range(0, 61, 10))
        ax.set_xticklabels([str(60 - i) for i in range(0, 61, 10)])
        ax.set_ylim(0, 100)
        ax.set_xlabel("Time")
        ax.set_ylabel("Memory Usage (%)")
        ax.set_title("Real-time Memory Usage")

        ani = FuncAnimation(fig, ex_1.memory_usage_graph, fargs=(time_data, usage_data, line), interval=200, cache_frame_data=False)
        plt.show()


ex_1 = Process_Resource_Info()
ex_1.print_system_usage()
process1 = ex_1.memory_realtime_graph()