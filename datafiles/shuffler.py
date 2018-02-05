import random

def shuffle(f):
    a = open(f,'r')
    lines = a.read().splitlines()
    a.close()
    random.shuffle(lines)
    b = open("output.txt",'w')
    b.write("\n".join(lines))
