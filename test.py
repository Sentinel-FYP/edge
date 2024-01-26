from scapy.all import sr, sr1
from scapy.layers.inet import IP, ICMP, TCP
import socket
import ipaddress


def get_network_range():
    # Get the local hostname and IP address
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)

    subnet_mask = "24"
    # Calculate the network range
    network = ipaddress.IPv4Network(f"{ip_address}/{subnet_mask}", strict=False)

    return network


def discover_cameras(network, port=554):
    # Create an IP range to scan
    ip_range = IP(network)

    # Create an ICMP packet for network discovery
    icmp_packet = IP(dst=ip_range) / ICMP()

    # Send the ICMP packet and collect responses
    response, _ = sr(icmp_packet, timeout=2, verbose=0)

    # Extract IP addresses from the responses
    ip_addresses = [resp[1][IP].src for resp in response]

    # Scan each IP address on the specified port
    for ip in ip_addresses:
        print(f"Scanning {ip} on port {port}")
        camera_packet = IP(dst=ip) / TCP(dport=port, flags="S")

        # Send the TCP packet and wait for a response
        response = sr1(camera_packet, timeout=1, verbose=0)

        # Check if the port is open (SYN-ACK received)
        if response and response.haslayer(TCP) and response[TCP].flags == 0x12:
            print(f"Found IP camera at {ip}:{port}")


if __name__ == "__main__":
    # Replace "192.168.1.0/24" with your network range
    discover_cameras(network=get_network_range())
