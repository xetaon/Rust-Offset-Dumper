import struct

def rol(x, n):
    n &= 31
    return ((x << n) | (x >> (32 - n))) & 0xffffffff

def u2f(u):
    return struct.unpack('<f', struct.pack('<I', u & 0xffffffff))[0]

def f2u(f):
    return struct.unpack('<I', struct.pack('<f', f))[0]

def decCode(v):
    v = rol(v, 4)
    v = (v + 0x4E30062E) & 0xffffffff
    v = rol(v, 29)
    v = (v ^ 0x74A660FA) & 0xffffffff
    return v

def encCode(v):
    v = (v ^ 0x74A660FA) & 0xffffffff
    v = rol(v, 3)
    v = (v - 0x4E30062E) & 0xffffffff
    v = rol(v, 28)
    return v

def decLog(v):
    v = (v + 0xFE1B32BB) & 0xffffffff
    v = rol(v, 11)
    v = (v + 0xC022822C) & 0xffffffff
    v = rol(v, 26)
    return v

old = 0x35C8301A
enc = 0xB65B85C6

print("old dword 0x%08X" % old)
print("code decrypt ->", u2f(decCode(old)), "hex 0x%08X" % decCode(old))
print("log  decrypt ->", u2f(decLog(old)), "hex 0x%08X" % decLog(old))
print("target bits(109.7122) = 0x%08X" % f2u(109.7122))
print("encCode(target) = 0x%08X" % encCode(f2u(109.7122)))
print("log decrypt(logged enc) =", u2f(decLog(enc)))
print("code decrypt(logged enc) =", u2f(decCode(enc)))
print("f2u(30.0) = 0x%08X" % f2u(30.0))
print("decLog(f2u(30)) =", u2f(decLog(f2u(30.0))))
print("decCode(f2u(30)) =", u2f(decCode(f2u(30.0))))
