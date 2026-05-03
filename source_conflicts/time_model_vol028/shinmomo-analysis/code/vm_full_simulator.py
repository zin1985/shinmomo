#!/usr/bin/env python3
"""
Skeleton simulator for the Shin Momotarou Densetsu object/VM working model.
This is NOT a complete emulator. It is a scaffold for future decoded opcode data.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Callable

@dataclass
class Obj:
    active: bool = True
    state: int = 0
    wait: int = 0
    pc: int = 0
    script: bytes = b""
    slots: Dict[str, int] = field(default_factory=dict)

Command = Callable[[Obj, List[int]], None]

class VM:
    def __init__(self):
        self.commands: Dict[int, Command] = {}

    def register(self, command_id: int, fn: Command) -> None:
        self.commands[command_id] = fn

    def step(self, obj: Obj) -> None:
        if not obj.active:
            return
        if obj.wait > 0:
            obj.wait -= 1
            return
        if obj.pc >= len(obj.script):
            return
        opcode = obj.script[obj.pc]
        obj.pc += 1
        # Placeholder: no real Table A yet.
        command_id = opcode
        command = self.commands.get(command_id)
        if command is None:
            obj.slots['unknown_opcode'] = opcode
            return
        command(obj, [])

if __name__ == "__main__":
    print("VM scaffold only. Populate opcode map before use.")
