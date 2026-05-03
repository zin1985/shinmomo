; VM dispatch skeleton / not confirmed code
; Purpose: document the expected lookup shape to hunt in disassembly.

; expected pattern candidate:
;   fetch opcode/script byte
;   optional TableA lookup
;   index command table
;   indirect jump/call

; Search patterns:
;   ASL A / TAX / LDA table,X
;   LDA table,X / STA zp / JMP (zp)
;   JSR common_epilogue after slot writes
