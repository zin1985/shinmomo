-- shinmomo_trace_dialogue_compact_v4_raw_snes9x_20260426.lua
-- Snes9x core fallback: dialogue compact RAW tracer v4
--
-- v4方針:
--   ・日本語への無理な変換をしない
--   ・$1204/$1205 のような毎フレーム系カウンタを見ない
--   ・会話処理でまとまって動く $1260..$12CF だけを見る
--   ・同じ内容は重複出力しない
--   ・1つの会話送りにつき数行程度を目標にする
--
-- 出力:
--   TRACE_DIALOGUE_V4_EVENT
--
-- 見る場所:
--   raw_runs=       非ゼロbyte列
--   words_le=       2byte little-endian風に見た値
--   state=          12AD/12B2/12B4/12B5/12B6 など
--
-- 注意:
--   このLuaは翻訳しません。本文復元用の材料採取に徹します。
--   今回のログでは $718B/$7197 は固定値寄りで本文ではなさそうだったため、監視対象から外しています。

local WATCH_START = 0x1260
local WATCH_LEN   = 0x0070       -- $1260..$12CF
local MIN_LOG_INTERVAL = 10      -- 小さいほど細かいが増える
local PRINT_READY = true

local function choose_domain()
  local domains = memory.getmemorydomainlist()
  local preferred = {"System Bus", "WRAM", "Snes WRAM", "SNES WRAM", "Main RAM"}
  for _, want in ipairs(preferred) do
    for _, got in ipairs(domains) do
      if got == want then return got end
    end
  end
  return domains[1]
end

local DOMAIN = choose_domain()

local function h2(v, n)
  n = n or 2
  if v == nil then return string.rep("?", n) end
  local mod = 1
  for _ = 1, n do mod = mod * 16 end
  return string.format("%0" .. n .. "X", v % mod)
end

local function raw8(addr)
  return memory.read_u8(addr, DOMAIN)
end

local function wram8(addr)
  if DOMAIN == "System Bus" then
    return raw8(0x7E0000 + addr)
  else
    return raw8(addr)
  end
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

local function bytesAt(start, len)
  local t = {}
  for i = 0, len - 1 do
    t[#t + 1] = wram8(start + i)
  end
  return t
end

local function hexBytes(t, maxLen)
  maxLen = maxLen or #t
  local out = {}
  local n = math.min(#t, maxLen)
  for i = 1, n do out[#out + 1] = h2(t[i], 2) end
  return table.concat(out, " ")
end

local function keyBytes(t)
  local out = {}
  for i = 1, #t do out[#out+1] = string.char(t[i]) end
  return table.concat(out)
end

local function stateText()
  return table.concat({
    "12A9=" .. h2(wram8(0x12A9),2),
    "12AD=" .. h2(wram8(0x12AD),2),
    "12B2=" .. h2(wram8(0x12B2),2),
    "12B4=" .. h2(wram8(0x12B4),2),
    "12B5=" .. h2(wram8(0x12B5),2),
    "12B6=" .. h2(wram8(0x12B6),2),
    "12BA=" .. h2(wram8(0x12BA),2),
    "12BB=" .. h2(wram8(0x12BB),2),
    "12BC=" .. h2(wram8(0x12BC),2)
  }, ",")
end

local function diffSpan(prev, cur, base)
  local first, last, count = nil, nil, 0
  for i = 1, #cur do
    if prev[i] ~= cur[i] then
      if first == nil then first = i end
      last = i
      count = count + 1
    end
  end
  if first == nil then return "$0000..$0000", 0 end
  return "$" .. h2(base + first - 1, 4) .. "..$" .. h2(base + last - 1, 4), count
end

local function nonzeroRunsRaw(bytes, base, minLen)
  minLen = minLen or 2
  local out = {}
  local i = 1

  while i <= #bytes do
    while i <= #bytes and bytes[i] == 0 do i = i + 1 end
    local s = i
    while i <= #bytes and bytes[i] ~= 0 do i = i + 1 end
    local e = i - 1

    if e >= s and (e - s + 1) >= minLen then
      local sub = {}
      for j = s, e do sub[#sub+1] = bytes[j] end
      out[#out+1] = string.format("$%04X:[%s]", base + s - 1, hexBytes(sub, 96))
    end
  end

  return table.concat(out, " || ")
end

local function wordsLE(bytes, base)
  -- 2byte little-endian風に見た値。制御/ポインタ/文字候補の目視用。
  local out = {}
  local i = 1
  while i < #bytes do
    local lo = bytes[i]
    local hi = bytes[i+1]
    if lo ~= 0 or hi ~= 0 then
      out[#out+1] = string.format("$%04X=%02X%02X", base + i - 1, hi, lo)
    end
    i = i + 2
  end
  -- 長すぎ防止
  if #out > 40 then
    local short = {}
    for j = 1, 40 do short[j] = out[j] end
    short[#short+1] = "..."
    return table.concat(short, " ")
  end
  return table.concat(out, " ")
end

local function meaningfulKey(bytes)
  -- 同じ内容の再出力を防ぐ。
  -- 全byteそのものをkeyにする。$1204/$1205は対象外なのでカウンタノイズは入らない。
  return keyBytes(bytes)
end

if PRINT_READY then
  logLine("shinmomo dialogue compact raw tracer v4 loaded.")
  logLine("memory domain=" .. tostring(DOMAIN))
  logLine("watch=$" .. h2(WATCH_START,4) .. "..$" .. h2(WATCH_START + WATCH_LEN - 1,4))
  logLine("No JP decode. RAW only. Paste TRACE_DIALOGUE_V4_EVENT lines.")
  logLine("TRACE_DIALOGUE_V4_READY,frame=" .. emu.framecount() .. "," .. stateText())
end

local prev = bytesAt(WATCH_START, WATCH_LEN)
local prevMeaningful = meaningfulKey(prev)
local lastLogFrame = -9999

while true do
  emu.frameadvance()
  local f = emu.framecount()
  local cur = bytesAt(WATCH_START, WATCH_LEN)
  local key = meaningfulKey(cur)

  if key ~= prevMeaningful and (f - lastLogFrame) >= MIN_LOG_INTERVAL then
    local span, count = diffSpan(prev, cur, WATCH_START)
    logLine(table.concat({
      "TRACE_DIALOGUE_V4_EVENT",
      "frame=" .. f,
      stateText(),
      "changed=" .. span,
      "count=" .. tostring(count),
      "raw_runs=" .. nonzeroRunsRaw(cur, WATCH_START, 2),
      "words_le=" .. wordsLE(cur, WATCH_START)
    }, ","))

    prevMeaningful = key
    lastLogFrame = f
  end

  prev = cur
end
