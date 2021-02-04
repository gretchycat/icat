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
c0=0
c1=0
for y in range(h):
    for x in range(w):
        p=rimg.getpixel((x,y))
        c1=term_color(p)
        if (c0==c1):
            print(" ",end='')
        else:
            print("\x1b[48;5;{0}m ".format(c1),end='')
            c0=c1
  
    print("")
