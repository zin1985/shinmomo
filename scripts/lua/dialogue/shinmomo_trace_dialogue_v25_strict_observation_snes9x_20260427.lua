-- shinmomo_trace_dialogue_v25_strict_observation_snes9x_20260427.lua
-- v25: 汎用化のための strict observation 版
--
-- 方針:
--   * 文脈から予測した単語をプログラム内に追加しない
--   * 画面文脈による固定置換/reconstructed_candidate/display_hints は出さない
--   * あくまで実際に観測した表示tokenと周辺メモリを出す
--   * 足りない文字は「追加メモリ窓」「source_state」「raw token列」から後で解析する
--
-- 出力:
--   TRACE_DIALOGUE_V25_MODE_SOURCE
--   TRACE_DIALOGUE_V25_TOKEN
--   TRACE_DIALOGUE_V25_LINE
--
-- 見るところ:
--   decoded_observed=
--   token_events=
--   mem12_window=
--   source_state=
--   mode_source_raw=

local READ_LEN = 32
local DISPLAY_IDLE_FLUSH_FRAMES = 90
local TOKEN_REPEAT_SUPPRESS_FRAMES = 3

local function list_domains()
  local ok, domains = pcall(function() return memory.getmemorydomainlist() end)
  if ok and domains then return domains end
  return {}
end

local DOMAINS = list_domains()

local function choose_domain(preferred)
  for _, want in ipairs(preferred) do
    for _, got in ipairs(DOMAINS) do
      if got == want then return got end
    end
  end
  for _, want in ipairs(preferred) do
    local wl = string.lower(want)
    for _, got in ipairs(DOMAINS) do
      if string.find(string.lower(got), wl, 1, true) then return got end
    end
  end
  return nil
end

local WRAM_DOMAIN = choose_domain({"WRAM", "Snes WRAM", "SNES WRAM", "Main RAM"}) or DOMAINS[1]
local ROM_DOMAIN  = choose_domain({"CARTROM", "Cart ROM", "Cartridge ROM", "ROM", "Snes ROM", "SNES ROM"})

local function domain_size(domain)
  if domain == nil then return 0 end
  local ok, sz = pcall(function() return memory.getmemorydomainsize(domain) end)
  if ok and sz then return sz end
  if domain == WRAM_DOMAIN then return 0x20000 end
  if domain == ROM_DOMAIN then return 0x800000 end
  return 0
end

local function safe_read_u8(addr, domain)
  if domain == nil then return nil end
  local sz = domain_size(domain)
  if sz > 0 and (addr < 0 or addr >= sz) then return nil end
  local ok, v = pcall(function() return memory.read_u8(addr, domain) end)
  if ok then return v end
  return nil
end

local function wram8(addr)
  return safe_read_u8(addr, WRAM_DOMAIN) or 0
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
  if console and console.log then console.log(s)
  elseif client and client.log then client.log(s)
  else print(s) end
end

-- ここは「文字コード表」として扱う。
-- 会話文脈から予測した単語・文章は入れない。
-- 未確定文字は {xx}/{Kxxxx}/{02xx} のまま出す。
local SINGLE = {
  ["50"]=" ", ["51"]="  ", ["52"]="   ",
  ["5C"]="!", ["7D"]="「", ["7E"]="」", ["80"]="ー",

  ["90"]="あ", ["91"]="い", ["92"]="う", ["93"]="え", ["94"]="お",
  ["95"]="か", ["96"]="き", ["97"]="く", ["98"]="け", ["99"]="こ",
  ["9A"]="さ", ["9B"]="し", ["9C"]="す", ["9D"]="せ", ["9E"]="そ", ["9F"]="た",
  ["A0"]="ち", ["A1"]="つ", ["A2"]="て", ["A3"]="と", ["A4"]="な", ["A5"]="に",
  ["A6"]="ぬ", ["A7"]="ね", ["A8"]="の", ["A9"]="は",
  ["AE"]="ま", ["AF"]="み", ["B0"]="む", ["B1"]="め", ["B2"]="も", ["B3"]="や",
  ["B5"]="よ", ["B6"]="ら", ["B7"]="り", ["B8"]="る", ["B9"]="れ", ["BA"]="ろ",
  ["BB"]="わ", ["BC"]="を", ["BD"]="ん", ["BE"]="で", ["BF"]="ど",

  ["D0"]="が", ["D3"]="ぎ", ["D6"]="じ", ["D9"]="だ", ["DA"]="だ", ["DD"]="な", ["DE"]="ば", ["DF"]="び",
  ["E5"]="づ", ["F5"]="っ", ["F6"]="ゃ", ["F8"]="ゅ", ["FC"]="？"
}

-- 確度が高い既知2byte辞書だけ。文脈予測語は入れない。
local DICT02 = {
  ["A0"]="桃太郎",
  ["AC"]="オニ",
  ["B0"]="きんたん",
  ["B9"]="ゆうき",
  ["C0"]="おにぎり",
  ["CD"]="ちから",
  ["CE"]="あしゅら"
}

-- 確定済み漢字コードだけ。文章候補や文脈補正は入れない。
local KANJI = {
  ["1800"]="桃", ["1801"]="太", ["1802"]="郎",
  ["1803"]="金", ["1804"]="浦", ["1805"]="島",
  ["1808"]="夜", ["1809"]="叉", ["180A"]="姫",
  ["1811"]="西", ["1813"]="北", ["1815"]="体",
  ["181F"]="装", ["1820"]="備",
  ["1847"]="人", ["184C"]="刀",
  ["1850"]="銀", ["1851"]="次",
  ["188F"]="火", ["18DB"]="鬼", ["18F2"]="無",
  ["199B"]="旅", ["19BF"]="行", ["19D7"]="入", ["19EB"]="穴",
  ["1A1A"]="言", ["1A31"]="理", ["1A59"]="着", ["1A5F"]="流"
}

local function src_ptr()
  local lo = wram8(0x00B1)
  local hi = wram8(0x00B2)
  local bank = wram8(0x00B3)
  return bank, lo + hi * 0x100
end

local function hirom_offset(bank, addr)
  local b = bank
  if b >= 0xC0 then b = b - 0xC0
  elseif b >= 0x80 then b = b - 0x80 end
  return b * 0x10000 + addr
end

local function read_rom(bank, addr, n)
  if ROM_DOMAIN == nil then return nil, "no_rom_domain" end
  local base = hirom_offset(bank, addr)
  local sz = domain_size(ROM_DOMAIN)
  if base < 0 or base + n > sz then return nil, "rom_oob:" .. h6(base) end
  local t = {}
  for i=0,n-1 do
    local v = safe_read_u8(base+i, ROM_DOMAIN)
    if v == nil then return nil, "rom_read_failed" end
    t[#t+1] = v
  end
  return t, "rom:" .. h6(base)
end

local function hex_bytes(t)
  local out = {}
  for _, b in ipairs(t or {}) do out[#out+1] = h2(b) end
  return table.concat(out, " ")
end

local function decode_single_byte(b)
  return SINGLE[h2(b)] or ("{" .. h2(b) .. "}")
end

local function decode_kanji_pair(prefix, low)
  local key = h2(prefix) .. h2(low)
  return KANJI[key] or ("{K" .. key .. "}")
end

local function decode_dict02(low)
  return DICT02[h2(low)] or ("{02" .. h2(low) .. "}")
end

local function decode_token_candidate(prefix, low)
  if prefix == 0x02 then
    return decode_dict02(low)
  elseif prefix >= 0x18 and prefix < 0x20 then
    return decode_kanji_pair(prefix, low)
  else
    return decode_single_byte(prefix)
  end
end

local function decode_display_observed()
  local b2 = wram8(0x12B2)
  local b3 = wram8(0x12B3)
  local c4 = wram8(0x12C4)
  local c5 = wram8(0x12C5)

  local primary = ""
  local via = ""

  -- c4/c5 reverse dict candidate
  if c5 == 0x02 then
    primary = decode_dict02(c4)
    via = "c4c5_dict02_rev"
  -- b2/b3 kanji candidate
  elseif b2 >= 0x18 and b2 < 0x20 then
    primary = decode_kanji_pair(b2, b3)
    via = "b2b3_kanji"
  -- c4/c5 kanji candidate
  elseif c4 >= 0x18 and c4 < 0x20 then
    primary = decode_kanji_pair(c4, c5)
    via = "c4c5_kanji"
  else
    local a = SINGLE[h2(c4)] or ""
    local b = SINGLE[h2(b2)] or ""
    if a ~= "" and b ~= "" and c4 == b2 then
      primary = a
      via = "dedup_same_c4_b2"
    else
      primary = a .. b
      via = "single_mix"
    end
  end

  local alt_b2 = ""
  if b2 >= 0x18 and b2 < 0x20 then
    alt_b2 = decode_kanji_pair(b2, b3)
  elseif b2 ~= 0 then
    alt_b2 = SINGLE[h2(b2)] or ("{" .. h2(b2) .. "}")
  end

  local alt_c4 = ""
  if c4 >= 0x18 and c4 < 0x20 then
    alt_c4 = decode_kanji_pair(c4, c5)
  elseif c5 == 0x02 then
    alt_c4 = decode_dict02(c4)
  elseif c4 ~= 0 then
    alt_c4 = SINGLE[h2(c4)] or ("{" .. h2(c4) .. "}")
  end

  return primary, via, alt_b2, alt_c4
end

local function mem_window(start, len)
  local out = {}
  for i=0,len-1 do out[#out+1] = h2(wram8(start+i)) end
  return table.concat(out, " ")
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

local function source_state_words()
  local out = {}
  for a = 0x1264, 0x1286, 2 do
    local lo = wram8(a)
    local hi = wram8(a+1)
    if lo ~= 0 or hi ~= 0 then out[#out+1] = "$" .. h4(a) .. "=" .. h2(hi) .. h2(lo) end
  end
  return table.concat(out, " ")
end

local function active_text()
  return wram8(0x12B4) == 0x50 or wram8(0x12AD) == 0x00 or wram8(0x12B2) ~= 0x00
end

logLine("shinmomo dialogue v25 strict observation tracer loaded.")
logLine("domains=" .. table.concat(DOMAINS, "|") .. ", WRAM=" .. tostring(WRAM_DOMAIN) .. ", ROM=" .. tostring(ROM_DOMAIN))
logLine("No context word insertion. No display_hints. No reconstructed_candidate.")
logLine("TRACE_DIALOGUE_V25_READY,frame=" .. emu.framecount() .. "," .. state())

local last_mode_key = ""
local decoded_buf = ""
local token_events = {}
local last_token_key = ""
local last_token_frame = -9999
local last_display_frame = emu.framecount()

while true do
  emu.frameadvance()
  local f = emu.framecount()

  if active_text() then
    local bank, addr = src_ptr()
    local mode = wram8(0x12AA)

    -- mode/source rawは、文字として決め打ちしない。rawだけ保存。
    if mode ~= 0x00 then
      local bytes, src = read_rom(bank, addr, READ_LEN)
      if bytes ~= nil then
        local mkey = h2(mode) .. ":" .. h2(bank) .. ":" .. h4(addr) .. ":" .. hex_bytes(bytes)
        if mkey ~= last_mode_key then
          logLine(table.concat({
            "TRACE_DIALOGUE_V25_MODE_SOURCE",
            "frame=" .. f,
            "mode=" .. h2(mode),
            "src_ptr=" .. h2(bank) .. ":" .. h4(addr),
            "source=" .. tostring(src),
            "mode_source_raw=" .. hex_bytes(bytes),
            "source_state=" .. source_state_words(),
            "mem12_window=" .. mem_window(0x12A0, 0x40),
            state()
          }, ","))
          last_mode_key = mkey
        end
      end
    end

    local primary, via, alt_b2, alt_c4 = decode_display_observed()
    local raw_key = table.concat({
      h2(wram8(0x12B2)), h2(wram8(0x12B3)),
      h2(wram8(0x12C4)), h2(wram8(0x12C5)),
      h2(wram8(0x12AD)), h2(wram8(0x12BC)),
      tostring(primary)
    }, ":")

    if primary ~= "" and (raw_key ~= last_token_key or (f - last_token_frame) > TOKEN_REPEAT_SUPPRESS_FRAMES) then
      decoded_buf = decoded_buf .. primary
      token_events[#token_events+1] = string.format(
        "f%d:%s:b2%02X%02X:c4%02X%02X:via=%s:alt_b2=%s:alt_c4=%s",
        f, primary,
        wram8(0x12B2), wram8(0x12B3), wram8(0x12C4), wram8(0x12C5),
        via, alt_b2, alt_c4
      )
      if #token_events > 80 then table.remove(token_events, 1) end

      logLine(table.concat({
        "TRACE_DIALOGUE_V25_TOKEN",
        "frame=" .. f,
        "token=" .. primary,
        "via=" .. via,
        "alt_b2=" .. alt_b2,
        "alt_c4=" .. alt_c4,
        state()
      }, ","))

      last_token_key = raw_key
      last_token_frame = f
      last_display_frame = f
    end

    if decoded_buf ~= "" and (f - last_display_frame) > DISPLAY_IDLE_FLUSH_FRAMES then
      logLine(table.concat({
        "TRACE_DIALOGUE_V25_LINE",
        "frame=" .. f,
        "decoded_observed=" .. decoded_buf,
        "token_events=" .. table.concat(token_events, " | "),
        "source_state=" .. source_state_words(),
        "mem12_window=" .. mem_window(0x12A0, 0x40),
        state()
      }, ","))
      decoded_buf = ""
      token_events = {}
      last_token_key = ""
    end
  else
    if decoded_buf ~= "" and (f - last_display_frame) > DISPLAY_IDLE_FLUSH_FRAMES then
      logLine(table.concat({
        "TRACE_DIALOGUE_V25_LINE",
        "frame=" .. f,
        "decoded_observed=" .. decoded_buf,
        "token_events=" .. table.concat(token_events, " | "),
        "source_state=" .. source_state_words(),
        "mem12_window=" .. mem_window(0x12A0, 0x40),
        state()
      }, ","))
      decoded_buf = ""
      token_events = {}
      last_token_key = ""
    end
  end
end
