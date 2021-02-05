import multiprocessing
import sys

from main import main

if __name__ == '__main__':
    # Start bar as a process
    p = multiprocessing.Process(target=main)
    p.start()
    p.join(10)
    if p.is_alive():  # success
        print("ok, yobot lauched successfully, let's stop it")
        p.terminate()
        p.join()
        sys.exit(0)  # return 0
