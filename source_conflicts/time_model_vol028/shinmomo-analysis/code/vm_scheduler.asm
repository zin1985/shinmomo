; Scheduler pseudocode / not direct disassembly

; if object inactive -> return
; if wait/timer field > 0 -> decrement and return
; if state allows script -> run VM step
; else normal object routine
