"""
=========================================================
DISTRIBUTED PUB-SUB EVENT NOTIFICATION SYSTEM
Component: Terminal Live Dashboard
Author: Prahas
Role: Polls the central broker over the network to display 
      real-time metrics for all 4 DS concepts.
=========================================================
"""

import socket
import json
import time
import os
import sys

# UPDATED: Defaults to the correct LAN IP if not provided
BROKER_HOST = sys.argv[1] if len(sys.argv) > 1 else "10.10.16.136"
BROKER_PORT = 9000
INTERVAL = 2.0

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def fetch_status():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(1.5) 
    
    try:
        client.connect((BROKER_HOST, BROKER_PORT))
        request = json.dumps({"type": "STATUS"}) + "\n"
        client.sendall(request.encode('utf-8'))
        
        response_bytes = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            response_bytes += chunk
            if b"\n" in chunk:
                break
                
        return json.loads(response_bytes.decode('utf-8'))
    except (socket.error, json.JSONDecodeError, TimeoutError):
        return None
    finally:
        client.close()

def render_dashboard(state):
    clear_screen()
    
    BOLD = "\033[1m"
    RESET = "\033[0m"
    
    print("=" * 60)
    print(f"{BOLD}              SMART CITY LIVE DS DASHBOARD                  {RESET}")
    print(f"               Targeting Broker: {BROKER_HOST}:{BROKER_PORT}")
    print("=" * 60)
    
    if state is None:
        print(f"\n\033[31m[⚠️ ERROR] Unable to connect to broker at {BROKER_HOST}:{BROKER_PORT}{RESET}")
        print("Retrying automatically in 2 seconds...\n")
        print("=" * 60)
        return

    events = state.get("events", [])
    lamport_clock = state.get("lamport", 0)
    subscribers = state.get("subscribers", {})
    transactions = state.get("transactions", [])

    print(f"{BOLD}[PANEL 1: RPC MODEL DATA LOGS]{RESET}")
    if events:
        for event in events:
            print(f" - {event}")
    else:
        print(" - No log entries available.")
    print()

    print(f"{BOLD}[PANEL 2: LOGICAL SYSTEM CLOCKS]{RESET}")
    print(f" Current Broker Logical Clock Time: {lamport_clock}")
    print()

    print(f"{BOLD}[PANEL 3: MUTEX OPERATIONS REGISTRY]{RESET}")
    if subscribers:
        for topic, subs in subscribers.items():
            print(f" Topic '{topic}' -> Active: {subs}")
    else:
        print(" No active topic locking or subscriptions registered.")
    print()

    print(f"{BOLD}[PANEL 4: DISTRIBUTED TRANSACTIONS LOG (2PC-lite)]{RESET}")
    if transactions:
        for tx in transactions:
            tx_id = tx.get("tx_id", "N/A")
            status = tx.get("status", "UNKNOWN")
            
            if status == "COMMITTED":
                status_str = f"\033[32m✅ {status}\033[0m"
            elif status == "ABORTED":
                status_str = f"\033[31m❌ {status}\033[0m"
            else:
                status_str = f"\033[33m⏳ {status}\033[0m"
                
            participants = tx.get("participants", [])
            print(f" TX-ID: {tx_id} | Status: {status_str} | Nodes: {participants}")
    else:
        print(" No active or finalized distributed transactions.")
        
    print("=" * 60)

def main():
    try:
        clear_screen()
        print(f"Initializing dashboard... attempting connection to {BROKER_HOST}:{BROKER_PORT}")
        while True:
            state = fetch_status()
            render_dashboard(state)
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nDashboard closed gracefully.")
        sys.exit(0)

if __name__ == "__main__":
    main()