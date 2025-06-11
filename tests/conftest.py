import os
import sys

# Insert the project root (parent of 'src') into sys.path so that tests can import from 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 