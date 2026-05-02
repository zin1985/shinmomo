# 新桃太郎伝説 vol015: 19D5/19E5/19F5/19C5 staging setter trace

## Conclusion
`token 09` consumes runtime queue pairs generated from `$19D5/$19E5/$19F5/$19C5` by `85:9F4B`. The staging rows are built primarily by two paths:

1. `85:9219..9250` and `85:9286..9250`: type04/base rows with `$19E5=0`.
2. `85:92AF -> 85:93AC`: expanded rows with `$19E5=$198C`, `$19F5` allocated by `85:957F`, and optional `$19C5 bit4` set by `85:9470`.

`85:90A3` is not a setter; it maintains/shifts `$1979/$197D` active-list state.

## Key setters

### 85:9219..9230 + 85:9250
Builds base rows from `$1569,Y`:

```
85:9219 LDA $1569,Y
85:921C BEQ end
85:921E CMP #$1A
85:9220 BCS end
...
85:9230 STA $19D5,X
85:923A JSR $9250
```

`85:9250` initializes:

```
85:9253 STZ $19E5,X
85:9256 LDA #$01
85:9258 STA $19C5,X
...
85:9282 STZ $19C5,X  ; if availability check fails
```

This path produces queue pair `(value=$19D5, type=04)` unless disabled.

### 85:9286..9297 + 85:9250
Copies current `$198E` into a free staging slot:

```
85:9286 JSR $9535
85:928B LDA $198E
85:928E STA $19D5,X
85:9297 JSR $9250
```

Also a type04/base-row path.

### 85:92AF -> 85:93AC
`85:92AF` loops over `$1978/$197C`, sets `$198E/$198C`, then calls `85:93AC` repeatedly.

`85:93AC` is the main expanded-row builder:

```
85:93AE JSR $9535       ; find free row
85:93B6 STX $1986
85:93B9 LDA $198E
85:93BC STA $19D5,X
85:93BF STZ $1B35,X
85:93C2 LDA #$01
85:93C4 STA $19C5,X
85:93C7 JSR $9470
85:93D0 LDA $198C
85:93D3 STA $19E5,X
...
85:93E3 STZ $19F5,X
85:93E6 JSR $957F
85:93EE STA $19F5,X
```

This path generally produces `(value=$19D5, type=06)` followed by `(value=$19F5, type=0F)`.

### 85:9470 transform
If `$19D5,X` is `0x48` or `0x49`, it is randomized/remapped and `$19C5` bit `0x10` is set:

```
85:9476 LDA $19D5,X
85:9479 CMP #$48
85:947D CMP #$4A
...
85:9491 LDA $94A6,Y
85:9494 STA $19D5,X
85:9497 LDA $19C5,X
85:949A ORA #$10
85:949C STA $19C5,X
```

At queue build time, `85:9F4B` treats this bit as a forced pair0 value of `0x48`.

### 85:957F allocator
Allocates the value later stored to `$19F5,X`, using `$1D46/$1D4E` and scanning existing rows to avoid duplicate phase values for the same `$198E`.

### 85:9F4B queue builder
Consumes the row selected by `$1986`:

```
Y = $1986
$1297[X] = $19D5[Y]
if $19E5[Y] == 0:
    $129F[X] = 04
else:
    $129F[X] = 06
    if ($19C5[Y] & 0x10): $1297[X] = 48
    if $1297[X] < DB:
        $1297[X+1] = $19F5[Y]
        $129F[X+1] = 0F
terminator = (0,0)
```

## Updated progress
- Goal 7: 95% -> 96%
- Goal 9: 77% -> 79%
- Goal 10: 96% unchanged

## Next step
Trace which path is active immediately before each weapon descriptor token09 call by watching `$1986` and row contents. The most useful breakpoints are:

- write breakpoints: `$19D5/$19E5/$19F5/$19C5`
- queue build: `85:9F4B`
- token09 pop: `84:9F24 -> 84:9EC7`
