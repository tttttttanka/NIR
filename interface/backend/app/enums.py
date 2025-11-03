from enum import Enum

class Status(str, Enum):
    pending = "pending"
    running = "running"
    done = "done"
