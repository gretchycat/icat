#!/usr/bin/python3
import os,sys,termios,tty
from optparse import OptionParser
from icat import ICat 

parser=OptionParser(usage="usage: %prog [options] filelist")
parser.add_option("-m", "--mode", dest="mode", default="24bit", 
        help="Color mode: 24bit | 8bit | 8bitbright | 8bitgrey | 4bit | 4bitgrey | 3bit | bw")
parser.add_option("-f", "--fullblock", action="store_false", dest="full", default=True,
        help="Only use full blocks")
parser.add_option("-c", "--charset", dest="charset", default="utf8",
        help="Character set: utf8 | ascii")
(options, args)=parser.parse_args()

screenrows, screencolumns = os.popen('stty size', 'r').read().split()

keymap={ "\x1b[A":"Up", "\x1b[B":"Down",\
         "\x1b[C":"Right", "\x1b[D":"Left",\
         "\x7f":"Backspace", "\x09":"Tab",\
         "\x0a":"Enter", "\x1b":"Esc",\
         "\x1b[H":"Home", "\x1b[F":"End",\
         "\x1b[5~":"PgUp", "\x1b[6~":"PgDn",\
         "\x1b[2~":"Ins", "\x1b[3~":"Del",\
         "\x1bOP":"F1", "\x1bOQ":"F2",\
         "\x1bOR":"F3", "\x1bOS": "F4",\
         "\x1b[15~":"F5", "\x1b[17~": "F6",\
         "\x1b[18~":"F7", "\x1b[19~": "F8",\
         "\x1b[20~":"F9", "\x1b[21~": "F10",\
         "\x1b[23~":"F11", "\x1b[24~": "F12",\
         "\x1b[32~":"SyRq", "\x1b[34~": "Brk" }

class boxDraw:
    def __init__(self, bgColor='#157', \
                chars="\u2584\u2584\u2584\u2588\u2593\u2588\u2580\u2580\u2580",\
                frameColors=['#FFF', '#AAA','#777','#AAA', 0, '#555', '#777','#555','#333']):
        self.bgColor=bgColor
        self.chars=chars
        self.frameColors=frameColors
        self.tinted=None

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
            bgS=F"48;5;{fg}"    
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
            self.color(colors[8], self.bgColor)+self.chars[8]
        return buff

def showImage(image, x=0, y=0, f=True, w=30, h=15):
    ic=ICat(mode=options.mode.lower(), w=int(w), h=int(h), 
            zoom='aspect', f=options.full, charset=options.charset.lower(),
            x=int(x), y=int(y)) 
    return ic.print(image)

def convert_to_escape(text):
    escape_text = ""
    for char in text:
        if char.isprintable():
            escape_text += char
        else:
            escape_text += "\\x" + hex(ord(char))[2:]
    return escape_text

def read_keyboard_input():
    # Get the current settings of the terminal
    filedescriptors = termios.tcgetattr(sys.stdin)

    # Set the terminal to cooked mode
    tty.setcbreak(sys.stdin)

    # Read a character from the terminal
    char = sys.stdin.read(1)
    buffer=char
    # Check if the character is an arrow key or a function key
    if char == "\x1b":
        char = sys.stdin.read(1)
        buffer+=char
        if(char=='O'):
            char = sys.stdin.read(1)
            buffer+=char
        elif char=='[':
            char = sys.stdin.read(1)
            buffer+=char
            while char>='0' and char<='9' or char==';':
                char = sys.stdin.read(1)
                buffer+=char
    # Restore the original settings of the terminal
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, filedescriptors)

    key=keymap.get(buffer)
    return key or buffer


def main():
    buffer=""
    if len(args)==0:
        parser.print_help()
    else:
        # Save the current terminal settings
        stdin_fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(stdin_fd)
#        tty.setraw(stdin_fd) 

        cols=3
        rows=3
        selected=int((cols*rows)/2)
        page=0
        x0=4
        xsep=2
        y0=2
        ysep=0
        w=int((int(screencolumns)+1-((x0-1)*2)-((cols-1)*xsep))/cols)
        h=int((int(screenrows)+1-((y0-1)*2)-((rows-1)*ysep))/rows)
 
        backBox=boxDraw( bgColor='#157',\
                chars="\u2588\u2580\u2588\u2588 \u2588\u2588\u2584\u2588")
        backBox.tintFrame("#9DF")
        box=boxDraw()
        key=''
        refresh=True
        while key!='q' and key!='Esc':
            buffer=""
            if refresh:
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
                    if index<len(args) and refresh:
                        buffer+=showImage(args[index], x=c, y=r+1, w=w-2, h=h-2)
            refresh=False
            drawBoxes=False
            fillBoxes=False
            print(buffer,end='')
            print(F"\x1b[0;0H",end='')
            key=read_keyboard_input()

            page0=page
            if key=="Up":
                if selected-cols>=0:
                    selected=selected-cols
                    drawBoxes=True
            if key=="Down":
                if selected+cols<len(args):
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
                if selected<len(args):
                    print(showImage(args[selected], w=int(screencolumns), h=int(screenrows))+'-'*(int(screencolumns)))
                    print("\x1b[KSelect this image? (y/n)")
                    key=read_keyboard_input()
                    if key=='y' or key=='Y':
                        imagefile=args[selected]
                        print(F"\x1b[Kchose:'{imagefile}'")
                        return
                    refresh=True
            while(selected<(x+((page-1))*cols)):
                page=page-1
            while(selected>(x+(y+page)*cols)):
                page=page+1
            if(page0!=page):
                refresh=True
 
        print(F"\x1b[2J")
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    main()

