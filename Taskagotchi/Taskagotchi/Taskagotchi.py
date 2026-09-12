import psutil
import time

CPUCheckLength = 0
CheckInterval = 0
Monitoring = False


def userInput():
    global CPUCheckLength
    global CheckInterval
    global Monitoring

    CPUCheckLength = int(input("How long should each CPU check be: "))
    CheckInterval = int(input("How often should it check: "))
    Monitoring = input("Do you want to monitor your CPU usage? (True for Yes, False for No): ").strip().lower() in ("true", "yes", "1")

    if CPUCheckLength > CheckInterval:
        CPUCheckLength = CheckInterval


def check_CPUusage(CPUL):
    return (psutil.cpu_percent(CPUL))

def check_MemoryUsage():
    return psutil.virtual_memory().used / 1000000000  # bytes to Gigabytes

def check_MemoryRatio():
    return psutil.virtual_memory().used / psutil.virtual_memory().total  # Ratio of used to total

def check_DiskUsage():
    return psutil.disk_usage('/').used / 1000000000  # bytes to Gigabytes

def check_DiskRatio():
    return psutil.disk_usage('/').used / psutil.disk_usage('/').total  # Ratio of used to total

def check_BatteryPercent():
    return psutil.sensors_battery().percent

def check_PluggedIn():
    return psutil.sensors_battery().power_plugged

def check_MainFunc():
    CpuUse = check_CPUusage(CPUCheckLength)
    print(CpuUse, "% CPU")
    MemUse = check_MemoryUsage()
    print(MemUse, "GB of Memory in use")
    DiskUse = check_DiskUsage()
    print(DiskUse, "GB of Disk in use")
    BatPer = check_BatteryPercent()
    print("Battery at", BatPer, "%")
    PlugIn = check_PluggedIn()
    print(PlugIn)


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


