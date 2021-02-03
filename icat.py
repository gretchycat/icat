#!/usr/bin/python3
from PIL import Image
import sys
import os
rows,columns = os.popen('stty size', 'r').read().split()
print(columns,rows)
print(sys.argv)


