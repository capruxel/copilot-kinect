import atexit
import json
import os
import socket
import threading
import time


class MockLedDriver:
    def __init__(self, log_path="data/led_strip_log.jsonl"):
        self.log_path = log_path
        self._last_state = []
        self._last_update = 0.0
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)

    def update(self, region_states):
        with self._lock:
            self._last_state = list(region_states)
            self._last_update = time.time()
        entry = {"t": self._last_update, "regions": region_states}
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_status(self):
        with self._lock:
            return {
                "driver": "mock",
                "last_update": self._last_update,
                "region_states": self._last_state,
            }

    def close(self):
        pass


class TcpLedStripDriver:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self._server = None
        self._client = None
        self._lock = threading.Lock()
        self._last_state = []
        self._last_update = 0.0
        self._last_push = 0.0
        self._running = False
        self._thread = None
        atexit.register(self.close)

    def start(self):
        self._running = True
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind((self.host, self.port))
        self._server.listen(1)
        self._server.settimeout(1.0)
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()

    def _accept_loop(self):
        while self._running:
            try:
                conn, _addr = self._server.accept()
                self._handle_client(conn)
            except socket.timeout:
                continue
            except Exception:
                if self._running:
                    time.sleep(1.0)

    def _handle_client(self, conn):
        conn.settimeout(1.0)
        buffer = b""
        with self._lock:
            self._client = conn
        try:
            if self._last_state:
                self._send_state(conn)
            while self._running:
                try:
                    data = conn.recv(4096)
                    if not data:
                        break
                    buffer += data
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        msg = json.loads(line.decode("utf-8"))
                        if msg.get("t") == "hello":
                            self._send_state(conn)
                except socket.timeout:
                    self._send_state(conn)
                    continue
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                except Exception:
                    break
        finally:
            with self._lock:
                self._client = None
            try:
                conn.close()
            except Exception:
                pass

    def _send_state(self, conn):
        with self._lock:
            state = self._last_state
        if not state:
            return
        msg = json.dumps({"t": "state", "regions": state}, ensure_ascii=False) + "\n"
        try:
            conn.sendall(msg.encode("utf-8"))
            self._last_push = time.time()
        except Exception:
            pass

    def update(self, region_states):
        with self._lock:
            self._last_state = list(region_states)
            self._last_update = time.time()
            conn = self._client
        if conn is not None:
            self._send_state(conn)

    def get_status(self):
        with self._lock:
            return {
                "driver": "tcp",
                "host": self.host,
                "port": self.port,
                "connected": self._client is not None,
                "last_update": self._last_update,
                "last_push": self._last_push,
                "region_states": self._last_state,
            }

    def close(self):
        self._running = False
        conn = None
        with self._lock:
            if self._client:
                conn = self._client
                self._client = None
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        if self._server:
            try:
                self._server.close()
            except Exception:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
