-- BizHawk/EmuHawk Goal13 smoke probe.
-- ROM path is supplied to EmuHawk, never embedded here. Output is aggregate
-- JSON-lines only; do not use this probe to emit raw memory dumps.
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
  local x = reg("X")
  local slot0799 = x and wram(0x0799 + x) or nil
  local row = {
    kind=kind, frame=emu.framecount(), pc=reg("PC"), a=reg("A"), x=x,
    y=reg("Y"), sp=reg("S"), p=reg("P"),
    w0799x=slot0799, w030b=wram(0x030B), w030d=wram(0x030D),
    w1395=wram(0x1395), w1396=wram(0x1396)
  }
  for k,v in pairs(extra or {}) do row[k]=v end
  local parts={}
  for k,v in pairs(row) do
    parts[#parts+1]=string.format('%q:%s', k,
      v==nil and 'null' or (type(v)=='number' and tostring(v) or string.format('%q',tostring(v))))
  end
  f:write('{'..table.concat(parts,',')..'}\n'); f:flush()
end

local targets={
  {0x89BA36,"BA36"},{0x89BA48,"BA48"},{0x89BA70,"BA70"},
  {0x89BA76,"BA76_read0799x"},{0x89BA81,"BA81_write0799x"},
  {0x89BA89,"BA89_dec0799x"},{0x89BAC8,"BAC8"},{0x89BACD,"BACD_write0799x"}
}
for _,t in ipairs(targets) do
  pcall(event.onmemoryexecute, function()
    local x=reg("X")
    emit("execute", {target=t[2], phase="pre_instruction", slot_addr=x and (0x0799+x) or nil})
  end, t[1], "System Bus", "goal13_"..t[2])
end

-- Do not watch only 7E:0799: the code uses $0799,X. Execute hooks above
-- capture the effective indexed slot address without guessing slot bounds.\n-- Execute callbacks fire at instruction entry, so w0799x is explicitly the\n-- pre-instruction value. For STA sites, A/P in the same row describe the\n-- candidate store value/width; for DEC, compare the next hit/frame evidence.\n-- Do not mislabel these samples as post-write observations.
emit("probe_loaded", {targets="89:BA36,BA48,BA70,BA76,BA81,BA89,BAC8,BACD"})
while true do emu.frameadvance() end
