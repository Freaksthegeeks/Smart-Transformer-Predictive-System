from opcua import Server
import serial
import time
from datetime import datetime

# =========================================================
# OPC UA Setup
# =========================================================
server = Server()
server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
uri = "http://example.org/transformer"
idx = server.register_namespace(uri)
objects = server.get_objects_node()

trans_obj = objects.add_object(idx, "Transformer")
voltage = trans_obj.add_variable(idx, "Voltage_RMS", 0.0)
current = trans_obj.add_variable(idx, "Current_RMS", 0.0)
temperature = trans_obj.add_variable(idx, "Temperature_C", 0.0)
timestamp = trans_obj.add_variable(idx, "Timestamp", "")

for v in [voltage, current, temperature, timestamp]:
    v.set_writable()


server.start()
print("✅ OPC UA Server started at opc.tcp://localhost:4840")

# =========================================================
# SERIAL SETUP
# =========================================================
try:
    ser = serial.Serial("COM3", 115200, timeout=1)
    time.sleep(2)
    print("🔌 Connected to ESP32 on COM3")
except Exception as e:
    print("❌ Cannot open COM3:", e)
    exit()

print("📡 Waiting for clean sensor data...")

# =========================================================
# MAIN LOOP
# =========================================================
while True:
    try:
        raw = ser.readline()

        # skip empty reads
        if not raw:
            continue

        try:
            line = raw.decode(errors="ignore").strip()
        except:
            continue

        # skip junk / garbage data
        if not all(c.isdigit() or c in ".,-" for c in line):
            continue

        # now parse CSV
        parts = line.split(",")
        if len(parts) != 3:
            continue

        v = float(parts[0])
        c = float(parts[1])
        t = float(parts[2])

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # update OPC UA
        voltage.set_value(v)
        current.set_value(c)
        temperature.set_value(t)
        timestamp.set_value(ts)

        print(f"✔ {v:.2f}, {c:.2f}, {t:.2f}")

    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        server.stop()
        ser.close()
        break
