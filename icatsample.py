#!/usr/bin/python3
from icat import ICat 

def main():
    width=60
    height=30
    x=10
    y=5
    imagefile='sampleimage.jpg'
    ic=ICat(mode='utf8', w=width, h=height, f=True, zoom='aspect', x=x, y=y,)
    ic.print(imagefile)

if __name__ == "__main__":
    main()

