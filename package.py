from scapy.all import sniff, IP, TCP, UDP

class PacketCollector:
    def __init__(self):
        self.packets_info = []  # 存储捕获的数据包信息
        self.collecting = False

    def start_collection(self, iface=None, filter=None):
        """
        패킷 수집 시작
        :param iface: (str) 패킷 수집할 포트(default: None - 모든 포트)
        :param filter: (str) BPF Filter, 지정할 패킷 종류(default: None)
        """
        self.collecting = True
        print("패킷 수집 시작...")

        # 开始捕获数据包
        sniff(iface=iface, filter=filter, prn=self._process_packet, stop_filter=lambda x: not self.collecting)

    def stop_collection(self):
        """Stop 패킷 수집"""
        self.collecting = False
        print("패킷 수집 멈춤")

    def _process_packet(self, packet):
        """수집된 데이터 처리，IP 헤더와 TCP/UDP 헤더 데이터 추출"""
        if IP in packet:
            ip_header = packet[IP]
            src_ip = ip_header.src
            dst_ip = ip_header.dst

            if TCP in packet:
                tcp_header = packet[TCP]
                src_port = tcp_header.sport
                dst_port = tcp_header.dport
                protocol = "TCP"
            elif UDP in packet:
                udp_header = packet[UDP]
                src_port = udp_header.sport
                dst_port = udp_header.dport
                protocol = "UDP"
            else:
                return  # TCP/UDP 패킷 아니면 SKIP

            # 保存提取的信息
            packet_info = {
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": src_port,
                "dst_port": dst_port,
                "protocol": protocol
            }
            self.packets_info.append(packet_info)
            """ print(packet_info) 출력하기 """
            return packet_info

# 示例用法
if __name__ == "__main__":
    collector = PacketCollector()
    try:
        collector.start_collection()  # 开始捕获所有接口上的数据包
    except KeyboardInterrupt:
        collector.stop_collection()  # 捕获 Ctrl+C 停止捕获
