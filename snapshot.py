import psutil
import os
import signal
import hashlib
from datetime import datetime
import process_resource_info
import socket_info
from process import Proc

def get_process_info(proc_class):
    """프로세스 ID, 이름, 상태, CPU 및 메모리 사용량을 반환"""
    return {
        'pid': proc_class.pid,
        'name': proc_class.name(),
        'status': proc_class.status(),
    }

def snapshot_info(proc_class, resource_class, filename='snapshot_log.txt'):
    process_info = get_process_info(proc_class=proc_class)
    system_usage = resource_class.get_system_usage()
    handles_info = proc_class.get_handles_info()
    timestamp = datetime.now().isoformat()
    with open(filename, 'w') as log_file:
        log_file.write(f"===== Snapshot at {timestamp} =====\n\n")
        
        log_file.write("System Resource Usage:\n")
        log_file.write(f"Total CPU Usage: {system_usage['total_cpu_percent']}%\n")
        log_file.write("Core Usage:\n")
        for i, core_percent in enumerate(system_usage['core_percent']):
            log_file.write(f"Core {i + 1}: {core_percent}%\n")
        
        log_file.write(f"Memory Usage: {system_usage['memory_usage']['used']:.2f} GB / {system_usage['memory_usage']['total']:.2f} GB [{system_usage['memory_usage']['percent']}%]\n")
        log_file.write(f"Swap Usage: {system_usage['swap_usage']['used']:.2f} GB / {system_usage['swap_usage']['total']:.2f} GB [{system_usage['swap_usage']['percent']}%]\n")
        log_file.write(f"Disk I/O: Read={system_usage['disk_io_usage']['read_bytes']:.2f} GB, Write={system_usage['disk_io_usage']['write_bytes']:.2f} GB\n\n")

        log_file.write("Process Information:\n")
        log_file.write(f"PID: {process_info['pid']}\n")
        log_file.write(f"Name: {process_info['name']}\n")
        log_file.write(f"Status: {process_info['status']}\n")

        log_file.write("\nFile Handles Information:\n")
        log_file.write(f"Max Open Files (Soft Limit): {handles_info[0]}\n")
        log_file.write("Open Files:\n")
        for handle in handles_info[1]:
            log_file.write(f"{handle}\n")

        log_file.write("\n\n")


# 테스트 코드: 프로그램 시작 시 Proc 객체 생성 후, 스냅샷 호출
if __name__ == "__main__":
    # 프로그램 시작 시 Proc 인스턴스 생성
    proc_instance = Proc(18369)
    # resource_instance = process_resource_info.ProcessResourceInfo()

    # 버튼 클릭 시 호출되는 스냅샷 함수 (테스트 용도로 직접 호출)
    snapshot_info(proc_class=proc_instance)
