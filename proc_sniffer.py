import psutil
from scapy.all import sniff, IP, TCP, UDP

class PacketCollector:
    def __init__(self, pid):
        self.packets_info = []
        self.collecting = False
        self.pid = pid
        self.connections = self._get_connections()

    def _get_connections(self):
        """지정된 PID 모든 패킷 수집"""
        connections = []
        try:
            proc = psutil.Process(self.pid)
            for conn in proc.net_connections(kind="inet"):
                local_ip = conn.laddr.ip
                local_port = conn.laddr.port
                remote_ip = conn.raddr.ip if conn.raddr else None
                remote_port = conn.raddr.port if conn.raddr else None
                connections.append((local_ip, local_port, remote_ip, remote_port))
        except psutil.NoSuchProcess:
            return []  # PID 없을 때 빈 리스트 반환
        return connections

    def start_collection(self, iface=None):
        """ PID 관련 패킷 수집 시작"""
        self.collecting = True
        sniff(iface=iface, prn=self._process_packet, stop_filter=lambda x: not self.collecting)

    def stop_collection(self):
        """패킷 수집 멈춤"""
        self.collecting = False

    def _process_packet(self, packet):
        """수집된 패킷 데이터 처리，IP 헤더과 TCP/UDP 헤더만 추출"""
        if IP in packet:
            ip_header = packet[IP]
            src_ip = ip_header.src
            dst_ip = ip_header.dst

            if TCP in packet:
                transport_header = packet[TCP]
                src_port = transport_header.sport
                dst_port = transport_header.dport
                protocol = "TCP"
            elif UDP in packet:
                transport_header = packet[UDP]
                src_port = transport_header.sport
                dst_port = transport_header.dport
                protocol = "UDP"
            else:
                return

            # 연속 확인
            for (local_ip, local_port, remote_ip, remote_port) in self.connections:
                if ((src_ip == local_ip and src_port == local_port) or
                    (dst_ip == local_ip and dst_port == local_port)) and \
                   ((remote_ip is None) or (src_ip == remote_ip or dst_ip == remote_ip)):
                    packet_info = {
                        "src_ip": src_ip,
                        "dst_ip": dst_ip,
                        "src_port": src_port,
                        "dst_port": dst_port,
                        "protocol": protocol
                    }
                    self.packets_info.append(packet_info)
                    return packet_info

    def get_collected_packets(self):
        """패킷 정보 리턴"""
        return self.packets_info

# 테스트 코드
if __name__ == "__main__":
    pid = 20585  # 실제 PID 대체
    collector = PacketCollector(pid)
    try:
        print("패킷 수집 시작...")
        collector.start_collection()
    except KeyboardInterrupt:
        collector.stop_collection()
        print("패킷 수집 멈춤")

    # 패킷 데이터 추출
    collected_packets = collector.get_collected_packets()
    for packet in collected_packets:
        print(f'|{packet}|', flush=True)
