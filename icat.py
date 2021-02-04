#!/usr/bin/python3
from PIL import Image
import sys
import os
def term_color(c):
    r=int(c[0]/42)
    g=int(c[0]/42)
    b=int(c[2]/42)
    return b+6*g+36*r+16

rows,columns = os.popen('stty size', 'r').read().split()
print(columns,rows)
w=int(columns)
print(sys.argv)
img = Image.open(sys.argv[1])
print(img.width,img.height)
h=int(w*img.height/img.width/2)
print(columns, h)
rimg=img.resize((w,h))
img.close()
for y in range(h):
    for x in range(w):
        p=rimg.getpixel((x,y))
        print("\x1b[48;5;{0}m ".format(term_color(p)),end='')
    print("")
