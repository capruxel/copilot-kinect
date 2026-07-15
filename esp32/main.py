import json
import select
import socket
import time

from strip import breathe_all, set_led

HOST = "172.20.10.6"
PORT = 8765
HEARTBEAT_INTERVAL = 10
FALLBACK_TIMEOUT = 10
RECONNECT_DELAY_MS = 3000
CONNECT_TIMEOUT_MS = 5000

_last_recv = time.time()


def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setblocking(False)
    try:
        s.connect((HOST, PORT))
    except OSError:
        pass

    poller = select.poll()
    poller.register(s, select.POLLOUT)
    deadline = time.ticks_add(time.ticks_ms(), CONNECT_TIMEOUT_MS)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        breathe_all()
        events = poller.poll(100)
        if not events:
            continue
        event = events[0][1]
        if event & select.POLLOUT and not event & (select.POLLERR | select.POLLHUP):
            s.setblocking(True)
            print("TCP connected to", HOST)
            return s
        break

    print("TCP connect failed")
    s.close()
    return None


def send_json(sock, msg):
    try:
        sock.sendall((json.dumps(msg) + "\n").encode("utf-8"))
    except Exception:
        pass


def handle_state(regions):
    for r in regions:
        set_led(r.get("region", 0), r.get("color", "off"))


def fallback_delay():
    for _ in range(RECONNECT_DELAY_MS // 100):
        breathe_all()
        time.sleep_ms(100)


def run():
    global _last_recv
    sock = connect()
    if sock is None:
        fallback_delay()
        return

    send_json(sock, {"t": "hello"})
    poller = select.poll()
    poller.register(sock, select.POLLIN)
    buffer = b""
    last_heartbeat = time.time()
    fallback_active = False

    while True:
        try:
            if poller.poll(100):
                data = sock.recv(4096)
                if data:
                    _last_recv = time.time()
                    fallback_active = False
                    buffer += data
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        msg = json.loads(line.decode("utf-8"))
                        t = msg.get("t")
                        if t == "state":
                            handle_state(msg.get("regions", []))
                else:
                    break
        except Exception as e:
            print("recv error:", e)
            break

        if time.time() - last_heartbeat >= HEARTBEAT_INTERVAL:
            send_json(sock, {"t": "pong"})
            last_heartbeat = time.time()

        if time.time() - _last_recv > FALLBACK_TIMEOUT:
            if not fallback_active:
                print("fallback: blue breathing")
                fallback_active = True
            breathe_all()

    sock.close()


while True:
    try:
        run()
    except Exception as e:
        print("run error:", e)
        fallback_delay()
