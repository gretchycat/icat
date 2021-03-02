#!/usr/bin/python3
from PIL import Image
from optparse import OptionParser
import sys, math, os

def main():
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

    def term_24bit(c):
        (r,g,b)=c
        return "\x1b[48;2;"+str(r)+";"+str(g)+";"+str(b)+"m"+b0

    def term_24bith(c,c2):
        (r,g,b)=c
        (r2,g2,b2)=c2
        if r==r2 and g==g2 and b==b2:
            return "\x1b[48;2;"+str(r)+";"+str(g)+";"+str(b)+"m"+b0
        return "\x1b[38;2;"+str(r)+";"+str(g)+";"+str(b)+";48;2;"+str(r2)+";"+str(g2)+";"+str(b2)+"m"+bT

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

    def term_256(c):
        return "\x1b[48;5;"+str(color_256(c))+"m"+b0

    def term_256h(c,c2):
        cc=color_256(c)
        cc2=color_256(c2)
        if cc==cc2: 
            return "\x1b[48;5;"+str(cc)+"m"+b0
        else:
            return "\x1b[38;5;"+str(cc)+";48;5;"+str(cc2)+"m"+bT

    def color_grey256(c):
        d=10
        r=int((c[0]-8)/d)
        g=int((c[1]-8)/d)
        b=int((c[2]-8)/d)
        v=int((r+g+b)/3)
        if v<0:
            return 16
        if(v+232>=256):
            return 231
        return v+232

    def palette_grey_to_value(g):
        if g==0:
            return 0
        if g==7:
            return 96
        if g==8:
            return 192
        if g==15:
            return 255
        if g>=16 and g<232:
            if g==16:
                return 0
            if g==231:
                return 255
            return 0
        if g<256:
            return (g-232)*10+8
        return 0
     
    def term_grey256(c):    #term_256 greys
        return "\x1b[48;5;"+str(color_grey256(c))+"m"+b0

    def term_grey256h(c,c2):    #term_256 greys
        cc=color_grey256(c)
        cc2=color_grey256(c2)
        if cc==cc2:
            return "\x1b[48;5;"+str(cc)+"m"+b0
        else:
            return "\x1b[38;5;"+str(cc)+";48;5;"+str(cc2)+"m"+bT

    def term_grey16(c):    #term16 greys with semisolids
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
        if(rough==1):
            bg="47"
            fg="0;1;30"
        if(rough==2):
            bg="47"
            fg="0;1;37"
        if rough==0 or rough==2:
            if fine==0:
                bl=b0
            if fine==1:
                bl=b25
            if fine==2:
                bl=b50
            if fine==3:
                bl=b75
            if fine==4:
                bl=b100
        else:
            if fine==0:
                bl=b100
            if fine==1:
                bl=b75
            if fine==2:
                bl=b50
            if fine==3:
                bl=b25
            if fine==4:
                bl=b0
        return "\x1b["+fg+";"+bg+"m"+bl

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
            if v>=64 and v<128:
                c=0
                br=1
            if v>=128 and v<192:
                c=7
            if v>=192:
                c=7
                br=1
        else:   #if we're a color, set brightness
            if v>127:
                br=1
        return(c,br)

    def term_16h(c,c2):
        (cc,br)=color_16(c)
        (cc2,br2)=color_16(c2)
        if cc==cc2 and br==br2:
            return "\x1b[0;"+str(br)+";"+str(30+cc)+"m"+b100
        if br==1:   #16 color ansi doesnt usually support bright backgrounds
            return "\x1b[0;1;"+str(30+cc)+";"+str(40+cc2)+"m"+bT
        if br2==1:
            return "\x1b[0;1;"+str(30+cc2)+";"+str(40+cc)+"m"+bB
        else:
            return "\x1b[0;"+str(40+cc)+"m"+b0

    def term_16(c):
        (cc,br)=color_16(c)
        if br==1:   #16 color ansi doesnt usually support bright backgrounds
            return "\x1b[0;1;"+str(30+cc)+"m"+b100
        else:
            return "\x1b[0;"+str(40+cc)+"m"+b0

    def color_8(c):
        d=256/2
        r=int(c[0]/d)
        g=int(c[1]/d)
        b=int(c[2]/d)
        return r+2*g+4*b

    def term_8(c): 
        return "\x1b["+str(40+color_8(c))+"m"+b0

    def term_8h(c, c2): 
       return "\x1b[0;"+str(40+color_8(c))+";"+str(30+color_8(c2))+"m"+bB

    def term_bw(c):
        (r,g,b)=c
        v=(r+g+b)/3
        if v<51:
            return b0
        if v<102:
            return b25
        if v<153:
            return b50
        if v<204: 
            return b75
        else:
            return b100

    def docat(imagefile, mode, forcew, half):
        H=0
        if half=='yes' or half=='true':
            H=1
        if mode=='bw' or mode=='1bit' or mode=='4bitgrey':
            H=0
        rows,columns = os.popen('stty size', 'r').read().split()
        w=int(columns)
        img0 = Image.open(imagefile).convert(mode='RGB')
        resample=3
        if H==0:
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
        if H==0:
            img=img0.resize((w,h), resample=resample)
        else:
            img=img0.resize((w,h*2), resample=resample)
        img0.close()
        (c0,c1)=(' ',' ')
        for y in range(h):
            for x in range(w):
                p=(0,0,0)
                p2=(0,0,0)
                if H==0:
                    p=img.getpixel((x,y))
                else:
                    p=img.getpixel((x,y*2))
                    p2=img.getpixel((x,y*2+1))
                c1=''
                if (mode=='1bit' or mode=='bw'):
                    c1=term_bw(p)
                if (mode=='3bit' or mode=='8color'):
                    if H==0:
                        c1=term_8(p)
                    else:
                        c1=term_8h(p,p2)
                if (mode=='4bit' or mode=='16color'):
                    if H==0:
                        c1=term_16(p)
                    else:
                        c1=term_16h(p,p2)
                if (mode=='4bitgrey'):
                    if H==0:
                        c1=term_grey16(p)
                    else:
                        c1=term_8h(p,p2)
                if (mode=='8bit' or mode=='256color'):
                    if H==0:
                        c1=term_256(p)
                    else:
                        c1=term_256h(p,p2)
                if (mode=='8bitgrey' or mode=='grey'):
                    if H==0:
                        c1=term_grey256(p)
                    else:
                        c1=term_grey256h(p,p2)
                if (mode=='24bit' or c1==''):
                    if H==0:
                        c1=term_24bit(p)
                    else:
                        c1=term_24bith(p,p2)
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

    #TODO: try shlex or argparse instead
    parser=OptionParser(usage="usage: %prog [options] filelist")
    parser.add_option("-m", "--mode", dest="mode", default="24bit", 
            help="Color mode: 24bit | 8bit | 8bitgrey | 4bit | 4bitgrey | 3bit | bw")
    parser.add_option("-w", "--width", dest="width", default="0",
            help="0=auto, w>0 constrains image to the width")
    parser.add_option("-H", "--halfblock", dest="half", default="yes",
            help="Use half-blocks: no | yes")
    parser.add_option("-c", "--charset", dest="charset", default="utf8",
            help="Character set: utf8 | dos | ascii")
    (options, args)=parser.parse_args()
    if len(args)==0:
        parser.print_help()
    # 0%, 25%, 50%, 75% and 100% solid blocks
    #top, bottom, left and right half block
    (b0,b25,b50,b75,b100)=(' ',u"\u2591",u"\u2592",u"\u2593",u"\u2588")
    (bT,bB,bL,bR)=(u"\u2580",u"\u2584",u"\u258C",u"\u2590")
    if options.charset=="dos":
        (b0,b25,b50,b75,b100)=(' ','\xB0','\xB1','\xB2','\xDB')
        (bT,bB,bL,bR)=('\xDF','\xDC','\xDD','\xDE')
    if options.charset=="ascii":
        (b0,b25,b50,b75,b100)=(' ','.','=','%','#')
        (bT,bB,bL,bR)=('^','m','[',']')
    
    for imagefile in args:
        docat(imagefile, options.mode, int(options.width), options.half)

if __name__=="__main__":
    main()

