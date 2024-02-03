from http.client import ResponseNotReady
from scapy.all import *
from scapy.layers.inet import IP, TCP
import logging

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
import sys


target = "192.168.100.9"
startport = 8534
endport = 8534
print(f"scanning {target} for open TCP ports\n")


def find_open_ports(target, startport, endport):
    result = []
    endport += 1
    for x in range(startport, endport):
        packet = IP(dst=target) / TCP(dport=x, flags="S")
        response = sr1(packet, timeout=0.5, verbose=0)
        if response is not None and TCP in response and response[TCP].flags == 0x12:
            print(f"Port {str(x)} is open!\n")
            result.append(x)
            sr(
                IP(dst=target) / TCP(dport=response.sport, flags="R"),
                timeout=0.5,
                verbose=0,
            )


find_open_ports(target, startport, endport)
