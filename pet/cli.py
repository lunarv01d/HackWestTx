import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import Taskagotchi.Taskagotchi.Taskagotchi as task


def main():
    print("Welcome to Taskagotchi!")
    print("This program will monitor your CPU usage and give you a virtual pet to take care of.")
    task.userInput()

    print("CPU check length:", task.CPUCheckLength)
    print("Check interval:", task.CheckInterval)
    print("Monitoring enabled:", task.Monitoring)

    if task.Monitoring:
        while task.Monitoring:
            task.check_MainFunc()
            time.sleep(task.CheckInterval)
    else:
        task.check_MainFunc()


if __name__ == "__main__":
    main()



