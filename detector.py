import psutil
from recorder import record, websocket, disconnect

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
    while check_process("League of Legends.exe"):
        print("found")
        record(ws)
    disconnect(ws)

