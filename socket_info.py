import psutil
import time

def print_socket_info():
    '''
    [explain]
        실시간 socket 정보를 출력
    [param] 
        void
    [return]
        void
    '''
    
    while True:
        tcp_connections = psutil.net_connections(kind="tcp")
        udp_connections = psutil.net_connections(kind="udp")

        print("\033[H\033[J")

        # TCP 연결 정보 출력
        print("TCP Connections:")
        print(f"{'PID':<6} {'상태':<12} {'로컬 주소':<30} {'원격 주소'}")
        print("="*80)
        for conn in tcp_connections:
            laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "-"
            raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "-"
            pid = conn.pid if conn.pid else "-"
            status = conn.status if conn.status else "-"
            print(f"{pid:<6} {status:<12} {laddr:<30} {raddr}")

        # UDP 연결 정보 출력
        print("\nUDP Connections:")
        print(f"{'PID':<6} {'로컬 주소':<30} {'원격 주소'}")
        print("="*80)
        for conn in udp_connections:
            laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "-"
            raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "-"
            pid = conn.pid if conn.pid else "-"
            print(f"{pid:<6} {laddr:<30} {raddr}")

        time.sleep(0.2)

print_socket_info()