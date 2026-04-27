-- shinmomo_trace_dialogue_source_reader_context_lexicon_v20_compact_snes9x_20260427.lua
-- v20: v19のログ過多・WRAM範囲外read警告を抑えた版
--
-- 改善点:
--   1) $B1/$B2/$B3 が ROM bank(C0-FF等)を指す場合、WRAM domainで読まない
--   2) ROM domain / System Bus が無い場合は読まずに SKIP を1回だけ出す
--   3) active text phase中心に限定
--   4) all-zero raw は捨てる
--   5) pointer/rawが変わった時だけ出す
--
-- 出力:
--   TRACE_DIALOGUE_V20_SOURCE
--   TRACE_DIALOGUE_V20_SKIP
--   TRACE_DIALOGUE_V20_READY

local READ_LEN = 16
local MIN_LOG_FRAME_GAP = 4
local ACTIVE_ONLY = true
local LOG_ONLY_HITS = false  -- trueにすると static_hits/context_candidates がある時だけ出す

local function list_domains()
  local ok, domains = pcall(function() return memory.getmemorydomainlist() end)
  if ok and domains then return domains end
  return {}
end

local function join_domains(domains)
  local t = {}
  for _, d in ipairs(domains) do t[#t+1] = tostring(d) end
  return table.concat(t, "|")
end

local DOMAINS = list_domains()

local function choose_domain(preferred)
  for _, want in ipairs(preferred) do
    for _, got in ipairs(DOMAINS) do
      if got == want then return got end
    end
  end
  -- loose contains
  for _, want in ipairs(preferred) do
    local wl = string.lower(want)
    for _, got in ipairs(DOMAINS) do
      local gl = string.lower(got)
      if string.find(gl, wl, 1, true) then return got end
    end
  end
  return nil
end

local WRAM_DOMAIN = choose_domain({"WRAM", "Snes WRAM", "SNES WRAM", "Main RAM"}) or DOMAINS[1]
local SYS_DOMAIN  = choose_domain({"System Bus"})
local ROM_DOMAIN  = choose_domain({"CARTROM", "Cart ROM", "Cartridge ROM", "ROM", "Snes ROM", "SNES ROM"})

local function domain_size(domain)
  if domain == nil then return 0 end
  local ok, sz = pcall(function() return memory.getmemorydomainsize(domain) end)
  if ok and sz then return sz end
  -- fallback estimates
  if domain == WRAM_DOMAIN then return 0x20000 end
  if domain == SYS_DOMAIN then return 0x1000000 end
  if domain == ROM_DOMAIN then return 0x800000 end
  return 0
end

local WRAM_SIZE = domain_size(WRAM_DOMAIN)
local SYS_SIZE  = domain_size(SYS_DOMAIN)
local ROM_SIZE  = domain_size(ROM_DOMAIN)

local function safe_read_u8(addr, domain)
  if domain == nil then return nil end
  local sz = domain_size(domain)
  if sz > 0 and (addr < 0 or addr >= sz) then return nil end
  local ok, v = pcall(function() return memory.read_u8(addr, domain) end)
  if ok then return v end
  return nil
end

local function wram8(addr)
  if WRAM_DOMAIN == nil then return 0 end
  -- WRAM domainは通常0始まり。System BusではなくWRAMを選んでいるので、そのまま読む。
  local v = safe_read_u8(addr, WRAM_DOMAIN)
  return v or 0
end

local function h2(v)
  if v == nil then return "??" end
  return string.format("%02X", v % 0x100)
end

local function h4(v)
  if v == nil then return "????" end
  return string.format("%04X", v % 0x10000)
end

local function h6(v)
  if v == nil then return "??????" end
  return string.format("%06X", v % 0x1000000)
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

-- ===== minimal dictionary =====
local SINGLE = {
  ["5C"]="!", ["7E"]="」", ["80"]="ー",
  ["92"]="う", ["93"]="え", ["94"]="お", ["95"]="か", ["96"]="き", ["97"]="く",
  ["99"]="こ", ["9A"]="さ", ["9B"]="し", ["9C"]="す", ["9D"]="せ", ["9E"]="そ", ["9F"]="た",
  ["A0"]="ち", ["A1"]="つ", ["A2"]="て", ["A3"]="と", ["A4"]="な", ["A5"]="に",
  ["A8"]="の", ["A9"]="は", ["AE"]="ま", ["B0"]="む", ["B2"]="も",
  ["B5"]="よ", ["B6"]="ら", ["B7"]="り", ["B8"]="る", ["B9"]="れ", ["BA"]="ろ",
  ["BC"]="を", ["BD"]="ん", ["BE"]="で", ["DF"]="び", ["F6"]="ゃ"
}

local DICT02 = {
  ["84"]="行く",
  ["9B"]="旅の人",
  ["A0"]="桃太郎",
  ["AC"]="オニ",
  ["B0"]="きんたん",
  ["B9"]="ゆうき",
  ["C0"]="おにぎり",
  ["CD"]="ちから",
  ["CE"]="あしゅら",
  ["D7"]="入れ"
}

local KANJI = {
  ["1800"]="桃", ["1801"]="太", ["1802"]="郎",
  ["1803"]="金", ["1804"]="浦", ["1805"]="島",
  ["1808"]="夜", ["1809"]="叉", ["180A"]="姫",
  ["1811"]="西", ["1813"]="北", ["1815"]="体",
  ["181F"]="装", ["1820"]="備",
  ["1847"]="人", ["184C"]="刀", ["1850"]="銀", ["1851"]="次",
  ["188F"]="火", ["18DB"]="鬼", ["18F2"]="無",
  ["199B"]="旅", ["19BF"]="行", ["19D7"]="入", ["19EB"]="穴",
  ["1A1A"]="言", ["1A31"]="理"
}

local STATIC_SEQS = {
  {name="桃太郎", bytes={0x02,0xA0}},
  {name="銀次", bytes={0x18,0x50,0x18,0x51}},
  {name="銀次の", bytes={0x18,0x50,0x18,0x51,0xA8}},
  {name="銀次は", bytes={0x18,0x50,0x18,0x51,0xA9}},
  {name="刀", bytes={0x18,0x4C}},
  {name="装備", bytes={0x18,0x1F,0x18,0x20}},
  {name="そうび", bytes={0x9E,0x92,0xDF}},
  {name="できるよ", bytes={0xBE,0x96,0xB8,0xB5}},
  {name="たき火", bytes={0x9F,0x96,0x18,0x8F}},
  {name="おむすびころりん", bytes={0x94,0xB0,0x9C,0xDF,0x99,0xBA,0xB7,0xBD}},
  {name="鬼たいじ", bytes={0x18,0xDB,0x9F,0x91,0xD6}},
  {name="行くのか", bytes={0x19,0xBF,0x97,0xA8,0x95}},
  {name="無理", bytes={0x18,0xF2,0x1A,0x31}},
  {name="旅の人", bytes={0x02,0x9B}},
  {name="入れ", bytes={0x02,0xD7}},
  {name="穴", bytes={0x19,0xEB}},
  {name="鬼", bytes={0x18,0xDB}},
  {name="火", bytes={0x18,0x8F}},
  {name="体", bytes={0x18,0x15}},
  {name="言", bytes={0x1A,0x1A}}
}

local function bytes_match_at(src, pos, pat)
  if pos + #pat - 1 > #src then return false end
  for i = 1, #pat do
    if src[pos+i-1] ~= pat[i] then return false end
  end
  return true
end

local function scan_static(src)
  local hits = {}
  local seen = {}
  for pos = 1, #src do
    for _, rule in ipairs(STATIC_SEQS) do
      if bytes_match_at(src, pos, rule.bytes) then
        local k = rule.name .. "@" .. tostring(pos)
        if not seen[k] then
          seen[k] = true
          hits[#hits+1] = k
        end
      end
    end
  end
  return table.concat(hits, " | ")
end

local function contains(s, needle)
  return string.find(s or "", needle, 1, true) ~= nil
end

local function context_candidates(src, dec)
  local hits = scan_static(src)
  local out = {}
  if contains(hits, "銀次の") and (contains(hits, "そうび") or contains(dec, "そうび")) then out[#out+1] = "銀次のそうび" end
  if contains(hits, "銀次は") and contains(hits, "刀") then out[#out+1] = "銀次は刀" end
  if contains(hits, "桃太郎") and contains(dec, "さん") then out[#out+1] = "桃太郎さん" end
  if contains(hits, "入れ") and contains(dec, "ません") then out[#out+1] = "入れません" end
  if contains(hits, "鬼たいじ") then out[#out+1] = "鬼たいじ" end
  if contains(hits, "無理") then out[#out+1] = "無理" end
  if contains(hits, "行くのか") then out[#out+1] = "行くのか" end
  return table.concat(out, " | ")
end

local function src_ptr()
  local lo = wram8(0x00B1)
  local hi = wram8(0x00B2)
  local bank = wram8(0x00B3)
  return bank, lo + hi * 0x100
end

local function hirom_offset(bank, addr)
  -- 新桃は解析上 HiROM型: C1:9AF1 -> file offset 0x019AF1
  local b = bank
  if b >= 0xC0 then b = b - 0xC0
  elseif b >= 0x80 then b = b - 0x80
  end
  return b * 0x10000 + addr
end

local function read_source_bytes(bank, addr, n)
  local bytes = {}

  -- 1) System Bus があるならCPU addressで読む
  if SYS_DOMAIN ~= nil and SYS_SIZE >= 0x1000000 then
    local base = bank * 0x10000 + addr
    for i = 0, n-1 do
      local v = safe_read_u8(base + i, SYS_DOMAIN)
      if v == nil then return nil, "sysbus_oob" end
      bytes[#bytes+1] = v
    end
    return bytes, "system_bus"
  end

  -- 2) ROM domainがあるならHiROM offsetへ変換して読む
  if ROM_DOMAIN ~= nil then
    local base = hirom_offset(bank, addr)
    if base < 0 or base + n > ROM_SIZE then return nil, "rom_oob:" .. h6(base) end
    for i = 0, n-1 do
      local v = safe_read_u8(base + i, ROM_DOMAIN)
      if v == nil then return nil, "rom_read_failed" end
      bytes[#bytes+1] = v
    end
    return bytes, "rom:" .. h6(base)
  end

  return nil, "no_systembus_or_rom_domain"
end

local function hex_bytes(t)
  local out = {}
  for _, b in ipairs(t or {}) do out[#out+1] = h2(b) end
  return table.concat(out, " ")
end

local function all_zero(t)
  if t == nil then return true end
  for _, b in ipairs(t) do
    if b ~= 0 then return false end
  end
  return true
end

local function decode_bytes(t)
  local out = {}
  local i = 1
  while i <= #t do
    local b = t[i]
    if b == 0x02 and i < #t then
      out[#out+1] = DICT02[h2(t[i+1])] or ("{02" .. h2(t[i+1]) .. "}")
      i = i + 2
    elseif b >= 0x18 and b < 0x20 and i < #t then
      local key = h2(b) .. h2(t[i+1])
      out[#out+1] = KANJI[key] or ("{K" .. key .. "}")
      i = i + 2
    else
      out[#out+1] = SINGLE[h2(b)] or ("{" .. h2(b) .. "}")
      i = i + 1
    end
  end
  return table.concat(out, "")
end

local function state()
  return table.concat({
    "12AA=" .. h2(wram8(0x12AA)),
    "12A9=" .. h2(wram8(0x12A9)),
    "12AD=" .. h2(wram8(0x12AD)),
    "12B2=" .. h2(wram8(0x12B2)),
    "12B3=" .. h2(wram8(0x12B3)),
    "12B4=" .. h2(wram8(0x12B4)),
    "12B5=" .. h2(wram8(0x12B5)),
    "12B6=" .. h2(wram8(0x12B6)),
    "12BC=" .. h2(wram8(0x12BC)),
    "12C4=" .. h2(wram8(0x12C4)),
    "12C5=" .. h2(wram8(0x12C5))
  }, ",")
end

local function active_text_phase()
  if not ACTIVE_ONLY then return true end
  -- v19の警告は 12AD=04/12B4=04 のidle寄りで出ていたため除外。
  if wram8(0x12B4) == 0x50 and wram8(0x12AD) == 0x00 then return true end
  if wram8(0x12B2) ~= 0x00 and wram8(0x12B4) == 0x50 then return true end
  return false
end

local function source_state_words()
  local out = {}
  for a = 0x1264, 0x1286, 2 do
    local lo = wram8(a)
    local hi = wram8(a+1)
    if lo ~= 0 or hi ~= 0 then out[#out+1] = "$" .. h4(a) .. "=" .. h2(hi) .. h2(lo) end
  end
  return table.concat(out, " ")
end

logLine("shinmomo source reader compact tracer v20 loaded.")
logLine("domains=" .. join_domains(DOMAINS) .. ", WRAM=" .. tostring(WRAM_DOMAIN) .. ", SYS=" .. tostring(SYS_DOMAIN) .. ", ROM=" .. tostring(ROM_DOMAIN))
logLine("No WRAM out-of-range ROM reads. Active text phase only. READ_LEN=" .. tostring(READ_LEN))
logLine("TRACE_DIALOGUE_V20_READY,frame=" .. emu.framecount() .. "," .. state())

local last_key = ""
local last_skip_reason = ""
local last_log_frame = -9999

while true do
  emu.frameadvance()
  local f = emu.framecount()

  if active_text_phase() then
    local bank, addr = src_ptr()
    local bytes, source = read_source_bytes(bank, addr, READ_LEN)

    if bytes == nil then
      local reason = tostring(source) .. ",src_ptr=" .. h2(bank) .. ":" .. h4(addr)
      if reason ~= last_skip_reason then
        logLine("TRACE_DIALOGUE_V20_SKIP,frame=" .. f .. ",reason=" .. reason .. ",domains=" .. join_domains(DOMAINS) .. "," .. state())
        last_skip_reason = reason
      end
    elseif not all_zero(bytes) then
      local dec = decode_bytes(bytes)
      local hits = scan_static(bytes)
      local ctx = context_candidates(bytes, dec)
      local raw = hex_bytes(bytes)
      local key = h2(bank) .. ":" .. h4(addr) .. ":" .. raw .. ":" .. hits .. ":" .. ctx

      local useful = true
      if LOG_ONLY_HITS and hits == "" and ctx == "" then useful = false end

      if useful and key ~= last_key and (f - last_log_frame) >= MIN_LOG_FRAME_GAP then
        logLine(table.concat({
          "TRACE_DIALOGUE_V20_SOURCE",
          "frame=" .. f,
          "src_ptr=" .. h2(bank) .. ":" .. h4(addr),
          "source=" .. tostring(source),
          "src_raw=" .. raw,
          "src_decode=" .. dec,
          "static_hits=" .. hits,
          "context_candidates=" .. ctx,
          "source_state=" .. source_state_words(),
          state()
        }, ","))
        last_key = key
        last_log_frame = f
      end
    end
  end
end
