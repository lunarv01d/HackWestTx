import psutil
import time

CPUCheckLength = 0
RAMCheckLength = 0
CheckInterval = 0
Monitoring = False
_last_net = psutil.net_io_counters()
_last_net_time = time.monotonic()


def userInput():
    global CPUCheckLength
    global CheckInterval
    global Monitoring

    CPUCheckLength = int(input("How long should each CPU check be: "))
    CheckInterval = int(input("How often should it check: "))
    Monitoring = input("Do you want to monitor your CPU usage? (True for Yes, False for No): ").strip().lower() in ("true", "yes", "1")

    if CPUCheckLength > CheckInterval:
        CPUCheckLength = CheckInterval

def check_User():
    return psutil.users()[0].name

def check_CPUusage(CPUL):
    return (psutil.cpu_percent(CPUL))

def check_MemoryUsage():
    return psutil.virtual_memory().used / 1_000_000_000 # bytes to Gigabytes

def check_MemoryRatio():
    return psutil.virtual_memory().percent

def check_DiskUsage():
    return psutil.disk_usage('/').used / 1000000000  # bytes to Gigabytes

def check_DiskRatio():
    return psutil.disk_usage(f'/Users/{check_User()}/').percent  # Ratio of used to total

def check_BatteryPercent():
    return psutil.sensors_battery().percent

def check_PluggedIn():
    battery = psutil.sensors_battery()

    if battery is None:
        return True

    return battery.power_plugged

def check_netUsage():
    global _last_net
    global _last_net_time

    # Get current network counters and time
    current_net = psutil.net_io_counters()
    current_time = time.monotonic()

    # Time since last network check
    elapsed_time = current_time - _last_net_time

    if elapsed_time <= 0:
        return 0.0, 0.0

    # Calculate bytes transferred since last check
    bytes_sent = current_net.bytes_sent - _last_net.bytes_sent
    bytes_received = current_net.bytes_recv - _last_net.bytes_recv

    # Convert to bytes per second
    upload_bytes_per_sec = bytes_sent / elapsed_time
    download_bytes_per_sec = bytes_received / elapsed_time

    # Convert bytes/sec to megabits/sec
    upload_mbps = (upload_bytes_per_sec * 8) / 1_000_000
    download_mbps = (download_bytes_per_sec * 8) / 1_000_000

    # Save current values for next check
    _last_net = current_net
    _last_net_time = current_time

    return upload_mbps, download_mbps

def check_MainFunc():
    CpuUse = check_CPUusage(CPUCheckLength)
    print(CpuUse, "% CPU")
    MemUse = check_MemoryUsage()
    print(round(MemUse, 2), "GB of Memory in use")
    MemPer = check_MemoryRatio()
    print(round(MemPer, 2), "% Memory in use")
    DiskUse = check_DiskUsage()
    print(round(DiskUse, 2), "GB of Disk in use")
    DiskPer = check_DiskRatio()
    print(round(DiskPer, 2), "% Disk in use")
    BatPer = check_BatteryPercent()
    print("Battery at", BatPer, "%")
    PlugIn = check_PluggedIn()
    print(PlugIn)
    upload, download = check_netUsage()
    print("Upload:", round(upload, 2), "Mbps")
    print("Download:", round(download, 2), "Mbps")


def main():
    userInput()
    if Monitoring:
        while Monitoring:
            check_MainFunc()
            time.sleep(CheckInterval)
    else:
        check_MainFunc()


if __name__ == "__main__":
    main()


