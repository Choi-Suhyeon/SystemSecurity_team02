import psutil
import time

def print_socket_info():
    while True:
        connections = psutil.net_connections()
        
        print(f"{'PID':<6} {'상태':<12} {'로컬 주소':<30} {'원격 주소'}")
        print("="*80)
        
        for conn in connections:
            pid = conn.pid if conn.pid is not None else "-"
            status = conn.status if conn.status is not None else "-"
            laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "-"
            raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "-"
            print(f"{pid:<6} {status:<12} {laddr:<30} {raddr}")
        
        time.sleep(0.2)

print_socket_info()

