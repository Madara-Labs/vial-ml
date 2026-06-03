import os
import sys
from pathlib import Path

GLOBAL_CONST = 42
UNUSED_CONST = 100

class User:
    """User docstring"""
    def __init__(self, name):
        self.name = name

    def get_name(self):
        """Returns name"""
        return self.name

class App:
    def __init__(self):
        self.user = User("Alice")
        
    def do_something(self):
        print(GLOBAL_CONST)
        name = self.user.get_name()
        self._helper()
        print("Doing something else!")
        print("test")
        return name
        
    def _helper(self):
        print("helper")

def unused_func():
    pass
