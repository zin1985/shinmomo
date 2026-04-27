-- shinmomo_trace_C4_opcode_1B_1E_bizhawk.lua
-- BizHawk / EmuHawk 想定版
-- 目的:
--   C4 script VM の opcode 0x1B..0x1E 実行時に、
--   candidate 0x10..0x13 がどのentityへ解決されるかをログ出力する。
--
-- 使い方:
--   1. BizHawkで Shin Momotarou Densetsu (J).smc を起動
--   2. Tools -> Lua Console
--   3. Open Script でこのLuaを開く
--   4. 怨みの洞窟/候補NPC/イベント候補が出る場面を操作
--   5. Lua Console または client.log 出力を確認
--
-- 注意:
--   BizHawkのメモリドメイン名は環境により違うことがあります。
--   Lua Consoleで memory.getmemorydomainlist() を実行して、
--   "System Bus" が存在しない場合は、SYS_DOMAINを書き換えてください。

local SYS_DOMAIN = "System Bus"

local function h2(v, n)
  n = n or 2
  if v == nil then return string.rep("?", n) end
  local mask = (n == 2) and 0xFF or ((n == 4) and 0xFFFF or 0xFFFFFF)
  return string.format("%0" .. n .. "X", v & mask)
end

local function bus8(addr)
  return memory.read_u8(addr, SYS_DOMAIN)
end

local function wram8(addr)
  return memory.read_u8(0x7E0000 + addr, SYS_DOMAIN)
end

local function wram16(addr)
  local lo = wram8(addr)
  local hi = wram8(addr + 1)
  return lo + hi * 0x100
end

local function rangeHexBus(addr, len)
  local t = {}
  for i = 0, len - 1 do
    t[#t + 1] = h2(bus8(addr + i), 2)
  end
  return table.concat(t, " ")
end

local function rangeHexWram(addr, len)
  local t = {}
  for i = 0, len - 1 do
    t[#t + 1] = h2(wram8(addr + i), 2)
  end
  return table.concat(t, " ")
end

local function scriptPtrBus()
  local lo = wram8(0x000F)
  local hi = wram8(0x0010)
  local bank = wram8(0x0011)
  return bank * 0x10000 + hi * 0x100 + lo, bank, hi * 0x100 + lo
end

local function entityFlag180A(entity)
  if entity == nil or entity <= 0 then return nil end
  return wram8(0x180A + entity - 1)
end

local function logLine(s)
  if console and console.log then
    console.log(s)
  elseif client and client.log then
    client.log(s)
  else
    print(s)
  end
end

local function dumpCandidateContext(tag)
  local sp, bank, ofs = scriptPtrBus()
  local opcode = 0
  local ok, val = pcall(function() return bus8(sp) end)
  if ok then opcode = val end

  local entity = wram8(0x192A)
  local flag = entityFlag180A(entity) or 0

  local parts = {
    "TRACE_C4_CAND",
    "frame=" .. emu.framecount(),
    "tag=" .. tag,
    "script_ptr=" .. h2(bank,2) .. ":" .. h2(ofs,4),
    "opcode=" .. h2(opcode,2),
    "script_bytes=" .. rangeHexBus(sp, 16),
    "1923=" .. h2(wram8(0x1923),2),
    "1924=" .. h2(wram8(0x1924),2),
    "192A=" .. h2(wram8(0x192A),2),
    "192B=" .. h2(wram8(0x192B),2),
    "1957=" .. h2(wram8(0x1957),2),
    "1958=" .. h2(wram8(0x1958),2),
    "195E=" .. h2(wram8(0x195E),2),
    "195F=" .. h2(wram8(0x195F),2),
    "1620=" .. h2(wram8(0x1620),2),
    "180A_entity_flag=" .. h2(flag,2),
    "1569=" .. rangeHexWram(0x1569, 10)
  }

  logLine(table.concat(parts, ","))
end

-- hook targets
local hooks = {
  { pc = 0xC4C2D0, tag = "dispatcher_C4_C2D0" },
  { pc = 0xC4C85A, tag = "op18_spawn_1958_pre" },
  { pc = 0xC4C864, tag = "op19_remove_1958_pre" },
  { pc = 0xC4C86E, tag = "op1B_mark_consumed_pre" },
  { pc = 0xC4C8AA, tag = "op1C_find_next_pre" },
  { pc = 0xC4C8F8, tag = "op1D_unconsumed_pre" },
  { pc = 0xC4C89B, tag = "op1E_all_done_pre" },
  { pc = 0xC4C357, tag = "success_C4_C357" },
  { pc = 0xC4C366, tag = "failure_C4_C366" },
}

for _, h in ipairs(hooks) do
  event.onmemoryexecute(function()
    dumpCandidateContext(h.tag)
  end, h.pc, "exec_" .. h.tag)
end

logLine("shinmomo C4 opcode 1B-1E tracer loaded.")
logLine("If no logs appear, check memory domain name and hook PC mapping.")

while true do
  emu.frameadvance()
end
