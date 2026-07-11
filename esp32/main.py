import json
import socket
import time

from strip import rainbow_all, set_strip

HOST = "192.168.1.100"
PORT = 8765
HEARTBEAT_INTERVAL = 10
FALLBACK_TIMEOUT = 10

_last_recv = time.time()


def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((HOST, PORT))
        print("TCP connected to", HOST)
        return s
    except Exception as e:
        print("TCP connect failed:", e)
        return None


def send_json(sock, msg):
    try:
        sock.sendall((json.dumps(msg) + "\n").encode("utf-8"))
    except Exception:
        pass


def handle_state(regions):
    for r in regions:
        set_strip(r.get("region", 0), r.get("color", "off"))


def run():
    global _last_recv
    sock = connect()
    if sock is None:
        rainbow_all()
        return

    send_json(sock, {"t": "hello"})
    sock.settimeout(1.0)
    buffer = b""
    last_heartbeat = time.time()

    while True:
        try:
            data = sock.recv(4096)
            if data:
                _last_recv = time.time()
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    msg = json.loads(line.decode("utf-8"))
                    t = msg.get("t")
                    if t == "state":
                        handle_state(msg.get("regions", []))
            else:
                break
        except socket.timeout:
            pass
        except Exception as e:
            print("recv error:", e)
            break

        if time.time() - last_heartbeat >= HEARTBEAT_INTERVAL:
            send_json(sock, {"t": "pong"})
            last_heartbeat = time.time()

        if time.time() - _last_recv > FALLBACK_TIMEOUT:
            print("fallback: rainbow")
            rainbow_all()
            _last_recv = time.time()

    sock.close()


while True:
    try:
        run()
    except Exception as e:
        print("run error:", e)
    time.sleep(3)
