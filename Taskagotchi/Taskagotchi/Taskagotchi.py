import psutil
import time

CPUCheckLength = 0
CPUCheckLength = int(input("How long should each check be: "))
CPUCheckInterval = 0
CheckInterval = int(input("How often should it check: "))
Monitoring = True

if(CPUCheckLength > CheckInterval):
    CPUCheckLength = CheckInterval

def check_CPUusage(CPUL):
    return (psutil.cpu_percent(CPUL))

def check_MainFunc():
    CpuUse = check_CPUusage(CPUCheckLength)
    print(CpuUse)

while (Monitoring == True):
    time.sleep(CheckInterval)
    check_MainFunc()
