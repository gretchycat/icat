#!/usr/bin/python3
from PIL import Image
import sys
import os
colorbits=24
def term_24bit(c):
    r=int(c[0])
    g=int(c[1])
    b=int(c[2])
    return str(r)+";"+str(g)+";"+str(b) 

def term_color(c):
    d=256/6
    r=int(c[0]/d)
    g=int(c[1]/d)
    b=int(c[2]/d)
    return b+6*g+36*r+16

def term_grey(c):
    d=256/24
    r=int(c[0]/d)
    g=int(c[1]/d)
    b=int(c[2]/d)
    v=int((r+g+b)/3)
    return v+232

def term_16(c): #this is wrong.
    d=256/3
    r=int(c[0]/d)
    g=int(c[1]/d)
    b=int(c[2]/d)
    return r+2*g+4*b

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
        c1=term_24bit(p)
        if (c0==c1):
            print(" ",end='')
        else:
            if(colorbits==8):
                print("\x1b[48;5;{0}m ".format(c1),end='')
            else: 
                if(colorbits==24):
                    print("\x1b[48;2;{0}m ".format(c1),end='')
            c0=c1
  
    print("")
