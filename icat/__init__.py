import math

def colordiff(c1, c2):  #compare how close two colors are
    return math.sqrt((c2[0]-c1[0])**2+(c2[1]-c1[1])**2+(c2[2]-c1[2])**2)

def colormix(c1, c2, pct):#get a combined color for semisolid blocks
    if(pct<0 or pct>1):
        pct=0.5
    return (c1[0]*pct+c2[0]*(1-pct), 
            c1[1]*pct+c2[1]*(1-pct), 
            c1[2]*pct+c2[2]*(1-pct))

def get_palette():  #returns standard xterm256 terminal colors
    p=[]
    for b in range(0,2):#low intensity 3bit rgb
        for g in range(0,2):
            for r in range(0,2):
                p.append((r*0x80,g*0x80,b*0x80))
    p[7]=(0xC0, 0xC0, 0xC0)
    for b in range(0,2):#high intensity 3bit rgb
        for g in range(0,2):
            for r in range(0,2):
                p.append((r*0xff,g*0xff,b*0xff))
    p[8]=(0x80, 0x80,0x80)
    for b in range(0,6):#6bit rgb
         for g in range(0,6):
             for r in range(0,6):
                 p.append((r*40+55*(r>0),g*40+55*(g>0),b*40+55*(b>0)))
    for v in range(0,24):#greys
        p.append((r*10+8,g*10+8,b*10+8))
    return p

def color_256(c):
    d=40
    r=int(max(0,c[0]-55)/d)
    g=int(max(0,c[1]-55)/d)
    b=int(max(0,c[2]-55)/d)
    gd=10
    vc=color_grey256(c)
    v=palette_grey_to_value(vc)
    #is grey closer? or color
    dc=colordiff(c, (r*d+55*(r>0), g*d+55*(g>0), b*d+55*(b>0)))
    dg=colordiff(c, (v,v,v))
    if dg<dc:
        return vc
    return b+6*g+36*r+16

def color_grey256(c):
    d=10
    r=int((c[0]-8)/d)
    g=int((c[1]-8)/d)
    b=int((c[2]-8)/d)
    v=int((r+g+b)/3)
    if v<0:
        return 16
    elif(v+232>=256):
        return 231
    return v+232

def palette_grey_to_value(g):
    if g==0:
        return 0
    elif g==7:
        return 96
    elif g==8:
        return 192
    elif g==15:
        return 255
    elif g>=16 and g<232:
        if g==16:
            return 0
        elif g==231:
            return 255
        return 0
    elif g<256:
        return (g-232)*10+8
    return 0
 
def color_16(c):
    (rg,gg,bg)=c
    d=256/2
    r=int(rg/d)
    g=int(gg/d)
    b=int(bg/d)
    v=int((rg+gg+bg)/3)
    c=r+2*g+4*b
    br=0
    if c==0 or c==7:    #handle the 4 greys
        if v<64:
            c=0
        elif v>=64 and v<128:
            c=0
            br=1
        elif v>=128 and v<192:
            c=7
        elif v>=192:
            c=7
            br=1
    else:   #if we're a color, set brightness
        if v>127:
            br=1
    return(c,br)

def color_8(c):
    d=256/2
    r=int(c[0]/d)
    g=int(c[1]/d)
    b=int(c[2]/d)
    return r+2*g+4*b

def term_24bit(c,cs):
    (r,g,b)=c
    return "\x1b[38;2;"+str(r)+";"+str(g)+";"+str(b)+"m"+cs['b100']

def term_24bith(c,c2,cs):
    (r,g,b)=c
    (r2,g2,b2)=c2
    if r==r2 and g==g2 and b==b2:
        return "\x1b[48;2;"+str(r)+";"+str(g)+";"+str(b)+"m"+cs['b0']
    return "\x1b[48;2;"+str(r)+";"+str(g)+";"+str(b)+";38;2;"+str(r2)+";"+str(g2)+";"+str(b2)+"m"+cs['bB']

def term_256(c,cs):
    return "\x1b[38;5;"+str(color_256(c))+"m"+cs['b100']

def term_256h(c,c2,cs):
    cc=color_256(c)
    cc2=color_256(c2)
    if cc==cc2: 
        return "\x1b[48;5;"+str(cc)+";38;5;"+str(cc)+"m"+cs['b100']
    else:
        return "\x1b[48;5;"+str(cc)+";38;5;"+str(cc2)+"m"+cs['bB']

def term_grey256(c,cs):    #term_256 greys
    return "\x1b[38;5;"+str(color_grey256(c))+"m"+cs['b100']

def term_grey256h(c,c2,cs):    #term_256 greys
    cc=color_grey256(c)
    cc2=color_grey256(c2)
    if cc==cc2:
        return "\x1b[48;5;"+str(cc)+";38;5;"+str(cc)+"m"+cs['b100']
    else:
        return "\x1b[48;5;"+str(cc)+";38;5;"+str(cc2)+"m"+cs['bB']

def term_grey16(c,cs):    #term16 greys with semisolids
    (r,g,b)=c
    v=(r+g+b)/3 
    bl='X'
    fg="0;1;31"
    bg="41"
    rough=int(v/(256/3))
    fine=int(v%(256/3)/(256/3/5))
    if(rough==0):
        bg="40"
        fg="0;1;30"
    elif(rough==1):
        bg="47"
        fg="0;1;30"
    elif(rough==2):
        bg="47"
        fg="0;1;37"
    if rough==0 or rough==2:
        if fine==0:
            bl=cs['b0']
        elif fine==1:
            bl=cs['b25']
        elif fine==2:
            bl=cs['b50']
        elif fine==3:
            bl=cs['b75']
        elif fine==4:
            bl=cs['b100']
    else:
        if fine==0:
            bl=cs['b100']
        elif fine==1:
            bl=cs['b75']
        elif fine==2:
            bl=cs['b50']
        elif fine==3:
            bl=cs['b25']
        elif fine==4:
            bl=cs['b0']
    return "\x1b["+fg+";"+bg+"m"+bl

def term_16h(c,c2,cs):
    (cc,br)=color_16(c)
    (cc2,br2)=color_16(c2)
    if cc==cc2 and br==br2:
        return "\x1b[0;"+str(br)+";"+str(30+cc)+"m"+cs['b100']
    elif br==1:   #16 color ansi doesnt usually support bright backgrounds
        return "\x1b[0;1;"+str(30+cc)+";"+str(40+cc2)+"m"+cs['bT']
    elif br2==1:
        return "\x1b[0;1;"+str(30+cc2)+";"+str(40+cc)+"m"+cs['bB']
    else:
        return "\x1b[0;"+str(30+cc)+"m"+cs['b100']

def term_16(c,cs):
    (cc,br)=color_16(c)
    if br==1:   #16 color ansi doesnt usually support bright backgrounds
        return "\x1b[0;1;"+str(30+cc)+"m"+cs['b100']
    else:
        return "\x1b[0;"+str(30+cc)+"m"+cs['b100']

def term_8(c,cs): 
    return "\x1b["+str(30+color_8(c))+"m"+cs['b100']

def term_8h(c, c2,cs): 
   return "\x1b[0;"+str(40+color_8(c))+";"+str(30+color_8(c2))+"m"+cs['bB']

def term_bw(c,cs):
    (r,g,b)=c
    v=(r+g+b)/3
    if v<51:
        return cs['b0']
    elif v<102:
        return cs['b25']
    elif v<153:
        return cs['b50']
    elif v<204: 
        return cs['b75']
    else:
        return cs['b100']

import os,sys
from optparse import OptionParser
from icat import *
try:
    from PIL import Image
except ImportError:
    sys.stderr.write("You need to install PIL module !\n")
    sys.exit(2)

def docat(imagefile, mode, forcew, full, charset, screenx, screeny):
    cs=dict([('b0',' '),('b25',u"\u2591"),
        ('b50',u"\u2592"),('b75',u"\u2593"),('b100',u"\u2588"),
        ('bT',u"\u2580"),('bB',u"\u2584"),('bL',u"\u258C"),('bR',u"\u2590")])
    if charset=="dos":
        cs=dict([('b0',' '),('b25',"\xB0"),
                ('b50',"\xB1"),('b75','\xB2'),('b100','\xDB'),
                ('bT',"\xdf"),('bB',"\xdc"),('bL',"\xdd"),('bR',"\xde")])
    elif charset=="ascii":
        cs=dict([('b0',' '),('b25',"."),
                ('b50',"="),('b75','%'),('b100','@'),
                ('bT',"^"),('bB',"m"),('bL',"["),('bR',"]")])
    F=True
    if full=='yes' or full=='true' or full==True:
        F=False
    if mode=='bw' or mode=='1bit' or mode=='4bitgrey':
        F=True
    rows,columns = os.popen('stty size', 'r').read().split()
    dy=0
    if screeny>0:
        dy=screeny
    dx=0
    if screenx>0:
        dx=screenx
    w=int(columns)-dx
    try:
        img0 = Image.open(imagefile).convert(mode='RGB')
    except Exception as e:
        sys.stderr.write(str(e)+"\n")
        return
    resample=3
    if F:
        if img0.width*2<w:
            w=img0.width*2
            resample=0
    else:
        if img0.width<w:
            w=img0.width
            resample=0
    if forcew>0:
        w=forcew
    h=int(w*img0.height/img0.width/2)
    if F:
        img=img0.resize((w,h), resample=resample)
    else:
        img=img0.resize((w,h*2), resample=resample)
    img0.close()
    (c0,c1)=(' ',' ')
    if screeny>0:
        print('\x1b['+str(dy)+';1H', end='')
    for y in range(h):
        if screenx>0:
            print('\x1b['+str(dx)+'C', end='')
        for x in range(w):
            p=(0,0,0)
            p2=(0,0,0)
            if F:
                p=img.getpixel((x,y))
            else:
                p=img.getpixel((x,y*2))
                p2=img.getpixel((x,y*2+1))
            c1=''
            if (mode=='1bit' or mode=='bw'):
                c1=term_bw(p,cs)
            elif (mode=='3bit' or mode=='8color'):
                if F:
                    c1=term_8(p,cs)
                else:
                    c1=term_8h(p,p2,cs)
            elif (mode=='4bit' or mode=='16color'):
                if F:
                    c1=term_16(p,cs)
                else:
                    c1=term_16h(p,p2,cs)
            elif (mode=='4bitgrey'):
                if F:
                    c1=term_grey16(p,cs)
                else:
                    c1=term_8h(p,p2,cs)
            elif (mode=='8bit' or mode=='256color'):
                if F:
                    c1=term_256(p,cs)
                else:
                    c1=term_256h(p,p2,cs)
            elif (mode=='8bitgrey' or mode=='grey'):
                if F:
                    c1=term_grey256(p,cs)
                else:
                    c1=term_grey256h(p,p2,cs)
            if (mode=='24bit' or c1==''):
                if F:
                    c1=term_24bit(p,cs)
                else:
                    c1=term_24bith(p,p2,cs)
            if (c0==c1):
                print(c1[-1],end='')
            else:
                print(c1,end='')
                c0=c1
        c0=0
        if mode!='1bit' and mode!='bw':
            print("\x1b[0m")
        else:
            print('')
    img.close()

