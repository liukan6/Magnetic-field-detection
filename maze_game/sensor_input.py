import sys
import time

import serial
import serial.tools.list_ports

from config import SERIAL_BAUD_RATE


def select_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        desc = port.description.lower()
        if "arduino" in desc or "ch340" in desc or "usb serial" in desc:
            print(f"Auto connect: {port.device}")
            return port.device

    print("Arduino not found.")
    sys.exit()


def open_serial_connection():
    port = select_port()
    ser = serial.Serial(port, SERIAL_BAUD_RATE, timeout=1)
    print(f"\nSerial connected: {port}")
    return ser


def parse_line(line):
    try:
        decoded = line.decode("utf-8", errors="ignore").strip()
        if "ms:" not in decoded:
            return None

        parts = decoded.split()
        if len(parts) < 3:
            return None

        bx = float(parts[1])
        by = float(parts[2])
        return bx, by
    except Exception:
        return None


def calibrate_sensor(ser, duration=2.0):
    print("\nCalibrating, please keep the magnetic input still...")
    ser.reset_input_buffer()
    bx0 = 0.0
    by0 = 0.0
    count = 0
    start = time.time()

    while time.time() - start < duration:
        if not ser.in_waiting:
            continue

        result = parse_line(ser.readline())
        if result is None:
            continue

        bx, by = result
        bx0 += bx
        by0 += by
        count += 1

    if count == 0:
        print("Calibration skipped because no valid serial data was received.")
        return 0.0, 0.0

    bx0 /= count
    by0 /= count
    print(f"Calibration done: bx0={bx0:.2f}, by0={by0:.2f}")
    return bx0, by0
