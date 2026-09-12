import psutil
import time

int CPUCheckLength;
CPUCheckLength = input("How long should each check be: ")
int CPUCheckInterval;
CheckInterval = input("How often should it check: ")
bool Monitoring = true;

if(CPUCheckLength > CheckInterval)
{
    CPUCheckLength = CheckInterval;
    }

def check_CPUusage(CPUL)
    return (psutil.cpu_percent(CPUL))

def check_MainFunc()
{
        CpuUse = check_CPUusage(CPUCheckLength);
        print(CpuUse);
    
    }

while (Monitoring == true)
{
    time.sleep(CheckInterval);
    check_MainFunc();

    }
