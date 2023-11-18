import socket
import tqdm


CAMS_CACHE_FILE = 'data/cams.txt'


def get_local_ip():
    # Get the local IP address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    try:
        # Doesn't actually send data, just connects
        s.connect(('10.255.255.255', 1))
        local_ip = s.getsockname()[0]
    except socket.error:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return local_ip


def discover_cameras():
    local_ip = get_local_ip()

    # Get the first three octets of the local IP address
    base_ip = ".".join(local_ip.split(".")[:3]) + "."

    # Set the range of ports to scan (adjust as needed)
    port_range = [534, 8534]
    ip_range = range(1, 20)

    cams = []
    print("Discovering cameras on the local network...")
    for i in tqdm.tqdm(ip_range):
        ip = base_ip + str(i)
        for port in port_range:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                sock.connect((ip, port))
                cams.append(f'{ip}:{port}')
            except (socket.timeout, socket.error):
                pass
            finally:
                sock.close()
    cache_to_file(cams)


def cache_to_file(cams: list):
    with open(CAMS_CACHE_FILE, 'w') as f:
        for cam in cams:
            f.write(cam+'\n')
