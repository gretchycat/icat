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

#keymap=[ "\1b[A":"Up", "\e1b[B":"Down" ]

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

    def draw(self, x, y, w, h):
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
                self.color(colors[3], self.bgColor)+self.chars[3]+\
                self.color(colors[4], self.bgColor)+self.chars[4]*(w-2)+\
                self.color(colors[5], self.bgColor)+self.chars[5]
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
        # The character is an escape character, so read another character
        char0 = sys.stdin.read(1)
        buffer+=char0
        char = sys.stdin.read(1)
        buffer+=char
        
        # Check if the next character is an arrow key or a function key
        # Restore the original settings of the terminal
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, filedescriptors)

    return buffer

import select

def is_data_available():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])


def get_input(stdin_fd):
    input_string = ""
    try:
        # Set the terminal to raw mode
        while is_data_available():
            input_string += sys.stdin.read(1)

    finally:
        pass
        # Restore the terminal settings
    return input_string


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
 
        #stdscr=curses.initscr()
        #curses.noecho()
        #curses.raw()
        #stdscr.keypad(True)
        #curses.cbreak()
        backBox=boxDraw( bgColor='#157',\
                chars="\u2588\u2580\u2588\u2588 \u2588\u2588\u2584\u2588")
        backBox.tintFrame("#9DF")
        box=boxDraw()
        buffer+=(backBox.draw(1,1, int(screencolumns), int(screenrows)))
        print(buffer,end='')
        char=''
        refreshImage=True
        oy=1
        while char!='q':
            buffer=""
            for x in range(0,cols):
                for y in range(0,rows):
                    c=x0+(w*x)+(xsep*x)
                    r=y0+(h*y)+(ysep*y)
                    index=x+y*cols
                    if index==selected:
                        box.tintFrame("#F00")
                    else:
                        box.unTintFrame()
                    if refreshImage:
                        buffer+=(box.draw(c,r,w,h))
                    if index<len(args) and refreshImage:
                        buffer+=showImage(args[index], x=c, y=r+1, w=w-2, h=h-2)
            refreshImage=False
            print(buffer,end='')
            print(F"\x1b[0;0H",end='')
            char=read_keyboard_input()
            #char=get_input(stdin_fd)
            print(F"\x1b[{oy};0HReturned Char: \"{convert_to_escape(char)}\"     ")
            oy+=1
        #stdscr.addstr(buffer)
        #stdscr.refresh()
        #curses.getch()
        #curses.echo()
        #stdscr.keypad(False)
        #curses.nocbreak()
        #curses.endwin()
        print(F"\x1b[2J")
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    main()

