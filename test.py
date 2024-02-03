from scapy.all import *
from scapy.layers.inet import IP, ICMP, TCP
import socket
import ipaddress


def get_network_ip():
    # Get the local hostname and IP address
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    ip = ip[: ip.rfind(".")] + ".0"
    return ipaddress.ip_address(ip)


def increment_ip(ip):
    ip = ipaddress.ip_address(ip)
    ip += 1
    return str(ip)


def generate_ip_range(max=20):
    if max > 250:
        raise ValueError("Max value cannot exceed 250")
    network_ip = get_network_ip()
    ip = network_ip
    for i in range(max):
        ip = increment_ip(ip)
        yield ip


def find_open_ports(target, ports):
    result = []
    for x in ports:
        packet = IP(dst=target) / TCP(dport=x, flags="S")
        response = sr1(packet, timeout=2, verbose=0)
        if response is not None and TCP in response and response[TCP].flags == 0x12:
            print(f"Port {str(x)} is open!\n")
            result.append(x)
            sr(
                IP(dst=target) / TCP(dport=response.sport, flags="R"),
                timeout=2,
                verbose=0,
            )
    return result


def discover_cameras(max_count=10, ports=[8534]):
    ips = list(generate_ip_range(max_count))
    for ip in ips:
        open_ports = find_open_ports(ip, ports)
        if len(open_ports) > 0:
            print(f"Found camera at {ip} with open ports {open_ports}")


if __name__ == "__main__":
    discover_cameras()
