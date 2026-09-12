import psutil
import time

cpuLen= 0
cpuLen= input("How long should each check be: ")
cpuInt = 0
cpuInt = input("How often should it check: ")
Monitoring = true

if(cpuLen > cpuInt):
    cpuLen = cpuInt


def check_CPUusage(CPUL)
    return (psutil.cpu_percent(CPUL))

def check_MainFunc()
    CpuUse = check_CPUusage(cpuLen)
    print(CpuUse)
    
while (Monitoring == true):
    time.sleep(cpuInt)
    check_MainFunc()

