"""
=========================================================
DISTRIBUTED PUB-SUB EVENT NOTIFICATION SYSTEM
Component: Central Broker (Server)
Authors: Nartan & Daiyan
Role: Routes messages, manages Lamport clocks, handles 
      mutex locks, coordinates 2PC distributed transactions,
      and serves HTTP API for React Dashboard.
=========================================================
"""

import socket
import threading
import json
import uuid
import time
import logging
from collections import deque
import http.server
import socketserver

# Configure basic logging for visibility into broker operations
logging.basicConfig(level=logging.INFO, format='%(asctime)s [BROKER] %(message)s')

class SubscriberRegistry:
    """Thread-safe registry mapping topics to active client sockets."""
    def __init__(self):
        self._lock = threading.Lock()
        self._topics = {}  # Format: { "topic_name": set(client_sockets) }
        self._address_map = {} # Maps sockets to friendly string names for the dashboard

    def subscribe(self, topic, client_socket, department_name):
        with self._lock:
            if topic not in self._topics:
                self._topics[topic] = set()
            self._topics[topic].add(client_socket)
            self._address_map[client_socket] = department_name
            logging.info(f"[MUTEX] ACQUIRE lock - Client '{department_name}' subscribed to '{topic}'")

    def get_subscribers(self, topic):
        with self._lock:
            return list(self._topics.get(topic, []))

    def get_all_subscribers(self):
        with self._lock:
            clean_map = {}
            for topic, sockets in self._topics.items():
                clean_map[topic] = [self._address_map.get(s, "Unknown") for s in sockets]
            return clean_map

    def remove_client(self, client_socket):
        with self._lock:
            for topic, subscribers in self._topics.items():
                if client_socket in subscribers:
                    subscribers.remove(client_socket)
            if client_socket in self._address_map:
                del self._address_map[client_socket]

class LamportClock:
    """Central logical clock utilizing the Lamport synchronization rule."""
    def __init__(self):
        self._lock = threading.Lock()
        self._time = 0

    def tick(self):
        with self._lock:
            self._time += 1
            return self._time

    def update(self, received_time):
        with self._lock:
            self._time = max(self._time, received_time) + 1
            return self._time

    def get_time(self):
        with self._lock:
            return self._time

class TransactionCoordinator:
    """Manages 2PC-lite states for HIGH and CRITICAL priority alerts."""
    def __init__(self):
        self._lock = threading.Lock()
        self._transactions = {}

    def start_transaction(self, expected_acks, participant_names):
        tx_id = str(uuid.uuid4())[:8]
        with self._lock:
            self._transactions[tx_id] = {
                "status": "PENDING",
                "expected": expected_acks,
                "acks": set(),
                "participants": participant_names
            }
        
        threading.Thread(target=self._timeout_task, args=(tx_id,), daemon=True).start()
        return tx_id

    def _timeout_task(self, tx_id):
        time.sleep(5.0)
        with self._lock:
            tx = self._transactions.get(tx_id)
            if tx and tx["status"] == "PENDING":
                tx["status"] = "ABORTED"
                logging.warning(f"[TXN] ABORTED {tx_id} due to timeout. Missing dependencies.")

    def ack(self, tx_id, client_id):
        with self._lock:
            tx = self._transactions.get(tx_id)
            if not tx or tx["status"] != "PENDING":
                return False
            
            tx["acks"].add(client_id)
            if len(tx["acks"]) >= tx["expected"]:
                tx["status"] = "COMMITTED"
                logging.info(f"[TXN] ✅ COMMITTED {tx_id} successfully.")
            return True

    def get_all_transactions(self):
        with self._lock:
            return [{"tx_id": k, "status": v["status"], "nodes": v["participants"]} for k, v in list(self._transactions.items())[-5:]]

class BrokerServer:
    """Persistent TCP server handling network boundaries and React API."""
    def __init__(self, host='0.0.0.0', port=9000):
        self.host = host
        self.port = port
        self.registry = SubscriberRegistry()
        self.clock = LamportClock()
        self.coordinator = TransactionCoordinator()
        
        self.recent_events = deque(maxlen=10) 
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start_api_bridge(self):
        """Starts a lightweight HTTP server on port 5000 for the React Dashboard"""
        broker_instance = self
        
        class DashboardAPIHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/api/status':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*') # Allows React to fetch data
                    self.end_headers()
                    
                    # Package the data exactly how React expects it
                    state = {
                        "lamport": broker_instance.clock.get_time(),
                        "events": [
                            # Parse the string back into a dict for React
                            {
                                "id": i,
                                "time": time.strftime("%H:%M:%S"),
                                "source": ev.split(' -> ')[0].split('] ')[1],
                                "data": ev.split(': ')[1].split(' (')[0],
                                "severity": ev.split('(')[1].replace(')','')
                            } for i, ev in enumerate(reversed(broker_instance.recent_events))
                        ],
                        "subscribers": broker_instance.registry.get_all_subscribers(),
                        "transactions": broker_instance.coordinator.get_all_transactions()
                    }
                    self.wfile.write(json.dumps(state).encode('utf-8'))
                else:
                    self.send_response(404)
                    self.end_headers()
                    
            def log_message(self, format, *args):
                return # Suppress HTTP logs to keep terminal clean

        api_server = socketserver.ThreadingTCPServer(('0.0.0.0', 5000), DashboardAPIHandler)
        threading.Thread(target=api_server.serve_forever, daemon=True).start()
        logging.info("React HTTP API Bridge listening on 0.0.0.0:5000")

    def start(self):
        self.start_api_bridge() # Start the React Bridge first
        
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(100)
        logging.info(f"Broker TCP socket bound and listening on Port {self.port}")
        logging.info("Waiting for sensors and departments to connect across the network...")
        
        try:
            while True:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            logging.info("Broker shutting down manually.")
        finally:
            self.server_socket.close()

    def handle_client(self, conn, addr):
        client_id = f"{addr[0]}:{addr[1]}"
        buffer = ""
        
        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                buffer += data.decode('utf-8')
                
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        self.process_message(line, conn, client_id)
        except Exception:
            pass 
        finally:
            self.registry.remove_client(conn)
            conn.close()

    def process_message(self, message_str, conn, client_id):
        try:
            msg = json.loads(message_str)
            msg_type = msg.get('type') 
            client_clock = msg.get('lamport', 0) 

            current_time = self.clock.update(client_clock)

            if msg_type == 'SUBSCRIBE':
                topic = msg.get('topic')
                dept_name = msg.get('department', client_id)
                self.registry.subscribe(topic, conn, dept_name)
                
                self._send(conn, {
                    "type": "SUBSCRIBED", 
                    "topic": topic, 
                    "lamport": self.clock.tick()
                })

            elif msg_type == 'PUBLISH':
                sensor_name = msg.get('sensor', 'unknown-sensor')
                topic = msg.get('topic', sensor_name.split('-')[0]) 
                data = msg.get('data', 'No data')
                severity = msg.get('severity', 'LOW')
                
                log_entry = f"[Lamport: {current_time}] {sensor_name} -> {topic}: {data} ({severity})"
                self.recent_events.append(log_entry)
                logging.info(f"[RPC RECV] {log_entry}")
                
                subscribers = self.registry.get_subscribers(topic)
                
                out_msg = {
                    "type": "EVENT",
                    "sensor": sensor_name,
                    "topic": topic,
                    "data": data,
                    "severity": severity,
                    "lamport": self.clock.tick()
                }

                if severity in ['HIGH', 'CRITICAL'] and subscribers:
                    participant_names = [self.registry._address_map.get(s, "Unknown") for s in subscribers]
                    tx_id = self.coordinator.start_transaction(len(subscribers), participant_names)
                    out_msg["tx_id"] = tx_id
                    logging.info(f"[TXN] BEGIN {tx_id} (Severity: {severity}, Awaiting ACKs: {participant_names})")

                for sub_conn in subscribers:
                    self._send(sub_conn, out_msg)

            elif msg_type == 'ACK':
                tx_id = msg.get('tx_id')
                if tx_id:
                    dept = msg.get('department', client_id)
                    logging.info(f"[ACK] Received for {tx_id} from {dept}")
                    self.coordinator.ack(tx_id, dept)

            elif msg_type == 'STATUS':
                self._send(conn, {
                    "type": "STATUS_REPLY", 
                    "lamport": self.clock.get_time(),
                    "events": list(self.recent_events),
                    "subscribers": self.registry.get_all_subscribers(),
                    "transactions": self.coordinator.get_all_transactions()
                })

        except json.JSONDecodeError:
            pass
        except Exception as e:
            logging.error(f"Processing error: {e}")

    def _send(self, conn, payload):
        try:
            message = json.dumps(payload) + '\n'
            conn.sendall(message.encode('utf-8'))
        except Exception:
            pass

if __name__ == '__main__':
    BrokerServer().start()