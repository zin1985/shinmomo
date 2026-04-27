-- shinmomo_trace_C4_opcode_1B_1E.lua
-- 目的:
--   C4 script VM の opcode 0x1B..0x1E 実script列を取る
--   candidate 0x10..0x13 が $192A/$1958 のどのentityへ解決されるかを取る
--
-- 注意:
--   このファイルは既存trace環境へ差し込む追加パッチ案です。
--   実際のhook登録API名は使用中エミュレータ/BizHawk/Mesen-S環境に合わせて置換してください。
--
-- 必須で欲しい機能:
--   read8(addr), read16(addr), readRangeHex(lo, hi)
--   registerExecHook(snes_pc, callback)
--   logLine(text)

TRACE_C4_CANDIDATE = true

local function h2(v, n)
  n = n or 2
  if v == nil then return string.rep("?", n) end
  return string.format("%0" .. n .. "X", v & ((1 << (4*n)) - 1))
end

local function r8(a)
  if read8 then return read8(a) end
  if getMemory then return getMemory(a, 1) end
  return 0
end

local function r16(a)
  local lo = r8(a)
  local hi = r8(a + 1)
  return lo + hi * 0x100
end

local function rangeHex(lo, hi)
  if readRangeHex then return readRangeHex(lo, hi) end
  local t = {}
  for a = lo, hi do
    t[#t+1] = h2(r8(a), 2)
  end
  return table.concat(t, " ")
end

local function scriptPtr()
  local lo = r8(0x000F)
  local hi = r8(0x0010)
  local bank = r8(0x0011)
  return bank * 0x10000 + hi * 0x100 + lo, bank, hi, lo
end

local function entityFlag180A(entity)
  if entity == nil or entity <= 0 then return nil end
  return r8(0x180A + entity - 1)
end

local function dumpCandidateContext(tag)
  if not TRACE_C4_CANDIDATE then return end

  local sp, bank, hi, lo = scriptPtr()
  local opcode = r8(sp & 0xFFFF) -- 環境によりbanked readへ置換が必要
  local e = r8(0x192A)
  local flag = entityFlag180A(e)

  local line = table.concat({
    "TRACE_C4_CAND",
    "tag=" .. tag,
    "script_ptr=" .. h2(bank,2) .. ":" .. h2(hi*0x100+lo,4),
    "opcode=" .. h2(opcode,2),
    "script_bytes=" .. rangeHex(sp & 0xFFFF, (sp & 0xFFFF) + 0x1F),
    "1923=" .. h2(r8(0x1923),2),
    "1924=" .. h2(r8(0x1924),2),
    "192A=" .. h2(r8(0x192A),2),
    "192B=" .. h2(r8(0x192B),2),
    "1957=" .. h2(r8(0x1957),2),
    "1958=" .. h2(r8(0x1958),2),
    "195E=" .. h2(r8(0x195E),2),
    "195F=" .. h2(r8(0x195F),2),
    "1620=" .. h2(r8(0x1620),2),
    "180A_entity_flag=" .. h2(flag or 0,2),
    "1569=" .. rangeHex(0x1569, 0x1572)
  }, ",")

  if logLine then
    logLine(line)
  else
    print(line)
  end
end

-- hook targets
-- C4:C2D0 dispatcher
-- C4:C85A opcode 18
-- C4:C864 opcode 19
-- C4:C86E opcode 1B
-- C4:C8AA opcode 1C
-- C4:C8F8 opcode 1D
-- C4:C89B opcode 1E
-- C4:C357 success
-- C4:C366 failure

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
  if registerExecHook then
    registerExecHook(h.pc, function() dumpCandidateContext(h.tag) end)
  else
    -- 既存環境のhook登録関数名に置換してください
    -- event.onmemoryexecute(function() dumpCandidateContext(h.tag) end, h.pc, "exec_" .. h.tag)
  end
end

-- 推奨marker
-- marker:c4_candidate_start
-- marker:c4_candidate_after_op1C
-- marker:c4_candidate_after_op18
-- marker:c4_candidate_after_op1B
-- marker:c4_candidate_all_done
