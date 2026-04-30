-- shinmomo_vram_cgram_tilemap_dump_v1_snes9x.lua
-- 新桃太郎伝説 VRAM/CGRAM/tilemap/OAM dump helper for Snes9x/BizHawk-like Lua
--
-- 出力:
--   shinmomo_vram_dumps/vram_frameXXXXXX.bin   64KB
--   shinmomo_vram_dumps/cgram_frameXXXXXX.bin  512 bytes, if CGRAM domain exists
--   shinmomo_vram_dumps/oam_frameXXXXXX.bin    544 bytes, if OAM domain exists
--   shinmomo_vram_dumps/tilemap_pages_frameXXXXXX.csv
--   shinmomo_vram_dumps/state_frameXXXXXX.txt
--
-- 使い方:
--   Luaを読み込むと READY を出します。
--   デフォルトでは 600 frameごとに状態だけALIVE表示。
--   DUMP_EVERY_N_FRAMES を 0 以外にすると定期dumpします。
--   手動dumpをしたい場合、DUMP_ON_MODE02_ONCE=true のまま会話/表示状態を開くと一度dumpします。
--
-- 注意:
--   Snes9x環境によって memory domain 名が違います。
--   VRAM/CGRAM/OAM domain が無い場合は、そのdumpだけスキップします。

local DUMP_DIR = "shinmomo_vram_dumps"
local DUMP_EVERY_N_FRAMES = 0        -- 例: 600なら10秒ごと程度。0なら定期dumpなし。
local DUMP_ON_MODE02_ONCE = false    -- 会話mode02で一度dumpしたい時はtrueへ。
local DUMP_ON_START = true           -- 起動直後に一度dump。
local ALIVE_EVERY_N_FRAMES = 600

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

local WRAM_DOMAIN  = choose_domain({"WRAM", "Snes WRAM", "SNES WRAM", "Main RAM"}) or DOMAINS[1]
local VRAM_DOMAIN  = choose_domain({"VRAM", "Snes VRAM", "SNES VRAM"})
local CGRAM_DOMAIN = choose_domain({"CGRAM", "CRAM", "Palette RAM", "Snes CGRAM", "SNES CGRAM"})
local OAM_DOMAIN   = choose_domain({"OAM", "Sprite RAM", "Snes OAM", "SNES OAM"})
local ROM_DOMAIN   = choose_domain({"CARTROM", "Cart ROM", "Cartridge ROM", "ROM", "Snes ROM", "SNES ROM"})

local function domain_size(domain)
  if domain == nil then return 0 end
  local ok, sz = pcall(function() return memory.getmemorydomainsize(domain) end)
  if ok and sz then return sz end
  if domain == WRAM_DOMAIN then return 0x20000 end
  if domain == VRAM_DOMAIN then return 0x10000 end
  if domain == CGRAM_DOMAIN then return 0x200 end
  if domain == OAM_DOMAIN then return 0x220 end
  return 0
end

local function safe_read_u8(addr, domain)
  if domain == nil then return nil end
  local sz = domain_size(domain)
  if sz > 0 and (addr < 0 or addr >= sz) then return nil end
  local ok, v = pcall(function() return memory.read_u8(addr, domain) end)
  if ok then return v end
  ok, v = pcall(function() return memory.readbyte(addr, domain) end)
  if ok then return v end
  return nil
end

local function wram8(addr)
  return safe_read_u8(addr, WRAM_DOMAIN) or 0
end

local function h2(v) return string.format("%02X", (v or 0) % 0x100) end
local function h4(v) return string.format("%04X", (v or 0) % 0x10000) end

local function logLine(s)
  if console and console.log then console.log(s)
  elseif client and client.log then client.log(s)
  else print(s) end
end

local function mkdir(path)
  -- Works on Windows and Unix-ish. Ignore errors.
  pcall(function() os.execute('mkdir "' .. path .. '"') end)
end

local function framecount()
  local ok, f = pcall(function() return emu.framecount() end)
  if ok and f then return f end
  ok, f = pcall(function() return movie.framecount() end)
  if ok and f then return f end
  return 0
end

local function dump_domain_bin(domain, size, path)
  if domain == nil then return false, "no-domain" end
  local sz = domain_size(domain)
  if sz <= 0 then sz = size end
  size = math.min(size, sz)
  local f, err = io.open(path, "wb")
  if not f then return false, err or "open-failed" end
  for i = 0, size - 1 do
    local v = safe_read_u8(i, domain) or 0
    f:write(string.char(v))
  end
  f:close()
  return true, "ok"
end

local function read_u16_le_domain(domain, addr)
  local lo = safe_read_u8(addr, domain) or 0
  local hi = safe_read_u8(addr + 1, domain) or 0
  return lo + hi * 256
end

local function dump_tilemap_pages_csv(frame, path)
  if VRAM_DOMAIN == nil then return false, "no-vram" end
  local f, err = io.open(path, "w")
  if not f then return false, err or "open-failed" end
  f:write("frame,page_base_vram,entry_index,x,y,raw,tile,palette,priority,hflip,vflip\n")
  -- SNES tilemap page: 32x32 entries * 2 bytes = 0x800 bytes.
  -- Output all possible 0x800-aligned pages, then choose relevant BG map base later by renderer.
  for base = 0, 0xF800, 0x800 do
    for i = 0, 1023 do
      local raw = read_u16_le_domain(VRAM_DOMAIN, base + i * 2)
      local tile = raw % 0x400
      local pal = math.floor(raw / 0x400) % 8
      local pri = math.floor(raw / 0x2000) % 2
      local hf  = math.floor(raw / 0x4000) % 2
      local vf  = math.floor(raw / 0x8000) % 2
      local x = i % 32
      local y = math.floor(i / 32)
      f:write(string.format("%d,0x%04X,%d,%d,%d,0x%04X,%d,%d,%d,%d,%d\n", frame, base, i, x, y, raw, tile, pal, pri, hf, vf))
    end
  end
  f:close()
  return true, "ok"
end

local function source_state_string()
  local parts = {}
  for a = 0x1264, 0x1286, 2 do
    local lo = wram8(a)
    local hi = wram8(a + 1)
    table.insert(parts, string.format("$%04X=%02X%02X", a, lo, hi))
  end
  return table.concat(parts, " ")
end

local function dump_state_txt(frame, path)
  local f, err = io.open(path, "w")
  if not f then return false, err or "open-failed" end
  f:write("shinmomo VRAM/CGRAM/tilemap dump state\n")
  f:write("frame=" .. tostring(frame) .. "\n")
  f:write("domains=" .. table.concat(DOMAINS, "|") .. "\n")
  f:write("WRAM=" .. tostring(WRAM_DOMAIN) .. " VRAM=" .. tostring(VRAM_DOMAIN) .. " CGRAM=" .. tostring(CGRAM_DOMAIN) .. " OAM=" .. tostring(OAM_DOMAIN) .. " ROM=" .. tostring(ROM_DOMAIN) .. "\n")
  f:write(string.format("12AA=%s 12A9=%s 12AD=%s 12B2=%s 12B3=%s 12B4=%s 12B5=%s 12B6=%s 12BC=%s 12C4=%s 12C5=%s\n",
    h2(wram8(0x12AA)), h2(wram8(0x12A9)), h2(wram8(0x12AD)), h2(wram8(0x12B2)), h2(wram8(0x12B3)),
    h2(wram8(0x12B4)), h2(wram8(0x12B5)), h2(wram8(0x12B6)), h2(wram8(0x12BC)), h2(wram8(0x12C4)), h2(wram8(0x12C5))))
  f:write("source_state=" .. source_state_string() .. "\n")
  f:close()
  return true, "ok"
end

local dumped_mode02_once = false
local last_dump_frame = -999999

local function dump_all(reason)
  mkdir(DUMP_DIR)
  local frame = framecount()
  local tag = string.format("frame%06d", frame)
  local ok_v, msg_v = dump_domain_bin(VRAM_DOMAIN, 0x10000, DUMP_DIR .. "/vram_" .. tag .. ".bin")
  local ok_c, msg_c = dump_domain_bin(CGRAM_DOMAIN, 0x200, DUMP_DIR .. "/cgram_" .. tag .. ".bin")
  local ok_o, msg_o = dump_domain_bin(OAM_DOMAIN, 0x220, DUMP_DIR .. "/oam_" .. tag .. ".bin")
  local ok_t, msg_t = dump_tilemap_pages_csv(frame, DUMP_DIR .. "/tilemap_pages_" .. tag .. ".csv")
  local ok_s, msg_s = dump_state_txt(frame, DUMP_DIR .. "/state_" .. tag .. ".txt")
  last_dump_frame = frame
  logLine(string.format("TRACE_GRAPHICS_DUMP_V1_DONE,frame=%d,reason=%s,vram=%s:%s,cgram=%s:%s,oam=%s:%s,tilemap=%s:%s,state=%s:%s,dir=%s",
    frame, reason or "manual", tostring(ok_v), tostring(msg_v), tostring(ok_c), tostring(msg_c), tostring(ok_o), tostring(msg_o), tostring(ok_t), tostring(msg_t), tostring(ok_s), tostring(msg_s), DUMP_DIR))
end

logLine("shinmomo graphics dump v1 loaded. VRAM/CGRAM/tilemap/OAM dump helper.")
logLine("domains=" .. table.concat(DOMAINS, "|") .. ", WRAM=" .. tostring(WRAM_DOMAIN) .. ", VRAM=" .. tostring(VRAM_DOMAIN) .. ", CGRAM=" .. tostring(CGRAM_DOMAIN) .. ", OAM=" .. tostring(OAM_DOMAIN) .. ", ROM=" .. tostring(ROM_DOMAIN))
logLine("TRACE_GRAPHICS_DUMP_V1_READY,frame=" .. tostring(framecount()))

if DUMP_ON_START then dump_all("start") end

while true do
  local frame = framecount()
  if ALIVE_EVERY_N_FRAMES > 0 and frame % ALIVE_EVERY_N_FRAMES == 0 then
    logLine(string.format("TRACE_GRAPHICS_DUMP_V1_ALIVE,frame=%d,12AA=%s,12B4=%s,12B5=%s,12C4=%s,12C5=%s", frame, h2(wram8(0x12AA)), h2(wram8(0x12B4)), h2(wram8(0x12B5)), h2(wram8(0x12C4)), h2(wram8(0x12C5))))
  end
  if DUMP_EVERY_N_FRAMES > 0 and frame > 0 and frame % DUMP_EVERY_N_FRAMES == 0 and frame ~= last_dump_frame then
    dump_all("periodic")
  end
  if DUMP_ON_MODE02_ONCE and not dumped_mode02_once and wram8(0x12AA) == 0x02 then
    dumped_mode02_once = true
    dump_all("mode02_once")
  end
  emu.frameadvance()
end
