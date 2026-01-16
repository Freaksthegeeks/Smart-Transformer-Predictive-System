from opcua import Server
import socket
import time
import random
from datetime import datetime

# === OPC UA SERVER SETUP ===
server = Server()
server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
uri = "http://example.org/transformer"
idx = server.register_namespace(uri)
objects = server.get_objects_node()

# Create transformer object and variables (Only 3 values)
trans_obj = objects.add_object(idx, "Transformer")
voltage = trans_obj.add_variable(idx, "Voltage_RMS", 0.0)
current = trans_obj.add_variable(idx, "Current_RMS", 0.0)
temperature = trans_obj.add_variable(idx, "Temperature_C", 0.0)
timestamp = trans_obj.add_variable(idx, "Timestamp", "")

# Make variables writable
for var in [voltage, current, temperature, timestamp]:
    var.set_writable()

server.start()
print("✅ OPC UA Server started at opc.tcp://localhost:4840")

# === TCP SERVER SETUP ===
HOST = "0.0.0.0"
PORT = 10020
mock_mode = False

try:
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.bind((HOST, PORT))
    tcp_server.listen(1)
    tcp_server.settimeout(10)
    print(f"🔌 Waiting for ESP32 client on TCP {HOST}:{PORT} ...")
    conn, addr = tcp_server.accept()
    print(f"✅ Connected to ESP32: {addr}")
except Exception as e:
    print(f"⚠ Could not start TCP server or no ESP32 connection: {e}")
    print("👉 Switching to MOCK DATA mode.")
    mock_mode = True
    conn = None

# === MAIN LOOP ===
try:
    last_anomaly = time.time()

    while True:
        if not mock_mode:
            try:
                conn.settimeout(2)
                data = conn.recv(1024).decode().strip()
                if not data:
                    continue

                # Expected ESP32 data format: voltage,current,tempC
                lines = data.splitlines()
                for line in lines:
                    parts = line.split(",")
                    if len(parts) >= 3:
                        v = float(parts[0])
                        c = float(parts[1])
                        t = float(parts[2])
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        voltage.set_value(v)
                        current.set_value(c)
                        temperature.set_value(t)
                        timestamp.set_value(now)

                        print(f"{v:.2f},{c:.2f},{t:.2f}")

            except socket.timeout:
                pass
            except Exception as e:
                print(f"⚠ Connection lost or data error: {e}")
                print("👉 Switching to MOCK DATA mode.")
                mock_mode = True

        else:
            # === MOCK DATA MODE ===
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            v = random.uniform(218, 222)  # around 220V
            c = random.uniform(1.0, 1.3)  # around 1.2A
            t = random.uniform(25, 28)    # around 26°C

            # Inject mock anomalies every 20s
            if time.time() - last_anomaly >= 20:
                anomaly_type = random.choice(["overload", "overheat", "voltage_surge"])
                if anomaly_type == "overload":
                    c = random.uniform(5.0, 6.0)
                    print("⚠ MOCK ANOMALY: Overload detected!")
                elif anomaly_type == "overheat":
                    t = random.uniform(80, 95)
                    print("⚠ MOCK ANOMALY: Overheat detected!")
                elif anomaly_type == "voltage_surge":
                    v = random.uniform(260, 280)
                    print("⚠ MOCK ANOMALY: Voltage Surge detected!")
                last_anomaly = time.time()

            voltage.set_value(v)
            current.set_value(c)
            temperature.set_value(t)
            timestamp.set_value(now)

            print(f"{v:.2f},{c:.2f},{t:.2f}")

        time.sleep(1)

except KeyboardInterrupt:
    print("\n🛑 Shutting down server.")
    server.stop()
    if conn:
        conn.close()
    if not mock_mode:
        tcp_server.close()
