"""
=========================================================
DISTRIBUTED PUB-SUB EVENT NOTIFICATION SYSTEM
Component: Smart City Sensor (Publisher Edge Node)
Author: Manoj
Role: Simulates IoT sensors, increments Lamport clocks, 
      and publishes JSON events over TCP.
=========================================================
"""

import socket
import threading
import json
import time
import random
import sys

BROKER_PORT = 9000

class LamportClock:
    def __init__(self):
        self.time = 0
        self._lock = threading.Lock()

    def tick(self):
        with self._lock:
            self.time += 1
            return self.time

    def update(self, received):
        with self._lock:
            self.time = max(self.time, received) + 1
            return self.time

EVENTS = {
    "traffic": [
        ("Major accident on Highway 5 — 3 vehicles involved",    "HIGH"),
        ("Heavy congestion detected near City Center junction",   "MEDIUM"),
        ("Signal failure at MG Road & Park Street crossing",      "MEDIUM"),
        ("Vehicle breakdown blocking right lane on Ring Road",    "LOW"),
        ("Rush hour congestion — average speed 12 km/h",         "LOW"),
        ("Wrong-way vehicle detected on Expressway — CRITICAL",  "CRITICAL"),
    ],
    "pollution": [
        ("AQI reached 380 — severe health hazard",               "CRITICAL"),
        ("PM2.5 levels spike to 210 μg/m³ in Zone 4",           "HIGH"),
        ("CO2 concentration above threshold near industrial hub", "HIGH"),
        ("Smog alert issued — visibility below 200m",            "MEDIUM"),
        ("Chemical leak detected near factory district",          "CRITICAL"),
        ("AQI moderate at 85 — safe for outdoor activity",       "LOW"),
    ],
    "weather": [
        ("Flash flood warning: rainfall 120mm in 2 hours",       "CRITICAL"),
        ("Category 2 storm approaching from the coast",          "HIGH"),
        ("Temperature hits 47°C — extreme heat advisory",        "HIGH"),
        ("Wind speed 95 km/h — avoid tall structures",           "MEDIUM"),
        ("Heavy rain expected — possible waterlogging",          "MEDIUM"),
        ("Earthquake tremor 4.2M detected near dam area",        "CRITICAL"),
    ],
}

class SmartCitySensor:
    def __init__(self, sensor_type: str, broker_host: str):
        self.sensor_type = sensor_type
        self.broker_host = broker_host
        self.clock       = LamportClock()
        self.conn        = None
        self.running     = True

    def connect(self):
        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((self.broker_host, BROKER_PORT))
            print(f"[SENSOR:{self.sensor_type.upper()}] Connected to broker at {self.broker_host}:{BROKER_PORT}")
        except ConnectionRefusedError:
            print(f"[ERROR] Could not connect to Broker at {self.broker_host}:{BROKER_PORT}")
            print("Check if the broker is running and the IP address is correct.")
            sys.exit(1)

    def publish(self, data: str, severity: str):
        ts = self.clock.tick()    
        event = {
            "type":     "PUBLISH",
            "sensor":   f"{self.sensor_type}-sensor",
            "data":     data,
            "severity": severity,
            "lamport":  ts,        
        }

        try:
            payload = json.dumps(event) + "\n"
            self.conn.sendall(payload.encode())   
            print(f"  [LAMPORT:{ts:04d}]  [{severity:8s}]  {data[:60]}")
        except Exception as e:
            print(f"[ERROR] Connection lost: {e}")
            self.running = False

    def run(self):
        self.connect()
        events = EVENTS.get(self.sensor_type, [])
        print(f"\n{'='*60}")
        print(f"  SENSOR: {self.sensor_type.upper()}  |  Events: {len(events)}")
        print(f"  Lamport clock starts at 0, increments each publish")
        print(f"{'='*60}\n")

        while self.running:
            data, severity = random.choice(events)

            if random.random() < 0.1:
                severity = "CRITICAL"
                data = "⚠ EMERGENCY: " + data

            self.publish(data, severity)
            delay = random.uniform(3, 8)
            time.sleep(delay)

if __name__ == "__main__":
    if len(sys.argv) > 3:
        print("Usage: python sensor.py <sensor_type> [broker_ip]")
        sys.exit(1)

    sensor_type = sys.argv[1] if len(sys.argv) > 1 else "traffic"
    # UPDATED: Defaults to the correct LAN IP if not provided
    broker_ip = sys.argv[2] if len(sys.argv) > 2 else "10.10.16.136"
    
    if sensor_type not in EVENTS:
        print(f"Unknown sensor type. Choose: {list(EVENTS.keys())}")
        sys.exit(1)

    sensor = SmartCitySensor(sensor_type, broker_ip)
    try:
        sensor.run()
    except KeyboardInterrupt:
        print(f"\n[SENSOR:{sensor_type}] Shutting down.")