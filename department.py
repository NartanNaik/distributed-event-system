"""
=========================================================
DISTRIBUTED PUB-SUB EVENT NOTIFICATION SYSTEM
Component: Department Subscriber (Edge Node)
Author: Farhaan
Role: Subscribes to topics, updates local Lamport clock, 
      and sends ACKs for critical distributed transactions.
=========================================================
"""

import socket
import json
import sys

def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python department.py <department_name> <topic> [broker_ip]")
        sys.exit(1)

    department_name = sys.argv[1]
    topic = sys.argv[2]
    # UPDATED: Defaults to the correct LAN IP if not provided
    broker_ip = sys.argv[3] if len(sys.argv) == 4 else "10.10.16.136"

    lamport_clock = 0

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((broker_ip, 9000))

        subscribe_message = {
            "type": "SUBSCRIBE",
            "department": department_name,
            "topic": topic
        }

        client_socket.sendall(
            (json.dumps(subscribe_message) + "\n").encode("utf-8")
        )

        print(f"Registered to topic '{topic}' as '{department_name}' on Broker {broker_ip}:9000")

        buffer = ""

        while True:
            data = client_socket.recv(1024)

            if not data:
                print("\nBroker connection closed. Shutting down.")
                break

            buffer += data.decode("utf-8")

            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)

                if not message.strip():
                    continue

                try:
                    event = json.loads(message)

                    if event.get("type") != "EVENT":
                        continue

                    received_lamport = event.get("lamport", 0)

                    lamport_clock = max(
                        lamport_clock,
                        received_lamport
                    ) + 1

                    topic_name = event.get("topic", "unknown")
                    event_data = event.get("data", "No Data")
                    tx_id = event.get("tx_id")

                    if tx_id:
                        print(
                            f"[RECEIVED CRITICAL ALERT] "
                            f"Txn ID: {tx_id} | "
                            f"Data: {event_data}"
                        )

                        ack_message = {
                            "type": "ACK",
                            "department": department_name,
                            "tx_id": tx_id,
                            "lamport": lamport_clock
                        }

                        client_socket.sendall(
                            (json.dumps(ack_message) + "\n").encode("utf-8")
                        )

                        print(
                            f"[SENT ACK] Responding to transaction "
                            f"confirmation {tx_id} "
                            f"at Lamport Time: {lamport_clock}"
                        )

                    else:
                        print(
                            f"[RECEIVED] Topic: {topic_name} | "
                            f"Data: {event_data} | "
                            f"Updated Lamport Clock: {lamport_clock}"
                        )

                except json.JSONDecodeError:
                    print(f"Invalid JSON received: {message}")

    except ConnectionRefusedError:
        print(f"ERROR: Could not connect to broker at {broker_ip}:9000")
        print("Check if the broker is running and the IP address is correct.")

    except KeyboardInterrupt:
        print("\nDisconnected from broker.")

    except Exception as e:
        print(f"Unexpected error: {e}")

    finally:
        try:
            client_socket.close()
        except:
            pass

if __name__ == "__main__":
    main()