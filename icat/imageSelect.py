#!/usr/bin/python3
import io, os, sys, math, termios, tty, subprocess, base64, time, select, shutil
from optparse import OptionParser
from icat import ICat
from PIL import Image
from base64 import standard_b64encode
"""
         0   1   2   3   4   5   6   7   8   9   A   B   C   D   E   F
U+250x   ─   ━   │   ┃   ┄   ┅   ┆   ┇   ┈   ┉   ┊   ┋   ┌   ┍   ┎   ┏
U+251x   ┐   ┑   ┒   ┓   └   ┕   ┖   ┗   ┘   ┙   ┚   ┛   ├   ┝   ┞   ┟
U+252x   ┠   ┡   ┢   ┣   ┤   ┥   ┦   ┧   ┨   ┩   ┪   ┫   ┬   ┭   ┮   ┯
U+253x   ┰   ┱   ┲   ┳   ┴   ┵   ┶   ┷   ┸   ┹   ┺   ┻   ┼   ┽   ┾   ┿
U+254x   ╀   ╁   ╂   ╃   ╄   ╅   ╆   ╇   ╈   ╉   ╊   ╋   ╌   ╍   ╎   ╏

         0   1   2   3   4   5   6   7   8   9   A   B   C   D   E   F
U+255x   ═   ║   ╒   ╓   ╔   ╕   ╖   ╗   ╘   ╙   ╚   ╛   ╜   ╝   ╞   ╟
U+256x   ╠   ╡   ╢   ╣   ╤   ╥   ╦   ╧   ╨   ╩   ╪   ╫   ╬   ╭   ╮   ╯
U+257x   ╰   ╱   ╲   ╳   ╴   ╵   ╶   ╷   ╸   ╹   ╺   ╻   ╼   ╽   ╾   ╿

         0   1   2   3   4   5   6   7   8   9   A   B   C   D   E   F
U+258x   ▀   ▁   ▂   ▃   ▄   ▅   ▆   ▇   █   ▉   ▊   ▋   ▌   ▍   ▎   ▏
U+259x   ▐   ░   ▒   ▓   ▔   ▕   ▖   ▗   ▘   ▙   ▚   ▛   ▜   ▝   ▞   ▟
"""

def pause_terminal_output():
    sys.stdout.flush()
    os.system('stty -icanon -echo')

def resume_terminal_output():
    sys.stdout.flush()
    os.system('stty icanon echo')

grchr={}
grchr['ascii']={'hline':'-', 'vline':'|',
                'TH':'^', 'BH':'o',
                'B0':' ', 'B25':':', 'BN60':'$', 'B75':'#', 'B100':'@',
                'BLC':'\\', 'TLC':'/', 'BRC':'/', 'TRC':'\\',
                'BLB':'+', 'TLB':'+', 'BRB':'+', 'TRB':'+',
                'TBR':'|', 'TBL':'|', 'BLR':'-', 'TLR':'-', 'TBLR':'+',
                }

grchr['utf8']={ 'hline':'\u2500', 'vline':'\u2502',
                'TH':'\u2580', 'BH':'\u2584',
                'B0':' ', 'B25':'\u2591', 'B50':'\u2593', 'B75':'\u2593', 'B100':'\u2588',
                'BLC':'\u256E', 'TLC':'\u256F', 'BRC':'\u256D', 'TRC':'\u2570',
                'BLB':'\u2510', 'TLB':'\u2518', 'BRB':'\u250C', 'TRB':'\u2514',
                'TBR':'\u251C', 'TBL':'\u2524', 'BLR':'\u252C', 'TLR':'\u2534', 'TBLR':'\u253C',
               }

theme={}
theme['inside']={
        'TL': 'BH', 'TC': 'BH', 'TR': 'BH',
        'ML': 'B100', 'MC': 'B75', 'MR': 'B100',
        'BL': 'TH', 'BC': 'TH', 'BR': 'TH'
        }

theme['outside']={
        'TL': 'B100', 'TC': 'TH', 'TR': 'B100',
        'ML': 'B100', 'MC': 'B0', 'MR': 'B100',
        'BL': 'B100', 'BC': 'BH', 'BR': 'B100'
        }

theme['curve']={
        'TL': 'BRC', 'TC': 'hline', 'TR': 'BLC',
        'ML': 'vline', 'MC': 'B0', 'MR': 'vline',
        'BL': 'TRC', 'BC': 'hline', 'BR': 'TLC'
        }

class boxDraw:
    def __init__(self, bgColor=24,
                chars="",
                frameColors=[],
                title="", statusBar='',
                mode='auto', charset='utf8',
                style='inside'):
        self.bgColor=bgColor
        if len(chars)!=9:
            cd=grchr['utf8']
            if charset.lower() in ['utf8', 'utf-8']:
                cd=grchr['utf8']
            else:
                cd=grchr['ascii']
            self.chars=f'{cd[theme[style]["TL"]]}{cd[theme[style]["TC"]]}{cd[theme[style]["TR"]]}'\
                        f'{cd[theme[style]["ML"]]}{cd[theme[style]["MC"]]}{cd[theme[style]["MR"]]}'\
                        f'{cd[theme[style]["BL"]]}{cd[theme[style]["BC"]]}{cd[theme[style]["BR"]]}'
        else:
            self.chars=chars
        fr=False
        if len(frameColors)!=9:
            fr=True
        if mode in ['sixel', 'kitty', '24bit', '24-bit', 'auto']:
            if fr:
                self.frameColors=['#FFF', '#AAA','#777','#AAA', 0, '#555', '#777','#555','#333']
            if type(bgColor)==int and bgColor>255:
                self.bgColor=0
            else:
                self.bgColor=bgColor
        elif mode in ['8bit', '8-bit', '256color', '8bitgrey', 'grey', '8bitbright']:
            if fr:
                self.frameColors=[255, 245, 240, 245, 0, 237, 240, 237, 235]
            if type(bgColor)!=int or bgColor>255:
                self.bgColor=0
            else:
                self.bgColor=bgColor
        elif mode in ['4bit', '4-bit', '16color', '4bitgrey']:
            if fr:
                self.frameColors=[15, 7, 8, 7, 0, 8, 7, 8, 0]
            if type(bgColor)!=int or bgColor>15:
                self.bgColor=0
            else:
                self.bgColor=bgColor
        else:
            if fr:
                self.frameColors=[7, 7, 7, 7, 0, 7, 7, 7, 7]
            self.bgColor=0
        self.tinted=None
        self.title=title
        self.statusBar=statusBar

    def setColors(self, bgcolor, frameColors):
        self.bgColor=bgColor
        self.frameColors=frameColors

    def tintFrame(self, color):
        r,g,b=self.getRGB(color)
        r=r/255.0
        g=g/255.0
        b=b/255.0
        self.tinted=[]
        for i in range(0, len(self.frameColors)):
            fr,fg,fb=self.getRGB(self.frameColors[i])
            fr=int(fr/16*r)
            fg=int(fg/16*g)
            fb=int(fb/16*b)
            self.tinted.append(F"#{fr:X}{fg:X}{fb:X}")

    def unTintFrame(self):
        self.tinted=None

    def setCharacters(self):
        self.chars=chars

    def getRGB(self, hex_triplet):
        if type(hex_triplet) != str:
            hex_triplet="#000"
        hex_triplet = hex_triplet.lstrip('#')  # Remove the '#' character if present
        if len(hex_triplet) == 3:
            hex_triplet = ''.join([c * 2 for c in hex_triplet])  # Expand shorthand format
        r = int(hex_triplet[0:2], 16)
        g = int(hex_triplet[2:4], 16)
        b = int(hex_triplet[4:6], 16)
        return r, g, b

    def color(self,fg,bg):
        bgS=""
        fgS=""
        if type(fg)==int:
            fgS=F"38;5;{fg}"
        if type(fg)==str:
            (r,g,b)=self.getRGB(fg)
            fgS=F"38;2;{r};{g};{b}"
        if type(bg)==int:
            bgS=F"48;5;{bg}"
        if type(bg)==str:
            (r,g,b)=self.getRGB(bg)
            bgS=F"48;2;{r};{g};{b}"
        if bgS=="" and fgS!="":
            return F"\x1b[{fgS}m"
        if bgS!="" and fgS!="":
            return F"\x1b[{fgS};{bgS}m"
        if bgS!="" and fgS=="":
            return F"\x1b[{bgS}m"
        return ""

    def move(self,x,y):
        buf=""
        buf+=F"\u001b[{y};{x}H"
        return buf

    def draw(self, x, y, w, h, fill=True):
        if(w<3): w=3
        if(h<3): h=3
        colors=self.frameColors
        if(self.tinted):
            colors=self.tinted
        buff=self.move(x,y)+\
            self.color(colors[0], self.bgColor)+self.chars[0]+\
            self.color(colors[1], self.bgColor)+self.chars[1]*(w-2)+\
            self.color(colors[2], self.bgColor)+self.chars[2]
        for i in range(1,h-1):
            buff+=self.move(x,y+i)+\
                self.color(colors[3], self.bgColor)+self.chars[3]
            if(fill):
                buff+=self.color(colors[4], self.bgColor)+self.chars[4]*(w-2)
            else:
                iw=w-2
                buff+=F"\x1b[{iw}C"
            buff+=self.color(colors[5], self.bgColor)+self.chars[5]
        buff+=self.move(x,y+h-1)+\
            self.color(colors[6], self.bgColor)+self.chars[6]+\
            self.color(colors[7], self.bgColor)+self.chars[7]*(w-2)+\
            self.color(colors[8], self.bgColor)+self.chars[8]+"\x1b[0m"
        if self.title!='':
            desc=self.title
            descX=int(x+(w/2)-(len(desc)/2))+1
            descY=int(y)
            descPos=self.move(descX, descY)
            descColor=self.color(16, colors[1])
            buff+=f'{descPos}{descColor}{desc}\n'
        if self.statusBar!='':
            pass
        return buff

class termKeyboard:
    def __init__(self):
        self.keymap={ "\x1b[A":"Up", "\x1b[B":"Down",\
                 "\x1b[C":"Right", "\x1b[D":"Left",\
                 "\x7f":"Backspace", "\x09":"Tab",\
                 "\x0a":"Enter", "\x1b\x1b":"Esc",\
                 "\x1b[H":"Home", "\x1b[F":"End",\
                 "\x1b[5~":"PgUp", "\x1b[6~":"PgDn",\
                 "\x1b[2~":"Ins", "\x1b[3~":"Del",\
                 "\x1bOP":"F1", "\x1bOQ":"F2",\
                 "\x1bOR":"F3", "\x1bOS":"F4",\
                 "\x1b[15~":"F5", "\x1b[17~": "F6",\
                 "\x1b[18~":"F7", "\x1b[19~": "F8",\
                 "\x1b[20~":"F9", "\x1b[21~": "F10",\
                 "\x1b[23~":"F11", "\x1b[24~": "F12",\
                 "\x1b[32~":"SyRq", "\x1b[34~": "Brk",
                 "\x1b[Z":"Shift Tab"}

    def disable_keyboard_echo(self): # Get the current terminal attributes
        attributes = termios.tcgetattr(sys.stdin)
        # Disable echo flag
        attributes[3] = attributes[3] & ~termios.ECHO
        # Apply the modified attributes
        termios.tcsetattr(sys.stdin, termios.TCSANOW, attributes)

    def enable_keyboard_echo(self): # Get the current terminal attributes
        attributes = termios.tcgetattr(sys.stdin)
        # Enable echo flag
        attributes[3] = attributes[3] | termios.ECHO
        # Apply the modified attributes
        termios.tcsetattr(sys.stdin, termios.TCSANOW, attributes)

    def binread(self):
        return sys.stdin.buffer.read(1)

    def read(self):
        try:
            return sys.stdin.read(1)
        except:
            return sys.stdin.buffer.read(1)
        return ''

    def ord(self, d):
        if(type(d)==int):
            return d
        if(type(d)==str):
            return ord(d[0])
        if(type(d)==bytes):
            return int.from_bytes(d)
        return int(d)

    def read_keyboard_input(self): # Get the current settings of the terminal
        filedescriptors = termios.tcgetattr(sys.stdin)
        # Set the terminal to cooked mode
        tty.setcbreak(sys.stdin)
        char = self.read()
        buffer=char
        # Check if the character is an arrow key or a function key
        if char == "\x1b":
            char = self.read()
            buffer+=char
            if(char=='O'):
                char = self.read()
                buffer+=char
            elif char=='[':
                char = self.read()
                buffer+=char
                if char=='M':
                    b = self.ord(self.read())-32
                    x = self.ord(self.read())-32
                    y = self.ord(self.read())-32
                    #TODO handle mouse code ---
                    buffer+=f'{b};{x};{y}'
                else:
                    while char>='0' and char<='9' or char==';':
                        char = self.read()
                        buffer+=char

        # Restore the original settings of the terminal
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, filedescriptors)
        key=self.keymap.get(str(buffer))
        return key or str(buffer)

class imageSelect:
    def __init__(self, logger=None):
        if logger:
            self.logging=logger
        self.image_support=[]
        self.img_cache={}
        term=os.environ.get('TERM', '')
        konsole_ver=os.environ.get('KONSOLE_VERSION', '')
        if 'kitty' in term:
            self.image_support.append('kitty')
        if 'vt340' in term or len(konsole_ver or '')>0:
            self.image_support.append('sixel')

    def execute_command(self, command, pipe=None):
        """
        Executes a command in the system and logs the command line and output.
        """
        try:
            output=""
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            if pipe:
                process.stdin.write(pipe)
            for line in process.stdout:
                #self.logging.debug(line.rstrip('\n'))
                output+=line
            process.wait()
            process.output=output
            return output
        except Exception as e:
            return f"Error :{' '.join(command)}"

    def clear_images(self):
        out=''
        if 'kitty' in self.image_support:
            out+='\x1b_Ga=d\x1b\\'
        if 'sixel' in self.image_support:
            pass
        return out

    def showImage(self, image, x=0, y=0, w=30, h=15, showInfo=False, mode='auto', charset='utf8'):
        desc=""
        imgX,imgY=0,0
        if(showInfo):
            try:
                img = Image.open(image)
                imgX,imgY=img.size
                img.close()
            except:
                pass
                #self.logging.WARNING(f"can't open {image} as an image.")
            filename=os.path.basename(image)
            desc=f'({imgX}x{imgY}) {filename}'[:w]
            descX=int(x+(w/2)-(len(desc)/2))+1
            descY=int(y+h)-1
            desc=f'\x1b[s\x1b[48;5;245;30m\x1b[{descY};{descX}H{desc}\n'
        start_pos = f'\x1b[{y};{x+1}H'
        if not self.img_cache.get(image):
            ic=ICat(w=int(w), h=int(h), zoom='aspect', f=True, x=int(0), y=int(0), place=True, mode=mode, charset=charset)
            self.img_cache[image]=ic.print(image)
        return f'{start_pos}{self.img_cache[image]}{desc}'

    def convert_to_escape(self, text):
        escape_text = ""
        for char in text:
            if char.isprintable():
                escape_text += char
            else:
                escape_text += "\\x" + hex(ord(char))[2:]
        return escape_text

    def isImage(self, filename):
        return os.path.splitext(filename)[1].lower() in [ '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.xcf' ]

    def isVideo(self, filename):
        return os.path.splitext(filename)[1].lower() in [ '.mp4', '.mkv', '.avi', '.mpg', '.asf' ]

    def setExt(self, filename, ext):
        return f'{os.path.splitext(filename)[0]}{ext}'

    def copy_media(self, source_path, destination_path):
        if self.isVideo(source_path):
            destination_path=self.setExt(destination_path, os.path.splitext(source_path)[1])
            try:
                shutil.copy(source_path, destination_path)
                print(f"Video copied from {source_path} to {destination_path}")
            except Exception as e:
                print(f"Unable to copy video from {source_path} to {destination_path} ({e})")
        if self.isImage(source_path):
            try:
                # Open the source image
                source_image = Image.open(source_path)
                # Save a copy of the source image to the destination path
                source_image.save(destination_path, format='PNG')
                print(f"Image copied from {source_path} to {destination_path}")
            except Exception as e:
                print(f"Unable to copy image from {source_path} to {destination_path} ({e})")
        return destination_path

    def interface(self, target, images, describe, mode='auto', charset='utf8'):
        if len(images)<1:
            return
        cd=grchr['utf8']
        if charset.lower() in [ 'utf8', 'utf-8' ]:
            cd=grchr['utf8']
        else:
            cd=grchr['ascii']
        buffer=""
        kb=termKeyboard()
        # Save the current terminal settings
        stdin_fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(stdin_fd)
        kb.disable_keyboard_echo()
        #start reporting mouse events
        print("\x1b[?1000h\x1b[?25l",end='')
        cols=3
        rows=3
        selected=int((cols*rows)/2)
        page=0
        x0=4
        xsep=2
        y0=2
        ysep=0
        backBox=boxDraw(title=describe, statusBar='',mode=mode, charset=charset, style='outside')
        backBox.tintFrame("#9DF")
        box=boxDraw(mode=mode, charset=charset)
        key=''
        esc='\x1b'
        refresh=True
        count=0
        time0=time.time()
        copied=""
        while True:
            seconds=time.time()-time0
            screenrows, screencolumns = os.popen('stty size', 'r').read().split()
            w=int((int(screencolumns)+1-((x0-1)*2)-((cols-1)*xsep))/cols)
            h=int((int(screenrows)+1-((y0-1)*2)-((rows-1)*ysep))/rows)
            if not self.img_cache.get(images[count%(len(images))]):
                self.showImage(images[count%len(images)], w=w-2, h=h-2, showInfo=True, mode=mode, charset=charset)
            count+=1
            buffer=""
            if refresh:
                print(self.clear_images(), end='')
                buffer+=(backBox.draw(1,1, int(screencolumns), int(screenrows)))
                drawBoxes=True
                fillBoxes=True
            for x in range(0,cols):
                for y in range(0,rows):
                    c=x0+(w*x)+(xsep*x)
                    r=y0+(h*y)+(ysep*y)
                    index=x+(y+page)*cols
                    if index==selected:
                        box.tintFrame("#F00")
                    else:
                        box.unTintFrame()
                    if drawBoxes:
                        buffer+=(box.draw(c,r,w,h,fillBoxes))
                    if index<len(images) and refresh:
                        buffer+=self.showImage(images[index], x=c, y=r+1, w=w-2, h=h-2, showInfo=True, mode=mode, charset=charset)
            refresh=False
            drawBoxes=False
            fillBoxes=False
            pause_terminal_output()
            sys.stdout.write(buffer)
            sys.stdout.flush()
            resume_terminal_output()
            #print(F"{esc}[0,0H{esc}[0m{esc}[Kkey pressed: '{key.replace(esc, '<-')}'")
            key=kb.read_keyboard_input()
            page0=page
            if key=="Up":
                if selected-cols>=0:
                    selected=selected-cols
                    drawBoxes=True
            if key=="Down":
                if selected+cols<(math.ceil(len(images)/cols)*cols):
                    selected=selected+cols
                    drawBoxes=True
            if key=="Left":
                if selected%cols>0:
                    selected=selected-1
                    drawBoxes=True
            if key=="Right":
                if selected%cols<cols-1:
                    selected=selected+1
                    drawBoxes=True
            if key=="Enter":
                if selected<len(images):
                    print(self.clear_images(), end='')
                    show=self.img_cache.get(images[selected])
                    self.img_cache[images[selected]]=False
                    print(self.showImage(images[selected],\
                        w=int(screencolumns),\
                        h=int(screenrows), mode=mode, charset=charset)\
                        +'-'*(int(screencolumns)))
                    self.img_cache[images[selected]]=show
                    print("\x1b[KSelect this media? (y/n)")
                    key=kb.read_keyboard_input()
                    if key=='y' or key=='Y':
                        imagefile=images[selected]
                        print(F"\x1b[Jchose:'{imagefile}'")
                        print("writing target media.")
                        copied= self.copy_media(imagefile, target)
                        break
                    refresh=True
            if key=='q' or key=='Esc' or key=='Q' or key=='Backspace':
                print(self.clear_images(), end='')
                print("\x1b[0m\x1b[0;0H\x1b[2J")
                break
            while(selected<(x+((page-1))*cols)):
                page=page-1
            while(selected>(x+(y+page)*cols)):
                page=page+1
            if(page0!=page):
                refresh=True
        print(F"\x1b[1000l\x1b[?25h")
        kb.enable_keyboard_echo()
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)
        return copied

def main():
    parser.add_option("-b", "--browse", action="store_true", dest="browse",
            default=False, help="Show images in columns")
    parser.add_option('-t', '--target', dest='target', default='selected.png',
            help='the target filename for the image in browse mode.')
    parser.add_option('-d', '--describe', dest='describe', default='',
            help='Text to describe the image in browse mode.')
    parser=OptionParser(usage="usage: %prog [options] filelist")
    parser.add_option('-t', '--target', dest='target', default='selected.png',
            help='the target filename for the image.')
    parser.add_option('-d', '--describe', dest='describe', default='',
            help='Text to describe the image.')
    (options, args)=parser.parse_args()
    if len(args)==0:
        parser.print_help()
    else:
        imgs=imageSelect()
        imgs.interface(options.target, args, options.describe)

if __name__ == "__main__":
    main()

