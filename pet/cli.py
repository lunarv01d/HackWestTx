from Taskagotchi.Taskagotchi.Taskagotchi import CPUCheckLength, CheckInterval


def cli():
    print("Welcome to Taskagotchi!")
    print("This program will monitor your CPU usage and give you a virtual pet to take care of.")
    print("Please enter the following information:")

    cpuLenCLI = CPUCheckLength
    print(cpuLenCLI)


if __name__ == "__main__":
    cli()