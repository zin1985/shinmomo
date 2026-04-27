-- shinmomo_trace_text_polling_snes9x_20260426.lua
-- Snes9x core fallback版: 会話/表示テキスト材料ログ用
--
-- 目的:
--   execute hookが使えないSnes9x coreでも、
--   会話・店・UI表示中に変化するWRAMの「表示コード/抽象トークン列」をログに残す。
--
-- 重要:
--   このLuaは「日本語本文そのもの」を即デコードするものではありません。
--   新桃は独自文字コードなので、まず raw hex token / staging buffer を採取し、
--   後で文字表・既知台詞と照合して復元します。
--
-- 主な監視対象:
--   $7180..$72FF : 表示コード staging / operand stack 候補。既知メモでは $718B.. が重要。
--   $1900..$197F : script/event/text work 候補。$1923/$1924/$192A 等も含む。
--   $1F90..$1FFF : 店/施設/UI phase work 候補。$1F9D/$1FAA 等も含む。
--   $7A00..$7BFF : 予備の表示/queue候補。ノイズが多い場合は WATCH_7A00=false にする。
--
-- 使い方:
--   1. BizHawk Lua ConsoleでこのLuaをOpen Script
--   2. 会話直前にログをクリア
--   3. NPCに話しかける / 店会話を出す / メッセージ送りをする
--   4. TRACE_TEXT_CHANGE / TRACE_TEXT_SNAPSHOT 行を保存して貼る
--
-- ログが多い場合:
--   DUMP_INTERVALを大きくする
--   WATCH_7A00=falseにする
--   MIN_CHANGE_INTERVALを大きくする

local DUMP_INTERVAL = 30          -- 定期snapshot間隔。0なら定期出力なし
local MIN_CHANGE_INTERVAL = 3     -- 変化ログの最短間隔
local WATCH_7A00 = false          -- 予備範囲。まずfalse推奨

local WATCHES = {
  { name = "display_7180", start = 0x7180, len = 0x0180, row = 32 },
  { name = "script_1900",  start = 0x1900, len = 0x0080, row = 32 },
  { name = "ui_1F90",      start = 0x1F90, len = 0x0070, row = 32 },
}

if WATCH_7A00 then
  WATCHES[#WATCHES + 1] = { name = "maybe_queue_7A00", start = 0x7A00, len = 0x0200, row = 32 }
end

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

local function rangeBytes(start, len)
  local t = {}
  for i = 0, len - 1 do
    t[#t + 1] = wram8(start + i)
  end
  return t
end

local function bytesKey(t)
  local out = {}
  for i = 1, #t do out[#out + 1] = string.char(t[i]) end
  return table.concat(out)
end

local function bytesHex(t, maxLen)
  maxLen = maxLen or #t
  local out = {}
  local n = math.min(#t, maxLen)
  for i = 1, n do out[#out + 1] = h2(t[i], 2) end
  return table.concat(out, " ")
end

local function nonzeroRuns(bytes, base, minLen)
  minLen = minLen or 4
  local runs = {}
  local i = 1
  while i <= #bytes do
    while i <= #bytes and bytes[i] == 0 do i = i + 1 end
    local s = i
    while i <= #bytes and bytes[i] ~= 0 do i = i + 1 end
    local e = i - 1
    if e >= s and (e - s + 1) >= minLen then
      local sub = {}
      for j = s, e do sub[#sub + 1] = bytes[j] end
      runs[#runs + 1] = string.format("$%04X:%s", base + s - 1, bytesHex(sub, 64))
    end
  end
  return table.concat(runs, " || ")
end

local function diffSummary(prev, cur, base)
  local first, last, count = nil, nil, 0
  for i = 1, #cur do
    if prev[i] ~= cur[i] then
      if first == nil then first = i end
      last = i
      count = count + 1
    end
  end
  if first == nil then
    return nil
  end

  local s = math.max(1, first - 8)
  local e = math.min(#cur, last + 8)
  local sub = {}
  for i = s, e do sub[#sub + 1] = cur[i] end

  return {
    first = base + first - 1,
    last = base + last - 1,
    count = count,
    hex = bytesHex(sub, 96),
  }
end

local function contextFields()
  local fields = {
    "1923=" .. h2(wram8(0x1923),2),
    "1924=" .. h2(wram8(0x1924),2),
    "192A=" .. h2(wram8(0x192A),2),
    "1957=" .. h2(wram8(0x1957),2),
    "1958=" .. h2(wram8(0x1958),2),
    "195E=" .. h2(wram8(0x195E),2),
    "1F9D=" .. h2(wram8(0x1F9D),2),
    "1F9E=" .. h2(wram8(0x1F9E),2),
    "1FAA=" .. h2(wram8(0x1FAA),2),
    "718B=" .. h2(wram8(0x718B),2),
    "718C=" .. h2(wram8(0x718C),2),
    "718D=" .. h2(wram8(0x718D),2),
  }
  return table.concat(fields, ",")
end

local function snapshotAll()
  local snap = {}
  for _, w in ipairs(WATCHES) do
    snap[w.name] = rangeBytes(w.start, w.len)
  end
  return snap
end

local function dumpSnapshot(tag, snap)
  logLine(table.concat({
    "TRACE_TEXT_SNAPSHOT",
    "frame=" .. emu.framecount(),
    "tag=" .. tag,
    "domain=" .. tostring(DOMAIN),
    contextFields()
  }, ","))

  for _, w in ipairs(WATCHES) do
    local b = snap[w.name]
    logLine(table.concat({
      "TRACE_TEXT_RANGE",
      "frame=" .. emu.framecount(),
      "name=" .. w.name,
      "base=$" .. h2(w.start,4),
      "len=$" .. h2(w.len,4),
      "head=" .. bytesHex(b, 96),
      "runs=" .. nonzeroRuns(b, w.start, 4)
    }, ","))
  end
end

local function dumpChange(w, diff, cur)
  logLine(table.concat({
    "TRACE_TEXT_CHANGE",
    "frame=" .. emu.framecount(),
    "name=" .. w.name,
    "changed=$" .. h2(diff.first,4) .. "..$" .. h2(diff.last,4),
    "count=" .. tostring(diff.count),
    contextFields(),
    "around=" .. diff.hex,
    "runs=" .. nonzeroRuns(cur, w.start, 4)
  }, ","))
end

logLine("shinmomo text/staging polling tracer loaded.")
logLine("memory domain=" .. tostring(DOMAIN))
logLine("This logs raw text/display tokens, not decoded Japanese.")
logLine("Known focus: $718B.. display staging / operand stack candidate.")

local prev = snapshotAll()
local lastChangeFrame = -9999
dumpSnapshot("initial", prev)

while true do
  emu.frameadvance()
  local f = emu.framecount()
  local cur = snapshotAll()

  local any = false
  if f - lastChangeFrame >= MIN_CHANGE_INTERVAL then
    for _, w in ipairs(WATCHES) do
      local d = diffSummary(prev[w.name], cur[w.name], w.start)
      if d ~= nil then
        dumpChange(w, d, cur[w.name])
        any = true
      end
    end
    if any then
      lastChangeFrame = f
    end
  end

  if DUMP_INTERVAL > 0 and f % DUMP_INTERVAL == 0 then
    dumpSnapshot("periodic", cur)
  end

  prev = cur
end
