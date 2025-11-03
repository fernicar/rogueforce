import socket
import sys
import threading
import time
from datetime import datetime
import os

MSG_EXIT = "EXIT"
DEBUG = True  # Set to False to disable debug logging

def debug_log(message, level="INFO"):
    """Enhanced logging function with timestamps and debug levels"""
    if DEBUG or level != "DEBUG":
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{level}] {message}")

class Server(object):
    def __init__(self, port1, port2):
        debug_log(f"Initializing server on ports {port1} and {port2}")
        self.s = []
        self.c = []
        self.a = []
        self.running = False
        self.shutdown_requested = False
        self._shutdown_lock = threading.Lock()
        self._closing = False
        self.start_time = time.time()
        
        for i in [0,1]:
            try:
                debug_log(f"Setting up socket {i} on port {port1 if i == 0 else port2}")
                self.s.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
                self.s[i].bind(('', port1 if i == 0 else port2))
                self.s[i].listen(1)
                # Set socket timeout to allow graceful shutdown
                self.s[i].settimeout(1.0)
                debug_log(f"Socket {i} successfully bound to port {port1 if i == 0 else port2}")
            except Exception as e:
                debug_log(f"Error setting up socket {i}: {e}", "ERROR")
                sys.exit(1)
        
        # Start threads first, then accept connections
        debug_log("Starting server threads and accepting connections")
        self.launch()

    def close(self):
        # Prevent multiple calls to close()
        with self._shutdown_lock:
            if self._closing:
                debug_log("Server already closing, ignoring duplicate close request", "DEBUG")
                return
            self._closing = True
        
        debug_log("Server shutdown initiated")
        self.shutdown_requested = True
        self.running = False
        uptime = time.time() - self.start_time
        debug_log(f"Server uptime: {uptime:.2f} seconds")
        
        # Close client sockets first
        debug_log(f"Closing {len(self.c)} client connections")
        for i, client in enumerate(self.c):
            try:
                debug_log(f"Closing client {i} connection")
                client.close()
                debug_log(f"Client {i} connection closed successfully")
            except Exception as e:
                debug_log(f"Error closing client {i}: {e}", "ERROR")
        
        # Close server sockets
        debug_log("Closing server sockets")
        for i, server_socket in enumerate(self.s):
            try:
                debug_log(f"Closing server socket {i}")
                server_socket.close()
                debug_log(f"Server socket {i} closed successfully")
            except Exception as e:
                debug_log(f"Error closing server socket {i}: {e}", "ERROR")
        
        debug_log("Server shutdown completed")

    def launch(self):
        debug_log("Launching server - starting accept connections thread")
        self.running = True
        # Accept connections in separate threads to avoid blocking
        threading.Thread(target=self.accept_connections, name="AcceptThread").start()
        debug_log("Accept connections thread started")

    def accept_connections(self):
        thread_name = threading.current_thread().name
        debug_log(f"Accept connections thread {thread_name} started")
        try:
            # Keep trying to accept connections until both clients are connected
            while len(self.c) < 2 and not self.shutdown_requested:
                for i in [0,1]:
                    # Check for shutdown before trying to accept
                    if self.shutdown_requested:
                        debug_log(f"Accept thread checking shutdown flag before client {i} connection", "DEBUG")
                        break
                    
                    # Only try to accept on socket if we don't have a client for it yet
                    if len(self.c) <= i:
                        debug_log(f"Waiting for client {i} to connect on socket {i}")
                        try:
                            client, address = self.s[i].accept()
                            self.c.append(client)
                            self.a.append(address)
                            debug_log(f"Client {i} connected from {address}")
                            
                            # Start listening thread for each client
                            thread_name = f"ListenThread-{i}"
                            debug_log(f"Starting listening thread {thread_name} for client {i}")
                            threading.Thread(target=self.listen, args=(i,), name=thread_name).start()
                            debug_log(f"Listening thread {thread_name} started for client {i}")
                            
                            if len(self.c) == 2:
                                debug_log("Both clients connected, stop accepting new connections")
                                break
                        except socket.timeout:
                            debug_log(f"Socket {i} timeout while waiting for client", "DEBUG")
                            continue
                        except Exception as e:
                            # Only treat as error if not shutting down
                            if not self.shutdown_requested:
                                debug_log(f"Error accepting connection on socket {i}: {e}", "ERROR")
                            break
                    
                    # Small delay to prevent tight loop
                    time.sleep(0.1)
                    
        except Exception as e:
            if not self.shutdown_requested:
                debug_log(f"Error in accept connections thread: {e}", "ERROR")
        finally:
            debug_log(f"Accept connections thread {thread_name} ending")

    def listen(self, i):
        thread_name = threading.current_thread().name
        debug_log(f"Listen thread {thread_name} started for client {i}")
        try:
            while not self.shutdown_requested and self.running:
                debug_log(f"Client {i} - waiting to receive data (thread: {thread_name})", "DEBUG")
                try:
                    data = self.c[i].recv(1024)
                except socket.timeout:
                    continue
                except Exception as e:
                    if not self.shutdown_requested:
                        debug_log(f"Socket error receiving from client {i}: {e}", "ERROR")
                    break
                
                if not data:
                    debug_log(f"Client {i} disconnected (empty data received)")
                    break
                
                # Decode bytes to string for proper comparison
                data_str = data.decode('utf-8').rstrip()
                debug_log(f"Client {i} sent: '{data_str}' (length: {len(data)} bytes)")
                
                if data_str == MSG_EXIT:
                    debug_log(f"Client {i} requested exit with message: '{MSG_EXIT}'")
                    debug_log("Initiating server shutdown due to client exit request")
                    self.close()
                    return
                else:
                    other_client = (i+1)%2
                    debug_log(f"Forwarding message from client {i} to client {other_client}")
                    try:
                        self.c[other_client].send(data)
                        debug_log(f"Successfully forwarded {len(data)} bytes to client {other_client}")
                    except Exception as e:
                        debug_log(f"Error sending to client {other_client}: {e}", "ERROR")
                        debug_log(f"Message forwarding failed for client {other_client}")
                        
                        # Check if the other client is still connected
                        try:
                            # Try to send a test message to check connection
                            self.c[other_client].send(b"PING")
                            debug_log(f"Client {other_client} is still responsive")
                        except:
                            debug_log(f"Client {other_client} appears to be disconnected", "ERROR")
                            break
                            
        except Exception as e:
            if not self.shutdown_requested:
                debug_log(f"Error in listen thread {i} ({thread_name}): {e}", "ERROR")
        finally:
            debug_log(f"Listen thread {thread_name} for client {i} ending")
            if i < len(self.c):
                try:
                    debug_log(f"Cleaning up client {i} connection")
                    self.c[i].close()
                    debug_log(f"Client {i} connection cleaned up successfully")
                except Exception as e:
                    debug_log(f"Error cleaning up client {i}: {e}", "ERROR")

if __name__ == "__main__":
    debug_log("=== SERVER STARTUP ===")
    debug_log(f"Python version: {sys.version}")
    debug_log(f"Command line args: {sys.argv}")
    
    if len(sys.argv) != 2:
        debug_log("Usage: python server.py <port>", "ERROR")
        print("Usage: python server.py <port>")
        sys.exit(1)
    
    p = int(sys.argv[1])
    debug_log(f"Starting server with base port: {p}")
    debug_log(f"Expected socket ports: {p} and {p+1}")
    
    try:
        debug_log("Creating Server instance")
        server = Server(p, p+1)
        debug_log("Server instance created successfully, entering main loop")
        
        # Keep main thread alive
        connection_count = 0
        while server.running:
            connection_count += 1
            if connection_count % 10 == 0:  # Log every 10 iterations
                debug_log(f"Server still running... (checked {connection_count} times)", "DEBUG")
            threading.Event().wait(1)
            
        debug_log("Main loop ended, server is no longer running")
    except KeyboardInterrupt:
        debug_log("Received KeyboardInterrupt (Ctrl+C)")
        print("\nShutting down server...")
        server.close()
        debug_log("Server closed due to keyboard interrupt")
    except Exception as e:
        debug_log(f"Server error: {e}", "ERROR")
        debug_log("Server error details:", "ERROR")
        import traceback
        debug_log(traceback.format_exc(), "ERROR")
        print(f"Server error: {e}")
    finally:
        debug_log("=== SERVER SHUTDOWN ===")
