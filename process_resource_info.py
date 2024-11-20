import psutil as pu
import time
import threading

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class ProcessResourceInfo():
    def __init__(self):
        self.core_num = pu.cpu_count()  # 코어 수
        self.interval = 0.2

    def get_system_usage(self):
        '''
        [explain]
            cpu, memory, swap, disk 전체 사용량을 딕셔너리 형태로 반환
        [param] 
            void
        [return]
            dict : 시스템 자원 사용 정보를 포함한 딕셔너리
        '''

        # CPU 및 메모리, 스왑, 디스크 사용량 정보 수집
        total_cpu_percent = pu.cpu_percent()           # 전체 CPU 사용량
        core_percent = pu.cpu_percent(percpu=True)     # 코어 당 사용량
        memory_usage = pu.virtual_memory()             # 메모리 사용량
        swap_usage = pu.swap_memory()                  # 스왑 사용량
        disk_io_usage = pu.disk_io_counters()          # 디스크 사용량

        # 딕셔너리에 시스템 자원 사용량 저장
        resource_info = {
            "total_cpu_percent": total_cpu_percent,
            "core_percent": core_percent,
            "memory_usage": {
                "used": memory_usage.used / (1000 ** 3),  # GB 단위로 변환
                "total": memory_usage.total / (1000 ** 3),
                "percent": memory_usage.percent
            },
            "swap_usage": {
                "used": swap_usage.used / (1000 ** 3),
                "total": swap_usage.total / (1000 ** 3),
                "percent": swap_usage.percent
            },
            "disk_io_usage": {
                "read_bytes": disk_io_usage.read_bytes / (1000 ** 3),
                "write_bytes": disk_io_usage.write_bytes / (1000 ** 3)
            }
        }

        return resource_info
        
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



# 예시: 주기적으로 시스템 자원 사용량을 딕셔너리로 가져오기

'''
if __name__ == "__main__":
    resource_info = ProcessResourceInfo()
    while True:
        usage = resource_info.get_system_usage()
        print(usage)  # 딕셔너리 형태의 시스템 자원 사용량 출력
        time.sleep(resource_info.interval)
        
    system_usage_thread = threading.Thread(target=ex_1.print_system_usage)
    system_usage_thread.daemon = True  # 메인 스레드가 종료되면 이 스레드도 자동 종료됨
    system_usage_thread.start()

    process1 = resource_info.memory_realtime_graph()
'''
