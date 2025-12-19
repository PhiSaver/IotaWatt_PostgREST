#!/usr/bin/env python3
"""
Port forwarding proxy with per-client logging.
Logs each client connection to a separate file: <hostname>-<port>.txt
"""

import socket
import threading
import sys
from datetime import datetime
import typer


def handle_client(client_sock, client_addr, target_host, target_port, log_timestamps):
    """Handle a single client connection and log traffic."""
    hostname, port = client_addr
    log_file = f"{hostname}-{port}.txt"

    try:
        # Connect to target
        target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_sock.connect((target_host, target_port))

        print(f"[+] New connection: {hostname}:{port} -> {target_host}:{target_port}")
        print(f"    Logging to: {log_file}")

        def relay(src, dst, direction, log_file):
            """Relay data from src to dst and log it."""
            try:
                with open(log_file, "ab") as f:
                    while True:
                        data = src.recv(4096)
                        if not data:
                            break

                        # Log with optional timestamp
                        if log_timestamps:
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                            log_line = f"[{timestamp}] [{direction}] {len(data)} bytes\n"
                        else:
                            log_line = f"[{direction}] {len(data)} bytes\n"

                        f.write(log_line.encode() + data + b"\n")
                        f.flush()

                        dst.send(data)
            except Exception as e:
                print(f"[!] Relay error ({direction}): {e}")
            finally:
                src.close()
                dst.close()

        # Start bidirectional relay
        client_to_target = threading.Thread(target=relay, args=(client_sock, target_sock, "→", log_file), daemon=True)
        target_to_client = threading.Thread(target=relay, args=(target_sock, client_sock, "←", log_file), daemon=True)

        client_to_target.start()
        target_to_client.start()

        # Wait for both directions to complete
        client_to_target.join()
        target_to_client.join()

    except Exception as e:
        print(f"[!] Error handling client {hostname}:{port}: {e}")
    finally:
        client_sock.close()
        print(f"[-] Closed connection: {hostname}:{port}")


def start_proxy(listen_port, target_host, target_port, log_timestamps):
    """Start the proxy server."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind(("0.0.0.0", listen_port))
        server.listen(5)
        print(f"[*] Proxy listening on 0.0.0.0:{listen_port}")
        print(f"[*] Forwarding to {target_host}:{target_port}")
        print(f"[*] Timestamps: {'enabled' if log_timestamps else 'disabled'}")
        print(f"[*] Log files will be created in: {sys.path[0] or '.'}")
        print()

        while True:
            client_sock, client_addr = server.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_sock, client_addr, target_host, target_port, log_timestamps),
                daemon=True,
            )
            client_thread.start()

    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
    except Exception as e:
        print(f"[!] Server error: {e}")
    finally:
        server.close()


def main(
    listen_port: int = typer.Argument(..., help="Port to listen on"),
    target_host: str = typer.Argument(..., help="Target host to forward to"),
    target_port: int = typer.Argument(..., help="Target port to forward to"),
    timestamps: bool = typer.Option(False, "--timestamps", "-t", help="Add timestamps to log entries"),
):
    """
    Port forwarding proxy with per-client logging.
    
    Log files are created as: <client-hostname>-<client-port>.txt
    
    Examples:
    
        proxy.py 8080 localhost 5432
        
        proxy.py 8080 localhost 5432 --timestamps
    """
    start_proxy(listen_port, target_host, target_port, timestamps)


if __name__ == "__main__":
    typer.run(main)
