import psutil
import requests

def check_process(process_name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == process_name:
            return True
        
    return False


def all_processes():
    for proc in psutil.process_iter(['name']):
        print(proc.info['name'])
