#!/usr/bin/python3
from PIL import Image
import sys
import os
mode='24bit' #cga, 8bit, grey, 24bit
def term_24bit(c):
    r=int(c[0])
    g=int(c[1])
    b=int(c[2])
    return "48;2;"+str(r)+";"+str(g)+";"+str(b) 

def term_color(c): #use greys too
    d=256/6
    r=int(c[0]/d)
    g=int(c[1]/d)
    b=int(c[2]/d)
    return "48;5;"+str(b+6*g+36*r+16)

def term_grey(c):
    d=256/24
    r=int(c[0]/d)
    g=int(c[1]/d)
    b=int(c[2]/d)
    v=int((r+g+b)/3)
    return "48;5;"+str(v+232)

def term_16(c): #this is wrong.
    d=256/3
    r=int(c[0]/d)
    g=int(c[1]/d)
    b=int(c[2]/d)
    return "48;5;"+str(r+2*g+4*b)

rows,columns = os.popen('stty size', 'r').read().split()
img = Image.open(sys.argv[1])
w=int(columns)
h=int(w*img.height/img.width/2)
if img.width*2<w:
    w=img.width*2
    h=int(w*img.height/img.width/2)
o=img
img=o.resize((w,h))
o.close()
c0=0
c1=0
for y in range(h):
    for x in range(w):
        p=img.getpixel((x,y))
        if mode=='cga':
            c1=term_16(p)
        if mode=='8bit':
            c1=term_color(p)
        if mode=='grey':
            c1=term_grey(p)
        if mode=='24bit':
            c1=term_24bit(p)
        if (c0==c1):
            print(" ",end='')
        else:
            print("\x1b["+c1+"m ",end='')
            c0=c1
  
    print("\x1b[0m")
img.close()
