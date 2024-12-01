from scapy.all import sniff, IP, TCP, UDP
import psutil
from threading import Thread, Event
import time


class PacketSniffer:
    def __init__(self, pid):
        self.pid = pid
        self.process = psutil.Process(pid)
        self.event = Event()
        self.collected_packets = list()

    def __get_connection_ports(self):
        try:
            connections = self.process.connections(kind='inet')
            return {
                (conn.laddr.ip, conn.laddr.port)
                for conn in connections if conn.status == "ESTABLISHED"
            } | {
                (conn.raddr.ip, conn.raddr.port)
                for conn in connections if conn.raddr and conn.status == "ESTABLISHED"
            }
        except psutil.AccessDenied:
            return set()

    def __filter_packets(self, packet):
        if not packet.haslayer(IP): 
            return False

        if not (packet.haslayer(TCP) or packet.haslayer(UDP)):  
            return False

        connections = self.__get_connection_ports()
        src_ip = packet[IP].src
        dest_ip = packet[IP].dst
        src_port = packet.sport if packet.haslayer(TCP) or packet.haslayer(UDP) else None
        dest_port = packet.dport if packet.haslayer(TCP) or packet.haslayer(UDP) else None

        if (src_ip, src_port) in connections or (dest_ip, dest_port) in connections:
            return True

        return False

    def __packet_handler(self, packet):
        if self.__filter_packets(packet):
            protocol = "TCP" if packet.haslayer(TCP) else "UDP"
            timestamp = time.time()
            self.collected_packets.append({
                "timestamp": timestamp,
                "src_ip": packet[IP].src,
                "src_port": packet.sport,
                "dest_ip": packet[IP].dst,
                "dest_port": packet.dport,
                "protocol": protocol
            })

    def start_sniffing(self):
        self.event.clear()
        self.sniffer_thread = Thread(target=self.__sniff)
        self.sniffer_thread.start()

    def __sniff(self):
        sniff(prn=self.__packet_handler, stop_filter=lambda p: self.event.is_set())

    def stop_sniffing(self):
        self.event.set()
        if self.sniffer_thread.is_alive():
            self.sniffer_thread.join()

    def get_packets(self):
        return self.collected_packets

    def wait_for_packets(self, timeout=10):
        """Wait for packets to be collected for a specified timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.collected_packets:  # If packets have been collected
                break
            time.sleep(0.1)  # Check every 100ms
        return self.collected_packets


'''
# 예시 사용법
if __name__ == "__main__":
    pid = 1234  # 실제 PID로 대체

    # 패킷 스니핑 시작
    sniffer = PacketSniffer(pid)
    sniffer.start_sniffing()

    # 일정 시간 기다린 후 패킷 확인
    time.sleep(5)  # 5초 대기

    # 수집된 패킷 출력
    packets = sniffer.get_packets()
    print(packets)

    # 수집을 멈추고 스레드 종료
    sniffer.stop_sniffing()

'''
