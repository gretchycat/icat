import math
import os,sys
from optparse import OptionParser
#from icat import *
try:
    from PIL import Image
except ImportError:
    sys.stderr.write("You need to install PIL module !\n")
    sys.exit(2)


class ICat:
    def __init__(self,y=0, x=0, w=0, f=False, mode='24bit', charset='utf8'):
#        print ('class init: '+str(y)+' '+str(x)+' '+str(w)+' '+str(f)+mode+' '+charset)
        self.w=w
        self.x=x
        self.y=y
        self.f=f
        self.mode=mode
        self.set_charset(charset)

    def set_charset(self,charset):
        if(charset in ('utf8','ascii','dos')):
            self.charset=charset
            self.cs=dict([('b0',' '),('b25',u"\u2591"),
                ('b50',u"\u2592"),('b75',u"\u2593"),('b100',u"\u2588"),
                ('bT',u"\u2580"),('bB',u"\u2584"),('bL',u"\u258C"),('bR',u"\u2590")])
            if charset=="dos":
                self.cs=dict([('b0',' '),('b25',"\xB0"),
                        ('b50',"\xB1"),('b75','\xB2'),('b100','\xDB'),
                        ('bT',"\xdf"),('bB',"\xdc"),('bL',"\xdd"),('bR',"\xde")])
            elif charset=="ascii":
                self.cs=dict([('b0',' '),('b25',"."),
                        ('b50',"="),('b75','%'),('b100','@'),
                        ('bT',"^"),('bB',"m"),('bL',"["),('bR',"]")])
        else:
            assert(f'Unknown charset: {charset}')

    def colormix(self, c1, c2, pct):#get a combined color for semisolid blocks
        if(pct<0 or pct>1):
            pct=0.5
        return (c1[0]*pct+c2[0]*(1-pct), 
                c1[1]*pct+c2[1]*(1-pct), 
                c1[2]*pct+c2[2]*(1-pct))

    def get_palette(self):  #returns standard xterm256 terminal colors
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

    def get_palette_color(self, c):
        if type(c) is tuple:
            if(self.mode=='24bit' or self.mode==''):
                return c
            elif(self.mode=='8bit' or self.mode=='256color'):
                return self.color_256(c)
            elif(self.mode=='8bitgrey' or self.mode=='grey'):
                return self.color_grey256(c)
            elif(self.mode=='4bit' or self.mode=='16color'):
                return self.color_16(c)
            elif(self.mode=='3bit' or self.mode=='8color'):
                return self.color_8(c)
            elif(self.mode=='1bit' or self.mode=='bw' or self.mode=='mono' or self.mode=='monochrome'):
                r=int((c[0]))
                g=int((c[1]))
                b=int((c[2]))
                v=int((r+g+b))
                if v<128:
                    return 0
                return 7
            return c
    
    def colordiff(self, c1, c2):  #compare how close two colors are
        return math.sqrt((c2[0]-c1[0])**2+(c2[1]-c1[1])**2+(c2[2]-c1[2])**2)

    def palette_grey_to_value(self, g):
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

    def color_256(self, c):
        d=40
        r=int(max(0,c[0]-55)/d)
        g=int(max(0,c[1]-55)/d)
        b=int(max(0,c[2]-55)/d)
        gd=10
        vc=self.color_grey256(c)
        v=self.palette_grey_to_value(vc)
        #is grey or color closer?
        dc=self.colordiff(c, (r*d+55*(r>0), g*d+55*(g>0), b*d+55*(b>0)))
        dg=self.colordiff(c, (v,v,v))
        if dg<dc:
            return vc
        return b+6*g+36*r+16

    def color_grey256(self, c):
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

    def color_16(self, c):
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
        return c+8*br

    def color_8(self, c):
        d=256/2
        r=int(c[0]/d)
        g=int(c[1]/d)
        b=int(c[2]/d)
        return r+2*g+4*b

    def ansi_color(self, fg, bg):
        fc=self.get_palette_color(fg)
        bc=self.get_palette_color(bg)
        same=False
        if fc==bc:
            same=True
#       if self.f:
            bc=0
        fs=''
        bs=''
        if(type(fc) is tuple):
            r,g,b=fc
            fs=f'38;2;{r};{g};{b}'
        elif type(fc) is int:
            if fc>15:
                fs=f'38;5;{fc}'
            else:
                c=fc%8
                br=int(fc/8)
                fs=str(br)+';'+str(c+30)
        if(type(bc) is tuple):
            r,g,b=bc
            bs=f'48;2;{r};{g};{b}'
        elif type(bc) is int:
            if bc>15:
                bs=f'48;5;{bc}'
            else:
                c=bc%8
                bs=str(c+40)
        return (f'\x1b[{fs};{bs}m',same)

    def term_print(self, c,c2):
        colstr,same=self.ansi_color(c,c2)
        if same:
            return colstr+self.cs['b100']
        return colstr+self.cs['bT']

    def term_grey16(self, c):    #term16 greys with semisolids
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
                bl=self.cs['b0']
            elif fine==1:
                bl=self.cs['b25']
            elif fine==2:
                bl=self.cs['b50']
            elif fine==3:
                bl=self.cs['b75']
            elif fine==4:
                bl=self.cs['b100']
        else:
            if fine==0:
                bl=self.cs['b100']
            elif fine==1:
                bl=self.cs['b75']
            elif fine==2:
                bl=self.cs['b50']
            elif fine==3:
                bl=self.cs['b25']
            elif fine==4:
                bl=self.cs['b0']
        return "\x1b["+fg+";"+bg+"m"+bl

    def term_bw(self, c):
        (r,g,b)=c
        v=(r+g+b)/3
        if v<51:
            return self.cs['b0']
        elif v<102:
            return self.cs['b25']
        elif v<153:
            return self.cs['b50']
        elif v<204: 
            return self.cs['b75']
        else:
            return self.cs['b100']

    def print(self, imagefile):
        F=True
        if self.f=='yes' or self.f=='true' or self.f==True:
            F=False
        if self.mode=='bw' or self.mode=='1bit' or self.mode=='4bitgrey':
            F=True
        rows,columns = os.popen('stty size', 'r').read().split()
        dy=0
        if self.y>0:
            dy=self.y
        dx=0
        if self.x>0:
            dx=self.x
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
        if self.w>0:
            w=self.w
        h=int(w*img0.height/img0.width/2)
        if F:
            img=img0.resize((w,h), resample=resample)
        else:
            img=img0.resize((w,h*2), resample=resample)
        img0.close()
        (c0,c1)=(' ',' ')
        if self.y>0:
            print('\x1b['+str(dy)+';1H', end='')
        for y in range(h):
            if self.x>0:
                print('\x1b['+str(dx)+'C', end='')
            for x in range(w):
                p=(0,0,0)
                p2=(0,0,0)
                if F:
                    p=img.getpixel((x,y))
                    p2=p
                else:
                    p=img.getpixel((x,y*2))
                    p2=img.getpixel((x,y*2+1))
                c1=''
                if (self.mode=='1bit' or self.mode=='bw'):
                    c1=self.term_bw(p)
                elif (self.mode=='4bitgrey'):
                    c1=self.term_grey16(p)
                else:
                    c1=self.term_print(p,p2)
                if (c0==c1):
                    print(c1[-1],end='')
                else:
                    print(c1,end='')
                    c0=c1
            c0=0
            if self.mode!='1bit' and self.mode!='bw':
                print("\x1b[0m")
            else:
                print('')
        img.close()

