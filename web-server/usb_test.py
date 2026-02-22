#!/usr/bin/env python3
import glob
import os
import subprocess

def detect_video_devices():
    """List all /dev/video* devices."""
    devices = glob.glob("/dev/video*")
    info = []
    for dev in devices:
        name_file = f"/sys/class/video4linux/{os.path.basename(dev)}/name"
        if os.path.exists(name_file):
            with open(name_file, "r", encoding="utf-8", errors="ignore") as f:
                name = f.read().strip()
        else:
            name = "Unknown"
        info.append({"device": dev, "name": name})
    return info

def detect_usb_devices():
    """Use lsusb to list all connected USB devices."""
    try:
        output = subprocess.check_output(["lsusb"], universal_newlines=True)
        usb_list = [line.strip() for line in output.split("\n") if line.strip()]
        return usb_list
    except Exception as e:
        return [f"Error detecting USB devices: {e}"]

def main():
    print("=== Video Devices (/dev/video*) ===")
    for cam in detect_video_devices():
        print(f"{cam['device']}: {cam['name']}")

    print("\n=== USB Devices (lsusb) ===")
    for dev in detect_usb_devices():
        print(dev)

if __name__ == "__main__":
    main()