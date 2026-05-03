; bank87 key snippets for vol017 diff
; These are byte/context notes, not full disassembly.

; $87:82C0 candidate reader
; file PC 0x0382C0
; BD 59 07      LDA $0759,X
; 85 2A         STA $2A
; BD 99 07      LDA $0799,X
; 85 2B         STA $2B
; ... later candidate: B1 2A = LDA ($2A),Y

; $87:810D init path
; A9 E0         LDA #$E0
; 9D 59 07      STA $0759,X
; A9 87         LDA #$87
; 9D 99 07      STA $0799,X

; $87:8173 init path
; A9 E0         LDA #$E0
; 9D 59 07      STA $0759,X
; A9 89         LDA #$89
; 9D 99 07      STA $0799,X

; $87:8459 toggle path
; BD 59 07      LDA $0759,X
; 1A            INC A
; 29 01         AND #$01
; 9D 59 07      STA $0759,X

; $87:E579 position-like update
; BD 19 07      LDA $0719,X
; 7D 99 07      ADC $0799,X
; 9D 19 07      STA $0719,X
; BD 59 07      LDA $0759,X
; 7D D9 07      ADC $07D9,X
; 9D 59 07      STA $0759,X
