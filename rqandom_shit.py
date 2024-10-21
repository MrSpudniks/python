import math as meth



def keep(string, keep):
    out = ""
    for i in string:
        if i in keep:
            out += i
    return out



def makeLetterFuckOff(letter):
    return float(keep(str(letter), ["1","2","3","4","5","6","7","8","9","0","."]))



print("why tf you run this dumb ass")