import psutil
import time

CPUCheckLength = 0
CPUCheckLength = int(input("How long should each CPU check be: "))
CPUCheckInterval = 0
CheckInterval = int(input("How often should it check: "))
Monitoring = True

if(CPUCheckLength > CheckInterval):
    CPUCheckLength = CheckInterval

def check_CPUusage(CPUL):
    return (psutil.cpu_percent(CPUL))

def check_MemoryUsage():
    return ((psutil.virtual_memory().used / 1000000000)) #bytes to Gigabytes

def check_DiskUsage():
    return ((psutil.disk_usage('/').used / 1000000000)) #bytes to Gigabytes

def check_MainFunc():
    CpuUse = check_CPUusage(CPUCheckLength)
    print(CpuUse, " CPU")
    MemUse = check_MemoryUsage()
    print(MemUse, " Memory")
    DiskUse = check_DiskUsage()
    print(DiskUse, " Disk")

while (Monitoring == True):
    time.sleep(CheckInterval)
    check_MainFunc()

if _name_ == "_main_":
    main()
