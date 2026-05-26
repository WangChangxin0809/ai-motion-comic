"""SSH tunnel: forward localhost:8188 -> remote ComfyUI port 8188."""
import paramiko
import socket
import threading
import select
import sys
import os

HOST = "117.50.27.169"
SSH_PORT = 23
USER = "root"
PASSWORD = "QlT1Yh36H825u9L4"
REMOTE_HOST = "127.0.0.1"
REMOTE_PORT = 8188
LOCAL_PORT = 8188


def forward(local_sock, ssh_client):
    """Forward a single connection through SSH tunnel."""
    channel = ssh_client.get_transport().open_channel(
        "direct-tcpip", (REMOTE_HOST, REMOTE_PORT), local_sock.getpeername()
    )
    if channel is None:
        local_sock.close()
        return

    while True:
        r, _, _ = select.select([local_sock, channel], [], [], 1)
        if local_sock in r:
            data = local_sock.recv(4096)
            if not data:
                break
            channel.send(data)
        if channel in r:
            data = channel.recv(4096)
            if not data:
                break
            local_sock.send(data)

    local_sock.close()
    channel.close()


def main():
    # Connect SSH
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, SSH_PORT, USER, PASSWORD)
    print(f"SSH connected to {HOST}:{SSH_PORT}")

    # Listen locally
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", LOCAL_PORT))
    server.listen(5)

    print(f"Tunnel active: http://localhost:{LOCAL_PORT} -> {HOST}:{REMOTE_PORT}")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            client, addr = server.accept()
            t = threading.Thread(target=forward, args=(client, ssh), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\nTunnel stopped.")
    finally:
        server.close()
        ssh.close()


if __name__ == "__main__":
    from pathlib import Path
    pid_file = Path("/tmp/comfyui_tunnel.pid")
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(os.getpid()))
    main()
