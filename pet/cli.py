from Taskagotchi.Taskagotchi.Taskagotchi import CPUCheckLength, CheckInterval, check_MainFunc, userInput
import time

Monitoring = True


def main():
    print("Welcome to Taskagotchi!")
    print("This program will monitor your CPU usage and give you a virtual pet to take care of.")
    userInput()

    cpuLenCLI = CPUCheckLength
    print(cpuLenCLI)
    
if __name__ == "__main__":
  main()
    
while (Monitoring == True):
    time.sleep(CheckInterval)
    check_MainFunc()



