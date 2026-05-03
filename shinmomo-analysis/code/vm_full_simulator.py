#!/usr/bin/env python3
from dataclasses import dataclass

@dataclass
class Obj:
    active: bool = True
    state: int = 0
    wait: int = 0
    pc: int = 0

BEHAVIOR = {0x00: "IDLE", 0x07: "EVENT", 0x80: "BRANCH", 0xFF: "BRANCH"}

def step(obj: Obj, script: bytes) -> None:
    if not obj.active:
        return
    if obj.wait > 0:
        obj.wait -= 1
        return
    if obj.pc >= len(script):
        obj.active = False
        return
    op = script[obj.pc]
    obj.pc += 1
    b = BEHAVIOR.get(op, "UNKNOWN")
    if b == "EVENT":
        if obj.pc < len(script):
            obj.state = script[obj.pc]
            obj.pc += 1
        obj.wait = 2
    elif b == "BRANCH":
        if obj.pc < len(script):
            obj.pc = script[obj.pc]
        obj.wait = 1
    else:
        obj.wait = 1

if __name__ == "__main__":
    o = Obj()
    s = bytes([0x07, 0x03, 0x00])
    for i in range(5):
        step(o, s)
        print(i, o)
