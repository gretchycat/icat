import math,io,os,sys,termios,tty,subprocess,tempfile
from base64 import standard_b64encode
from optparse import OptionParser
#from icat import *
try:
    from PIL import Image
except ImportError:
    sys.stderr.write("You need to install PIL module !\n")
    sys.exit(2)

def get_terminal_size():
    import array, fcntl, sys, termios
    buf = array.array('H', [0, 0, 0, 0])
    fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ, buf)
    # Create a dictionary with meaningful keys
    window_info = {
        "rows": buf[0],
        "columns": buf[1],
        "width": buf[2],
        "height": buf[3]
    }
    return window_info

def execute_command(command, pipe=None, print=True):
    """
    Executes a command in the system and logs the command line and output.
    """
    try:
        output=""
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        if pipe:
            process.stdin.write(pipe)
        for line in process.stdout:
            #logging.debug(line.rstrip('\n'))
            output+=line
        process.wait()
        process.output=output
        if print:
            return output
        else:
            return ""#output
    except Exception as e:
        return f"Error running: {' '.join(command)}"

class ICat:
    def __init__(self,y=0, x=0, w=0, h=0, zoom='aspect', f=False, mode='24bit', charset='utf8', browse=False, place=True):
        self.w=w
        self.h=h
        self.zoom=zoom
        self.x=x
        self.y=y
        self.f=f
        self.place=place
        terminfo=get_terminal_size()
        if terminfo['width']==0:
            if mode in ['kitty', 'sixel']:
                mode='4bit'
        if mode.lower()=='auto':
            term=os.environ.get('TERM', '')
            konsole_ver=os.environ.get('KONSOLE_VERSION', '')
            if terminfo['width']==0:
                mode='4bit'
            if 'kitty' in term:
                mode='kitty'
            elif 'vt340' in term or len(konsole_ver or '')>0:
                mode='sixel'
            else:
                mode='24bit'
        self.mode=mode
        self.set_charset(charset)

    def set_charset(self,charset):
        if(charset in ('utf8','ascii')):
            self.charset=charset
            self.cs=dict([('b0',' '),('b25',u"\u2591"),
                ('b50',u"\u2592"),('b75',u"\u2593"),('b100',u"\u2588"),
                ('bT',u"\u2580"),('bB',u"\u2584"),('bL',u"\u258C"),('bR',u"\u2590")])
            if charset=="ascii":
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
            elif(self.mode=='8bitbright' or self.mode=='256bright'):
                return self.color_256_bright(c)
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

    def bright(self, c, br):
        r=int(c[0]*br)
        g=int(c[1]*br)
        b=int(c[2]*br)
        r=min(r, 255)
        g=min(g, 255)
        b=min(b, 255)
        return [r, g, b]

    def color_256(self, c):
        d=40
        o=55
        r=int(max(0,c[0]-o)/d)
        g=int(max(0,c[1]-o)/d)
        b=int(max(0,c[2]-o)/d)
        #is grey or color closer?
        vc=self.color_grey256(c)
        v=self.palette_grey_to_value(vc)
        dc=self.colordiff(c, (r*d+o*(r>0), g*d+o*(g>0), b*d+o*(b>0)))
        dg=self.colordiff(c, (v,v,v))
        if dg<dc:
            return vc
        return b+6*g+36*r+16

    def color_256_bright(self, c):
        c2=self.bright(c, 1.625)
        return self.color_256(c2)

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
                fs=str(c+30+br*60)
        if(type(bc) is tuple):
            r,g,b=bc
            bs=f'48;2;{r};{g};{b}'
        elif type(bc) is int:
            if bc>15:
                bs=f'48;5;{bc}'
            else:
                c=bc%8
                br=int(bc/8)
                bs=str(c+40+br*60)
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
        fg="0;31"
        bg="41"
        rough=int(v/(256/3))
        fine=int(v%(256/3)/(256/3/5))
        if(rough==0):
            bg="40"
            fg="90"
        elif(rough==1):
            bg="47"
            fg="90"
        elif(rough==2):
            bg="47"
            fg="97"
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

    def getVidFrame(self, videofile, time):
        vidframe=temp_output_path = tempfile.NamedTemporaryFile(delete=True, suffix=f".png").name
        maxtime=1
        err=""
        try:
            # Use subprocess to run ffmpeg and extract the frame
            command = [
                "ffmpeg",
                "-i", videofile,
                "-ss", str(time*maxtime),  # Specify the time in seconds
                "-vframes:v", "1",  # Extract only 1 frame
                #"-f", ".png",  # Output format
                "-y",
                vidframe
            ]
            err=execute_command(command, pipe=None, print=False)
        except:
            return None, err
        return vidframe, err

    def openImage(self, imagefile, lines, columns):
        self.vidframe=None
        err=""
        img0=None
        try:
            img0 = Image.open(imagefile).convert(mode='RGB')
        except Exception as e: #TODO try loading a video frame using ffmpeg
            self.vidframe, err=self.getVidFrame(imagefile, 0.1)
        if not img0 and self.vidframe:
            try:
                img0 = Image.open(self.vidframe).convert(mode='RGB')
            except:
                pass
        if not img0:
            #sys.stderr.write(f"{err}\n")
            #sys.stderr.write(f"Can't open {imagefile}\n")
            return None, (0,0), err
        if self.w==0:
            self.w=columns
        imageAR=img0.height/img0.width
        termAR=-1
        termW, termH=self.w,self.h
        cropW, cropH=0,0
        if termW>0 and termH>0:   #modify width, height, dx, dy etc
            termAR=termH/termW
            if self.zoom=='aspect':
                newH=int((termW*imageAR)/2)
                newW=int((termH/imageAR)*2)
                if newH<termH:
                    termH=newH
                if newW<termW:
                    termW=newW
            elif self.zoom=='fill':
                cropW=termW
                cropH=termH
                newH=int((termW*imageAR)/2)
                newW=int((termH/imageAR)*2)
                if newH>termH:
                    termH=newH
                if newW>termW:
                    termW=newW
            elif self.zoom=='stretch':
                pass
        resample=3
        w=termW
        h=termH
        if self.F:  #if the image is smaller than the terminal
            if img0.width*2<w:
                w=img0.width*2
                resample=0
        else:
            if img0.width<w:
                w=img0.width
                resample=0
        if termW>0:
            w=termW
        if(termH==0):
            h=int(w*img0.height/img0.width/2)
        termH=h
        try:
            if self.F:
                img=img0.resize((int(w),int(h)), resample=resample)
            else:
                img=img0.resize((int(w),int(h)*2), resample=resample)
        except:
            return None, (0,0) ,err
        img0.close()
        if cropW>0 or cropH>0:
            termW, termH=cropW, cropH
        return img, (termW, termH), None

    def printLine(self, img, y, maxy, imgwidth):
        buffer=""
        if imgwidth>img.width:
            imgwidth=img.width
        if img:
            addy=(maxy-img.height)/2
            y=y-addy
        (c0,c1)=(' ',' ')
        for x in range(imgwidth):
            p=(0,0,0)
            p2=(0,0,0)
            if(img):
                if(y>=0):
                    if y<img.height:
                        p=img.getpixel((x,y))
                        if self.F:
                            p2=p
                        else:
                            if(y+1<img.height):
                                p2=img.getpixel((x,y+1))
            c1=''
            if (self.mode=='1bit' or self.mode=='bw'):
                c1=self.term_bw(p)
            elif (self.mode=='4bitgrey'):
                c1=self.term_grey16(p)
            else:
                c1=self.term_print(p,p2)
            if (c0==c1):
                buffer+=c1[-1]
            else:
                buffer+=c1
                c0=c1
        return buffer

    def centertext(self, text, width):
        add=width-len(text)
        if add>0:
            return " "*math.floor(add/2)+text+" "*math.ceil(add/2)
        if add<0:
            return text[:width]
        return text

    def print(self, imagefile):
        def write_chunked(data, items):
            def serialize_gr_command(payload, items):
                cmd = ','.join(f'{k}={v}' for k, v in items.items())
                ans = []
                w = ans.append
                w('\x1b_G'), w(cmd)
                if payload:
                    w(';')
                    w(payload)
                w('\x1b\\')
                return ''.join(ans)
            out=''
            base64=standard_b64encode(data).decode('ascii')
            while base64:
                chunk, base64 = base64[:4096], base64[4096:]
                m = 1 if base64 else 0
                items['m']=m
                out+=(serialize_gr_command(chunk, items ))
                items.clear()
            return out

        pos=""
        dx, dy=self.x, self.y
        if dx or dy:
            if dx==0:
                dx=1
            if dy==0:
                dy=1
            pos=f'\x1b[{dy};{dx+1}H'

        if self.mode in ['kitty', 'sixel']:
            desc=""
            #image_size = f'\x1b[8;{h};{w}t'
            imglist=[]
            img=None
            self.vidframe=None
            err=""
            if type(imagefile) is Image:
                img=imagefile
            if type(imagefile) is str:
                try:
                    img = Image.open(imagefile)
                except:
                    pass
            if not img:
                self.vidframe, err=self.getVidFrame(imagefile, 0.1)
            if not img and self.vidframe:
                try:
                    img = Image.open(self.vidframe).convert(mode='RGB')
                except:
                    pass
            if not img:
                if err:
                    return f'{pos}{err}'
                else:
                    return f"{pos}Not an Image: '{imagefile}'"#TODO get a list of frames from videos
            img_w, img_h=img.size
            img_ar=img_h/img_w
            term_size=get_terminal_size()
            cell_w=term_size['width']/term_size['columns']
            cell_h=term_size['height']/term_size['rows']
            # Calculate the scaling factor while preserving the aspect ratio
            w=self.w or term_size['columns']
            h=self.h or term_size['rows']
            scale=img_w/w
            scale2=img_h/((h-1)*2)
            if scale2>scale:
                scale=scale2
            new_h=img_h/scale/2
            new_w=img_w/scale
            dx, dy=self.x, self.y
            if self.mode=="sixel":
                img.close()
                if self.vidframe:
                    i=execute_command(['img2sixel', '-w', f'{int((new_w-1)*cell_w)}', '-h', f'{int(new_h*cell_h)}',self.vidframe])
                    self.vidframe=None
                else:
                    i=execute_command(['img2sixel', '-w', f'{int((new_w-1)*cell_w)}', '-h', f'{int(new_h*cell_h)}', imagefile])

                return f"{pos}{i}"
            elif self.mode=="kitty":
                try:
                    img = img.resize((int(new_w*cell_w), int(new_h*cell_h)), Image.LANCZOS)
                    # Generate a PNG stream
                    png_stream = io.BytesIO()
                    self.vidframe=None
                    img.save(png_stream, format='PNG')
                    img.close()
                    png_stream.seek(0)
                    items={"a": "T", "f":100}#, "r":h, "c":w}
                    i=write_chunked(png_stream.getvalue(), items)
                    png_stream.close()
                    return f"{pos}{i}"
                except:return f"{pos}Failed to resize image: '{imagefile}'"
        else:
            buffer=""
            if type(imagefile) is str:
                imagefile=(imagefile, )

            self.F=True
            if self.f=='yes' or self.f=='true' or self.f==True:
                self.F=False
            if self.mode=='bw' or self.mode=='1bit' or self.mode=='4bitgrey':
                self.F=True
            screenrows,screencolumns = os.popen('stty size', 'r').read().split()
            scroll_mode= not bool(self.place)
            dy=0
            if self.y>0:
                dy=self.y
            dx=0
            if self.x>0:
                dx=self.x
            w=int(screencolumns)-dx
            if self.y>0:
               buffer+=f'\x1b[{dy};{1}H'
            images=()
            maxy=0
            buffer+='\x1b[s'

            imgwidth=self.w
            if(self.w==0):    #when printing mulyiple images per width, split.
                imgwidth=int(w/len(imagefile))-(1 if len(imagefile)>1 else 0)
                if len(imagefile)>1:
                    self.w=imgwidth
            err=""
            for i in imagefile:
                if len(i)>0:
                    img, (imgwidth,imgheight), err=self.openImage(i, int(screenrows), int(screencolumns))
                    if not img:
                        if err:
                            return f"{pos}{err}"
                        else:
                            return f"{pos}Not an Image: '{i}'"#TODO get a list of frames from videos

                    img_w, img_h=img.size
                    if(img):
                        if img.height>maxy:
                            maxy=img.height
                        images=images+(img, )
            imgwidth=self.w
            for y in range(0, maxy, 1 if self.F else 2):
                if self.x>0:
                    buffer+=('\x1b['+str(dx)+'C')

                for img in images:
                    buffer+=(self.printLine(img, y, maxy, imgwidth))
                    if len(imagefile)>1:
                        if self.mode!='1bit' and self.mode!='bw':
                            if scroll_mode:
                                buffer+='\x1b[0m\n'
                            else:
                                buffer+='\n\x1b[u\x1b[B\x1b[s'
                        else:
                            buffer+="\n"

                if self.mode!='1bit' and self.mode!='bw':
                    if scroll_mode:
                        buffer+='\x1b[0m\n'
                    else:
                        buffer+='\x1b[u\x1b[B\x1b[s'
                else:
                    buffer+="\n"
            for img in images:
                if(img):
                    img.close()
            self.vidframe=None
            if len(imagefile)>1:
                if self.x>0:
                   buffer+=('\x1b['+str(dx)+'C')
                for fn in imagefile:
                   buffer+=(self.centertext(os.path.basename(fn), imgwidth)+" ")
            return buffer

