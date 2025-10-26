import time
import math
import json


class Task:
    def __init__(self, param):
        self.param = param
    
    def solve(self):
        time.sleep(10)
        return 0
    
    def get_plot_data(self):
        x = [i / 10 for i in range(100)]
        a = self.param.get('a', 1)
        b = self.param.get('b', 1)

        y = [a * math.sin(b * xi) for xi in x]
        return {'x': x, 'y': y}

def load_param(filename):
     with open(filename, 'r') as f:
         return json.load(f)
   

def save_param(param, filename):
    with open(filename, 'w') as f:
        json.dump(param, f, indent=2)