-- BizHawk/EmuHawk Goal13 smoke probe.
-- ROM path is supplied to EmuHawk, never embedded here. Output is an aggregate
-- JSON-lines file; do not use this probe to emit raw memory dumps.
local OUT = os.getenv("SHINMOMO_TRACE_OUT") or "goal13_trace.jsonl"
local f = assert(io.open(OUT, "w"))
local function reg(name)
  if emu and emu.getregister then
    local ok, v = pcall(emu.getregister, name)
    if ok then return v end
  end
  return nil
end
local function wram(addr)
  local ok, v = pcall(memory.read_u8, 0x7E0000 + addr, "System Bus")
  if ok then return v end
  return nil
end
local function emit(kind, extra)
  local row = {kind=kind, frame=emu.framecount(), pc=reg("PC"), a=reg("A"), x=reg("X"), y=reg("Y"), sp=reg("S"), p=reg("P"), w0799=wram(0x0799), w030b=wram(0x030B), w030d=wram(0x030D), w1395=wram(0x1395), w1396=wram(0x1396)}
  for k,v in pairs(extra or {}) do row[k]=v end
  local parts={}
  for k,v in pairs(row) do parts[#parts+1]=string.format('%q:%s',k,v==nil and 'null' or (type(v)=='number' and tostring(v) or string.format('%q',tostring(v)))) end
  f:write('{'..table.concat(parts,',')..'}\n'); f:flush()
end
local targets={{0x89BA36,"BA36"},{0x89BA48,"BA48"},{0x89BA70,"BA70"},{0x89BAC8,"BAC8"}}
for _,t in ipairs(targets) do
  pcall(event.onmemoryexecute, function() emit("execute", {target=t[2]}) end, t[1], "System Bus", "goal13_"..t[2])
end
pcall(event.onmemorywrite, function(_,addr,val) emit("0799_write", {addr=addr, value=val, bit7=((val or 0) & 0x80) ~= 0}) end, 0x7E0799, "System Bus", "goal13_0799")
if event.onframestart then event.onframestart(function() if emu.framecount() % 60 == 0 then emit("frame", {}) end end, "goal13_frame") end
emit("probe_loaded", {targets="89:BA36,89:BA48,89:BA70,89:BAC8"})
while true do emu.frameadvance() end
