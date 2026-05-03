# Two-stage dispatch hypothesis

仮説:
```text
opcode -> Table A -> command_table -> native command
```

現在は実アドレス未確定。
探索対象:
- dense byte array
- jump table
- bank87近傍のindirect jump pattern
