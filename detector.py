import psutil
from recorder import record, websocket, disconnect
import time


def check_process(process_name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == process_name:
            return True
        
    return False

# def all_processes():
#     for proc in psutil.process_iter(['name']):
#         print(proc.info['name'])


def main():
    ws = websocket()
    while not check_process("League of Legends.exe"):
        print("Waiting")
        time.sleep(2)
    print("found")
    record(ws)
    while check_process("League of Legends.exe"):
        time.sleep(1)
    print("ending")
    disconnect(ws)

if __name__ == "__main__":
    main()

