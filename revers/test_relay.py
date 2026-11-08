import base64
import pathlib
import socket
import ssl
import threading
import time
import urllib.parse
import select

SRC = pathlib.Path(r"C:\Users\SystemX\Desktop\SteamAccGen\SteamAccGen.py").read_text(encoding="utf-8")
start = SRC.index("def _recv_exact(")
end = SRC.index("def launch_chrome_with_cdp(profile_dir):")
ns = {"socket": socket, "ssl": ssl, "threading": threading,
      "select": select, "base64": base64, "urllib": urllib}
exec(SRC[start:end], ns)
ProxyRelay = ns["ProxyRelay"]

USER, PASS = "bob", "s3cret"
B64 = base64.b64encode(f"{USER}:{PASS}".encode()).decode()


def read_head(conn):
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = conn.recv(4096)
        if not chunk:
            break
        data += chunk
    return data


def echo_server():
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(5)
    port = srv.getsockname()[1]

    def run():
        while True:
            c, _ = srv.accept()
            threading.Thread(target=handle, args=(c,), daemon=True).start()

    def handle(c):
        while True:
            d = c.recv(4096)
            if not d:
                break
            c.sendall(b"echo:" + d)
        c.close()

    threading.Thread(target=run, daemon=True).start()
    return port


def fake_http_proxy(mode="auth"):
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(5)
    port = srv.getsockname()[1]

    def handle(c):
        head = read_head(c)
        if mode == "auth" and f"Proxy-Authorization: Basic {B64}" not in head.decode("latin-1"):
            c.sendall(b"HTTP/1.1 407 Proxy Authentication Required\r\n\r\n")
            c.close()
            return
        line = head.split(b"\r\n", 1)[0].decode()
        target = line.split(" ")[1]
        host, _, p = target.rpartition(":")
        up = socket.create_connection((host, int(p)))
        c.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
        pipe(c, up)

    def run():
        while True:
            c, _ = srv.accept()
            threading.Thread(target=handle, args=(c,), daemon=True).start()

    threading.Thread(target=run, daemon=True).start()
    return port


def fake_socks5(user=None, password=None):
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(5)
    port = srv.getsockname()[1]

    def recvn(c, n):
        b = b""
        while len(b) < n:
            d = c.recv(n - len(b))
            if not d:
                raise ConnectionError
            b += d
        return b

    def handle(c):
        ver, n = recvn(c, 2)
        methods = recvn(c, n)
        if user:
            c.sendall(b"\x05\x02")
            ver, ulen = recvn(c, 2)
            u = recvn(c, ulen).decode()
            plen = recvn(c, 1)[0]
            p = recvn(c, plen).decode()
            if u != user or p != password:
                c.sendall(b"\x01\x01")
                c.close()
                return
            c.sendall(b"\x01\x00")
        else:
            c.sendall(b"\x05\x00")
        ver, cmd, rsv, atyp = recvn(c, 4)
        if atyp == 3:
            ln = recvn(c, 1)[0]
            host = recvn(c, ln).decode()
        elif atyp == 1:
            host = socket.inet_ntoa(recvn(c, 4))
        else:
            raise ConnectionError("bad atyp")
        p = int.from_bytes(recvn(c, 2), "big")
        up = socket.create_connection((host, p))
        c.sendall(b"\x05\x00\x00\x01" + socket.inet_aton("127.0.0.1") + (0).to_bytes(2, "big"))
        pipe(c, up)

    def run():
        while True:
            c, _ = srv.accept()
            threading.Thread(target=handle, args=(c,), daemon=True).start()

    threading.Thread(target=run, daemon=True).start()
    return port


def pipe(a, b):
    socks = [a, b]
    try:
        while True:
            r, _, _ = select.select(socks, [], [], 5)
            if not r:
                return
            for s in r:
                d = s.recv(4096)
                if not d:
                    return
                (b if s is a else a).sendall(d)
    finally:
        a.close()
        b.close()


def test(upstream, label):
    echo = echo_server()
    relay = ProxyRelay(upstream)
    relay.start()
    time.sleep(0.2)
    c = socket.create_connection(("127.0.0.1", relay.port), timeout=5)
    c.sendall(f"CONNECT 127.0.0.1:{echo} HTTP/1.1\r\nHost: 127.0.0.1:{echo}\r\n\r\n".encode())
    resp = c.recv(4096)
    ok200 = b"200" in resp
    c.sendall(b"ping")
    got = c.recv(4096)
    c.close()
    relay.stop()
    print(f"{label:34} tunnel={ok200} data={got!r}")


echo_main = echo_server()

# 1. http upstream with auth
p = fake_http_proxy("auth")
test({"scheme": "http", "host": "127.0.0.1", "port": p, "user": USER,
      "password": PASS, "server": "", "url": "", "display": ""}, "http proxy + Basic auth")

# 2. socks5 upstream with auth
p = fake_socks5(USER, PASS)
test({"scheme": "socks5", "host": "127.0.0.1", "port": p, "user": USER,
      "password": PASS, "server": "", "url": "", "display": ""}, "socks5 proxy + auth")

# 3. socks5 upstream no auth
p = fake_socks5()
test({"scheme": "socks5", "host": "127.0.0.1", "port": p, "user": "",
      "password": "", "server": "", "url": "", "display": ""}, "socks5 proxy no auth")

# 4. wrong password must fail closed
p = fake_http_proxy("auth")
test({"scheme": "http", "host": "127.0.0.1", "port": p, "user": USER,
      "password": "WRONG", "server": "", "url": "", "display": ""}, "http proxy wrong pass")
print("done")
