-- shinmomo_graphics_full_capture_v2_snes9x_bizhawk_20260502.lua
-- 新桃太郎伝説 グラフィック完全復元用 全情報採取Lua v2
--
-- 目的:
--   グラフィック再現に必要な情報を、可能な限り1スナップショットに集約して出力する。
--   対象は BG/mapchip、キャラクター/OAM、CGRAM palette、PPU state、DMA/VRAM write、WRAM visible object候補。
--
-- 想定エミュレータ:
--   BizHawk系 Lua API を主想定。
--   Snes9x系でも memory.readbyte / event.onmemorywrite / emu.framecount があれば動くように寄せる。
--   write-only PPU register は「Lua開始後のwrite mirror」で拾うため、ROM起動直後から実行するほど正確。
--
-- 出力例:
--   shinmomo_graphics_full_capture_out/
--     manifest.csv
--     ppu_write_log.csv
--     dma_trigger_log.csv
--     vram_write_log.csv
--     cgram_write_log.csv
--     run_notes.txt
--     frame_000123/
--       frame_info.csv
--       vram.bin
--       cgram.bin
--       oam.bin
--       wram_0000_1fff.bin
--       wram_3900_03ff.bin
--       wram_7000_0200.bin
--       wram_dma_queue_8000_0800.bin
--       ppu_regs_capture.csv
--       cgram_palette.csv
--       bg_summary.csv
--       bg1_tilemap_decoded.csv ... bg4_tilemap_decoded.csv
--       all_tilemap_pages_decoded.csv
--       bg1_metatile_2x2.csv ... bg4_metatile_2x2.csv
--       oam_sprites.csv
--       oam_visible.csv
--       object_slots_0x00_0x7f.csv
--       object_active_chain_guess.csv
--       wram_watch_values.csv
--       vram_region_hashes.csv
--       tiles_2bpp_sheet.ppm / tiles_4bpp_sheet.ppm / tiles_8bpp_sheet.ppm
--       bg1_preview.ppm ... bg4_preview.ppm
--
-- 使い方:
--   1. ROM起動直後か、目的画面に入る前にこのLuaを実行する。
--   2. タイトル、フィールド、町、屋内、戦闘、会話あり/なしを移動する。
--   3. DUMP_EVERY_FRAMES間隔、またはPPU設定変化時に frame_xxxxxx が作られる。
--   4. 正確な色再現は cgram.bin + tilemap palette / OAM palette を使う。
--   5. キャラ再現は oam.bin / oam_sprites.csv と VRAM/CGRAM を使う。

------------------------------------------------------------
-- Config
------------------------------------------------------------

local OUT_DIR = "shinmomo_graphics_full_capture_out"
local DUMP_EVERY_FRAMES = 180              -- 3秒相当。重ければ 300 以上へ
local HEARTBEAT_EVERY_FRAMES = 60
local DUMP_ON_PPU_SIG_CHANGE = true
local PPU_CHANGE_COOLDOWN_FRAMES = 45
local DUMP_RAW_BINS = true
local DUMP_FULL_TILE_SHEETS = true
local DUMP_BG_PREVIEWS = true
local DUMP_ALL_TILEMAP_PAGES = true
local DUMP_OBJECT_SLOTS = true
local DUMP_WRAM_RANGES = true
local MAX_WRITE_LOG_PER_FRAME = 256
local MAX_ACTIVE_CHAIN = 128

------------------------------------------------------------
-- Utilities
------------------------------------------------------------

local function log(s)
  if console and console.log then console.log(s) else print(s) end
end

local function hex2(v) return string.format("%02X", (v or 0) & 0xFF) end
local function hex4(v) return string.format("%04X", (v or 0) & 0xFFFF) end
local function hex6(v) return string.format("%06X", (v or 0) & 0xFFFFFF) end
local function hex8(v) return string.format("%08X", (v or 0) & 0xFFFFFFFF) end

local function path_sep()
  if package and package.config then return package.config:sub(1,1) end
  return "/"
end
local SEP = path_sep()

local function join(a,b)
  if a:sub(-1) == "/" or a:sub(-1) == "\\" then return a .. b end
  return a .. SEP .. b
end

local function ensure_dir(path)
  if SEP == "\\" then
    os.execute('mkdir "' .. path .. '" >nul 2>nul')
  else
    os.execute('mkdir -p "' .. path .. '" >/dev/null 2>/dev/null')
  end
end

local function write_text(path, text)
  local f = assert(io.open(path, "w"))
  f:write(text or "")
  f:close()
end

local function append_text(path, text)
  local f = io.open(path, "a")
  if not f then f = assert(io.open(path, "w")) end
  f:write(text or "")
  f:close()
end

local function write_bin(path, bytes)
  local f = assert(io.open(path, "wb"))
  for i=1,#bytes do f:write(string.char((bytes[i] or 0) & 0xFF)) end
  f:close()
end

local function csv_escape(s)
  s = tostring(s or "")
  if s:find("[,\n\"]") then s = '"' .. s:gsub('"','""') .. '"' end
  return s
end

local function csv_line(t)
  local out = {}
  for i,v in ipairs(t) do out[#out+1] = csv_escape(v) end
  return table.concat(out, ",") .. "\n"
end

local function fnv1a_update(h, v)
  h = (h ~ ((v or 0) & 0xFF)) & 0xFFFFFFFF
  h = (h * 16777619) & 0xFFFFFFFF
  return h
end

local function simple_hash(bytes)
  local h = 2166136261
  for i=1,#bytes do h = fnv1a_update(h, bytes[i]) end
  return h
end

------------------------------------------------------------
-- Emulator API abstraction
------------------------------------------------------------

local function get_domains()
  local ok, domains = pcall(function()
    if memory and memory.getmemorydomainlist then return memory.getmemorydomainlist() end
    return {}
  end)
  if ok and domains then return domains end
  return {}
end

local DOMAINS = get_domains()
local function find_domain(candidates)
  for _,want in ipairs(candidates) do
    for _,got in ipairs(DOMAINS) do if got == want then return got end end
  end
  for _,want in ipairs(candidates) do
    local lw = want:lower()
    for _,got in ipairs(DOMAINS) do
      if got:lower():find(lw, 1, true) then return got end
    end
  end
  return nil
end

local BUS_DOMAIN   = find_domain({"System Bus", "Bus", "Snes Bus", "SNES Bus"})
local WRAM_DOMAIN  = find_domain({"WRAM", "Snes WRAM", "SNES WRAM", "Main RAM", "Work RAM"})
local VRAM_DOMAIN  = find_domain({"VRAM", "Snes VRAM", "SNES VRAM"})
local CGRAM_DOMAIN = find_domain({"CGRAM", "Snes CGRAM", "SNES CGRAM", "CRAM"})
local OAM_DOMAIN   = find_domain({"OAM", "Snes OAM", "SNES OAM", "Sprite RAM"})

local function safe_read_u8(addr, domain)
  if not memory then return 0 end
  local ok, v
  if memory.read_u8 then
    ok, v = pcall(memory.read_u8, addr, domain)
    if ok and v ~= nil then return v & 0xFF end
  end
  if memory.readbyte then
    if domain ~= nil then ok, v = pcall(memory.readbyte, addr, domain) else ok, v = pcall(memory.readbyte, addr) end
    if ok and v ~= nil then return v & 0xFF end
  end
  return 0
end

local function bus_read(addr)
  if BUS_DOMAIN then return safe_read_u8(addr, BUS_DOMAIN) end
  return safe_read_u8(addr, nil)
end

local function wram_read(addr)
  if WRAM_DOMAIN then return safe_read_u8(addr, WRAM_DOMAIN) end
  return bus_read(0x7E0000 + addr)
end

local function read_domain_bytes(domain, start_addr, size)
  local t = {}
  if not domain then return t end
  for i=0,size-1 do t[#t+1] = safe_read_u8(start_addr + i, domain) end
  return t
end

local function read_wram_range(start_addr, size)
  local t = {}
  for i=0,size-1 do t[#t+1] = wram_read(start_addr + i) end
  return t
end

local function current_frame()
  if emu and emu.framecount then
    local ok, v = pcall(emu.framecount)
    if ok and v then return v end
  end
  return 0
end

------------------------------------------------------------
-- PPU register mirror and write logs
------------------------------------------------------------

local function ppu_reg_name(addr)
  local names = {
    [0x2100]="INIDISP", [0x2101]="OBSEL", [0x2102]="OAMADDL", [0x2103]="OAMADDH", [0x2104]="OAMDATA",
    [0x2105]="BGMODE", [0x2106]="MOSAIC", [0x2107]="BG1SC", [0x2108]="BG2SC", [0x2109]="BG3SC", [0x210A]="BG4SC",
    [0x210B]="BG12NBA", [0x210C]="BG34NBA", [0x210D]="BG1HOFS", [0x210E]="BG1VOFS", [0x210F]="BG2HOFS", [0x2110]="BG2VOFS",
    [0x2111]="BG3HOFS", [0x2112]="BG3VOFS", [0x2113]="BG4HOFS", [0x2114]="BG4VOFS", [0x2115]="VMAIN",
    [0x2116]="VMADDL", [0x2117]="VMADDH", [0x2118]="VMDATAL", [0x2119]="VMDATAH", [0x211A]="M7SEL",
    [0x2121]="CGADD", [0x2122]="CGDATA", [0x2123]="W12SEL", [0x2124]="W34SEL", [0x2125]="WOBJSEL",
    [0x2126]="WH0", [0x2127]="WH1", [0x2128]="WH2", [0x2129]="WH3", [0x212A]="WBGLOG", [0x212B]="WOBJLOG",
    [0x212C]="TM", [0x212D]="TS", [0x212E]="TMW", [0x212F]="TSW", [0x2130]="CGWSEL", [0x2131]="CGADSUB",
    [0x2132]="COLDATA", [0x2133]="SETINI",
    [0x4200]="NMITIMEN", [0x420B]="MDMAEN", [0x420C]="HDMAEN"
  }
  if addr >= 0x4300 and addr <= 0x437F then
    local ch = math.floor((addr - 0x4300) / 0x10)
    local r = (addr - 0x4300) % 0x10
    local rn = ({[0]="DMAP",[1]="BBAD",[2]="A1T_L",[3]="A1T_H",[4]="A1B",[5]="DAS_L",[6]="DAS_H",[7]="DASB",[8]="A2A_L",[9]="A2A_H",[10]="NLTR"})[r] or ("R"..r)
    return "DMA" .. ch .. "_" .. rn
  end
  return names[addr] or ""
end

local ppu = {}
for a=0x2100,0x213F do ppu[a] = 0 end
for a=0x4200,0x421F do ppu[a] = 0 end
for a=0x4300,0x437F do ppu[a] = 0 end

local ppu_write_log_path = join(OUT_DIR, "ppu_write_log.csv")
local dma_log_path = join(OUT_DIR, "dma_trigger_log.csv")
local vram_write_log_path = join(OUT_DIR, "vram_write_log.csv")
local cgram_write_log_path = join(OUT_DIR, "cgram_write_log.csv")
local manifest_path = join(OUT_DIR, "manifest.csv")
local notes_path = join(OUT_DIR, "run_notes.txt")

local per_frame_write_count = {}
local function can_log_write(kind)
  local f = current_frame()
  per_frame_write_count[f] = (per_frame_write_count[f] or 0) + 1
  return per_frame_write_count[f] <= MAX_WRITE_LOG_PER_FRAME
end

local function dma_channel_row(ch)
  local base = 0x4300 + ch * 0x10
  local dmap = ppu[base + 0] or 0
  local bbad = ppu[base + 1] or 0
  local a1t = (ppu[base + 2] or 0) + ((ppu[base + 3] or 0) << 8)
  local a1b = ppu[base + 4] or 0
  local das = (ppu[base + 5] or 0) + ((ppu[base + 6] or 0) << 8)
  local dasb = ppu[base + 7] or 0
  return {ch, hex2(dmap), hex2(bbad), hex4(a1t), hex2(a1b), hex4(das), hex2(dasb), hex6((a1b << 16) | a1t), hex4(0x2100 + bbad)}
end

local function record_dma_trigger(addr, value)
  for ch=0,7 do
    if ((value >> ch) & 1) ~= 0 then
      local r = dma_channel_row(ch)
      append_text(dma_log_path, csv_line({current_frame(), hex4(addr), hex2(value), r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9]}))
    end
  end
end

local function record_ppu_write(addr, value)
  value = value & 0xFF
  ppu[addr] = value
  if can_log_write("ppu") then
    append_text(ppu_write_log_path, csv_line({current_frame(), hex4(addr), ppu_reg_name(addr), hex2(value)}))
  end
  if addr == 0x2118 or addr == 0x2119 then
    append_text(vram_write_log_path, csv_line({current_frame(), hex4(addr), ppu_reg_name(addr), hex2(value), hex2(ppu[0x2115]), hex2(ppu[0x2116]), hex2(ppu[0x2117])}))
  elseif addr == 0x2122 then
    append_text(cgram_write_log_path, csv_line({current_frame(), hex4(addr), hex2(value), hex2(ppu[0x2121])}))
  elseif addr == 0x420B or addr == 0x420C then
    record_dma_trigger(addr, value)
  end
end

local function install_write_hooks()
  if not event or not event.onmemorywrite then
    append_text(notes_path, "WARN: event.onmemorywrite is unavailable; PPU write mirror will remain incomplete.\n")
    return
  end
  local function hook_addr(addr)
    local function cb(a, v)
      -- BizHawk often gives (addr,value); some cores give value only. Use given addr if sane.
      local aa = addr
      local vv = v
      if type(a) == "number" and type(v) ~= "number" then vv = a end
      record_ppu_write(aa, vv or 0)
    end
    pcall(event.onmemorywrite, cb, addr, "shinmomo_ppu_" .. hex4(addr))
    if BUS_DOMAIN then pcall(event.onmemorywrite, cb, addr, BUS_DOMAIN, "shinmomo_ppu_" .. hex4(addr)) end
  end
  for a=0x2100,0x213F do hook_addr(a) end
  for a=0x4200,0x421F do hook_addr(a) end
  for a=0x4300,0x437F do hook_addr(a) end
end

------------------------------------------------------------
-- SNES BG / tile helpers
------------------------------------------------------------

local function vram_byte(vram, addr)
  return vram[(addr & 0xFFFF) + 1] or 0
end

local function cgram_word(cgram, index)
  local lo = cgram[index*2 + 1] or 0
  local hi = cgram[index*2 + 2] or 0
  return lo | (hi << 8)
end

local function snes_color_to_rgb(w)
  local r = w & 0x1F
  local g = (w >> 5) & 0x1F
  local b = (w >> 10) & 0x1F
  return {math.floor(r * 255 / 31), math.floor(g * 255 / 31), math.floor(b * 255 / 31), r, g, b}
end

local function cgram_palette(cgram)
  local pal = {}
  for i=0,255 do pal[i] = snes_color_to_rgb(cgram_word(cgram, i)) end
  return pal
end

local function tile_pixel(vram, base, tile_num, bpp, x, y)
  local tile_size = ({[2]=16, [4]=32, [8]=64})[bpp] or 32
  local addr = (base + tile_num * tile_size) & 0xFFFF
  local bit = 7 - x
  local color = 0
  local p0 = vram_byte(vram, addr + y*2)
  local p1 = vram_byte(vram, addr + y*2 + 1)
  color = color | (((p0 >> bit) & 1) << 0)
  color = color | (((p1 >> bit) & 1) << 1)
  if bpp >= 4 then
    local p2 = vram_byte(vram, addr + 16 + y*2)
    local p3 = vram_byte(vram, addr + 16 + y*2 + 1)
    color = color | (((p2 >> bit) & 1) << 2)
    color = color | (((p3 >> bit) & 1) << 3)
  end
  if bpp >= 8 then
    local p4 = vram_byte(vram, addr + 32 + y*2)
    local p5 = vram_byte(vram, addr + 32 + y*2 + 1)
    local p6 = vram_byte(vram, addr + 48 + y*2)
    local p7 = vram_byte(vram, addr + 48 + y*2 + 1)
    color = color | (((p4 >> bit) & 1) << 4)
    color = color | (((p5 >> bit) & 1) << 5)
    color = color | (((p6 >> bit) & 1) << 6)
    color = color | (((p7 >> bit) & 1) << 7)
  end
  return color
end

local function write_ppm(path, width, height, pixels)
  local f = assert(io.open(path, "wb"))
  f:write("P6\n" .. width .. " " .. height .. "\n255\n")
  for i=1,width*height do
    local p = pixels[i] or {0,0,0}
    f:write(string.char((p[1] or 0) & 0xFF, (p[2] or 0) & 0xFF, (p[3] or 0) & 0xFF))
  end
  f:close()
end

local function bgmode() return (ppu[0x2105] or 0) & 0x07 end
local function bg_sc_reg(bg) return ppu[0x2106 + bg] or 0 end
local function bg_map_base(bg) return ((bg_sc_reg(bg) & 0xFC) << 8) & 0xFFFF end
local function bg_map_size_code(bg) return bg_sc_reg(bg) & 0x03 end
local function bg_dims(bg)
  local s = bg_map_size_code(bg)
  if s == 0 then return 32,32 end
  if s == 1 then return 64,32 end
  if s == 2 then return 32,64 end
  return 64,64
end

local function bg_bpp(bg)
  local m = bgmode()
  if m == 0 then return 2 end
  if m == 1 then if bg == 3 then return 2 else return 4 end end
  if m == 2 then return 4 end
  if m == 3 then if bg == 1 then return 8 else return 4 end end
  if m == 4 then if bg == 1 then return 8 else return 2 end end
  if m == 5 then if bg == 1 then return 4 else return 2 end end
  if m == 6 then return 4 end
  if m == 7 then return 8 end
  return 4
end

local function bg_char_base(bg)
  if bg <= 2 then
    local r = ppu[0x210B] or 0
    local nib = (bg == 1) and (r & 0x0F) or ((r >> 4) & 0x0F)
    return (nib << 12) & 0xFFFF
  else
    local r = ppu[0x210C] or 0
    local nib = (bg == 3) and (r & 0x0F) or ((r >> 4) & 0x0F)
    return (nib << 12) & 0xFFFF
  end
end

local function tilemap_entry_addr(base, tx, ty, width, height)
  local sx = math.floor(tx / 32)
  local sy = math.floor(ty / 32)
  local ix = tx % 32
  local iy = ty % 32
  local screen_index = 0
  if width == 64 and height == 32 then screen_index = sx
  elseif width == 32 and height == 64 then screen_index = sy
  elseif width == 64 and height == 64 then screen_index = sy * 2 + sx end
  return (base + screen_index * 0x800 + (iy * 32 + ix) * 2) & 0xFFFF
end

local function read_tilemap_entry(vram, base, tx, ty, width, height)
  local a = tilemap_entry_addr(base, tx, ty, width, height)
  local lo = vram_byte(vram, a)
  local hi = vram_byte(vram, a + 1)
  return lo | (hi << 8), a
end

local function decode_entry(e)
  return {
    tile = e & 0x03FF,
    palette = (e >> 10) & 0x07,
    priority = (e >> 13) & 0x01,
    hflip = (e >> 14) & 0x01,
    vflip = (e >> 15) & 0x01
  }
end

------------------------------------------------------------
-- Dump helpers
------------------------------------------------------------

local function dump_cgram_palette_csv(dir, cgram)
  local lines = {csv_line({"index","group16","index_in_group","raw_bgr15","r5","g5","b5","r8","g8","b8"})}
  for i=0,255 do
    local w = cgram_word(cgram, i)
    local rgb = snes_color_to_rgb(w)
    lines[#lines+1] = csv_line({i, math.floor(i/16), i%16, hex4(w), rgb[4], rgb[5], rgb[6], rgb[1], rgb[2], rgb[3]})
  end
  write_text(join(dir, "cgram_palette.csv"), table.concat(lines))
end

local function dump_ppu_regs(dir)
  local lines = {csv_line({"addr","name","value"})}
  for a=0x2100,0x213F do lines[#lines+1] = csv_line({hex4(a), ppu_reg_name(a), hex2(ppu[a])}) end
  for a=0x4200,0x421F do lines[#lines+1] = csv_line({hex4(a), ppu_reg_name(a), hex2(ppu[a])}) end
  for a=0x4300,0x437F do lines[#lines+1] = csv_line({hex4(a), ppu_reg_name(a), hex2(ppu[a])}) end
  write_text(join(dir, "ppu_regs_capture.csv"), table.concat(lines))
end

local function dump_bg_summary(dir)
  local lines = {csv_line({"frame","mode","bg","sc_reg","map_base","size_code","width_tiles","height_tiles","char_base","bpp","tm_main","ts_sub","obsel","bg12nba","bg34nba"})}
  for bg=1,4 do
    local w,h = bg_dims(bg)
    lines[#lines+1] = csv_line({current_frame(), bgmode(), bg, hex2(bg_sc_reg(bg)), hex4(bg_map_base(bg)), bg_map_size_code(bg), w, h, hex4(bg_char_base(bg)), bg_bpp(bg), hex2(ppu[0x212C]), hex2(ppu[0x212D]), hex2(ppu[0x2101]), hex2(ppu[0x210B]), hex2(ppu[0x210C])})
  end
  write_text(join(dir, "bg_summary.csv"), table.concat(lines))
end

local function dump_bg_tilemap_csv(dir, bg, vram)
  local base = bg_map_base(bg)
  local cb = bg_char_base(bg)
  local width,height = bg_dims(bg)
  local bpp = bg_bpp(bg)
  local tile_size = ({[2]=16,[4]=32,[8]=64})[bpp] or 32
  local lines = {csv_line({"bg","tx","ty","vram_addr","entry_hex","tile","tile_addr","palette","palette_base_color_index","priority","hflip","vflip","map_base","char_base","bpp","mode"})}
  for ty=0,height-1 do
    for tx=0,width-1 do
      local e, addr = read_tilemap_entry(vram, base, tx, ty, width, height)
      local d = decode_entry(e)
      local pal_base = (bpp == 2) and (d.palette * 4) or ((bpp == 4) and (d.palette * 16) or 0)
      local tile_addr = (cb + d.tile * tile_size) & 0xFFFF
      lines[#lines+1] = csv_line({bg, tx, ty, hex4(addr), hex4(e), d.tile, hex4(tile_addr), d.palette, pal_base, d.priority, d.hflip, d.vflip, hex4(base), hex4(cb), bpp, bgmode()})
    end
  end
  write_text(join(dir, "bg"..bg.."_tilemap_decoded.csv"), table.concat(lines))
end

local function dump_all_tilemap_pages(dir, vram)
  local lines = {csv_line({"page_base","cell","tx","ty","vram_addr","entry_hex","tile","palette","priority","hflip","vflip"})}
  for page=0,0xF800,0x800 do
    for cell=0,1023 do
      local addr = page + cell*2
      local lo = vram_byte(vram, addr)
      local hi = vram_byte(vram, addr+1)
      local e = lo | (hi << 8)
      local d = decode_entry(e)
      lines[#lines+1] = csv_line({hex4(page), cell, cell%32, math.floor(cell/32), hex4(addr), hex4(e), d.tile, d.palette, d.priority, d.hflip, d.vflip})
    end
  end
  write_text(join(dir, "all_tilemap_pages_decoded.csv"), table.concat(lines))
end

local function dump_bg_metatile_2x2(dir, bg, vram)
  local base = bg_map_base(bg)
  local width,height = bg_dims(bg)
  local lines = {csv_line({"bg","mx","my","entry00","entry01","entry10","entry11","key_tile_pal_flip","map_base"})}
  for my=0,math.floor(height/2)-1 do
    for mx=0,math.floor(width/2)-1 do
      local tx = mx*2
      local ty = my*2
      local e00 = read_tilemap_entry(vram, base, tx, ty, width, height)
      local e01 = read_tilemap_entry(vram, base, tx+1, ty, width, height)
      local e10 = read_tilemap_entry(vram, base, tx, ty+1, width, height)
      local e11 = read_tilemap_entry(vram, base, tx+1, ty+1, width, height)
      lines[#lines+1] = csv_line({bg, mx, my, hex4(e00), hex4(e01), hex4(e10), hex4(e11), hex4(e00).."_"..hex4(e01).."_"..hex4(e10).."_"..hex4(e11), hex4(base)})
    end
  end
  write_text(join(dir, "bg"..bg.."_metatile_2x2.csv"), table.concat(lines))
end

local function dump_vram_region_hashes(dir, vram)
  local lines = {csv_line({"start","size","hash"})}
  for start=0,0xFFFF,0x400 do
    local h = 2166136261
    for i=0,0x3FF do h = fnv1a_update(h, vram_byte(vram, start+i)) end
    lines[#lines+1] = csv_line({hex4(start), hex4(0x400), hex8(h)})
  end
  write_text(join(dir, "vram_region_hashes.csv"), table.concat(lines))
end

local function dump_tile_sheet_ppm(dir, vram, cgram, bpp)
  local pal = cgram_palette(cgram)
  local tile_size = ({[2]=16,[4]=32,[8]=64})[bpp]
  if not tile_size then return end
  local tile_count = math.floor(0x10000 / tile_size)
  local cols = 32
  local rows = math.ceil(tile_count / cols)
  local w,h = cols*8, rows*8
  local pixels = {}
  for i=1,w*h do pixels[i] = {0,0,0} end
  for t=0,tile_count-1 do
    local ox = (t % cols) * 8
    local oy = math.floor(t / cols) * 8
    for y=0,7 do
      for x=0,7 do
        local ci = tile_pixel(vram, 0, t, bpp, x, y)
        local rgb = pal[ci] or {0,0,0}
        pixels[(oy+y)*w + (ox+x) + 1] = rgb
      end
    end
  end
  write_ppm(join(dir, "tiles_"..bpp.."bpp_sheet.ppm"), w, h, pixels)
end

local function dump_bg_preview_ppm(dir, bg, vram, cgram)
  local base = bg_map_base(bg)
  local cb = bg_char_base(bg)
  local width,height = bg_dims(bg)
  local bpp = bg_bpp(bg)
  if width <= 0 or height <= 0 then return end
  local pal = cgram_palette(cgram)
  local w,h = width*8, height*8
  local pixels = {}
  for i=1,w*h do pixels[i] = {0,0,0} end
  for ty=0,height-1 do
    for tx=0,width-1 do
      local e = read_tilemap_entry(vram, base, tx, ty, width, height)
      local d = decode_entry(e)
      local pal_base = 0
      if bpp == 2 then pal_base = d.palette * 4 elseif bpp == 4 then pal_base = d.palette * 16 end
      for py=0,7 do
        for px=0,7 do
          local sx = (d.hflip == 1) and (7-px) or px
          local sy = (d.vflip == 1) and (7-py) or py
          local ci = tile_pixel(vram, cb, d.tile, bpp, sx, sy)
          local rgb = {0,0,0}
          if ci ~= 0 then rgb = pal[(pal_base + ci) & 0xFF] or {0,0,0} end
          pixels[(ty*8+py)*w + (tx*8+px) + 1] = rgb
        end
      end
    end
  end
  write_ppm(join(dir, "bg"..bg.."_preview.ppm"), w, h, pixels)
end

------------------------------------------------------------
-- OAM and WRAM object helpers
------------------------------------------------------------

local function dump_oam_csv(dir, oam)
  local lines_all = {csv_line({"sprite","x","y","tile","attr","palette","priority","hflip","vflip","name_select","x_high","size_bit","raw0_x","raw1_y","raw2_tile","raw3_attr"})}
  local lines_vis = {csv_line({"sprite","x","y","tile","attr","palette","priority","hflip","vflip","size_bit"})}
  for i=0,127 do
    local base = i*4
    local xlo = oam[base + 1] or 0
    local y = oam[base + 2] or 0
    local tile = oam[base + 3] or 0
    local attr = oam[base + 4] or 0
    local hi = oam[512 + math.floor(i/4) + 1] or 0
    local pair = (hi >> ((i % 4) * 2)) & 0x03
    local xh = pair & 0x01
    local size = (pair >> 1) & 0x01
    local x = xlo + xh * 256
    if x >= 256 then x = x - 512 end
    local pal = (attr >> 1) & 0x07
    local pri = (attr >> 4) & 0x03
    local hf = (attr >> 6) & 0x01
    local vf = (attr >> 7) & 0x01
    local ns = attr & 0x01
    lines_all[#lines_all+1] = csv_line({i,x,y,tile,hex2(attr),pal,pri,hf,vf,ns,xh,size,hex2(xlo),hex2(y),hex2(tile),hex2(attr)})
    if not (y == 0xE0 and xlo == 0 and tile == 0 and attr == 0) then
      lines_vis[#lines_vis+1] = csv_line({i,x,y,tile,hex2(attr),pal,pri,hf,vf,size})
    end
  end
  write_text(join(dir, "oam_sprites.csv"), table.concat(lines_all))
  write_text(join(dir, "oam_visible.csv"), table.concat(lines_vis))
end

local function dump_object_slots(dir)
  local lines = {csv_line({"slot","next_0A61","prev_0A1F","sort_0AA3","field_0B25","field_0AE5","field_0E27","field_0BA5","field_0C65","field_0EA7","field_0B27","field_0E67"})}
  for slot=0,0x7F do
    lines[#lines+1] = csv_line({
      hex2(slot), hex2(wram_read(0x0A61+slot)), hex2(wram_read(0x0A1F+slot)), hex2(wram_read(0x0AA3+slot)),
      hex2(wram_read(0x0B25+slot)), hex2(wram_read(0x0AE5+slot)), hex2(wram_read(0x0E27+slot)),
      hex2(wram_read(0x0BA5+slot)), hex2(wram_read(0x0C65+slot)), hex2(wram_read(0x0EA7+slot)),
      hex2(wram_read(0x0B27+slot)), hex2(wram_read(0x0E67+slot))
    })
  end
  write_text(join(dir, "object_slots_0x00_0x7f.csv"), table.concat(lines))
end

local function dump_active_chain_guess(dir)
  local lines = {csv_line({"step","slot","next","prev","sort","field_0B25","field_0AE5","x_0BA5","y_0C65","anim_0E27"})}
  local head = wram_read(0x0A61)
  local slot = head
  local seen = {}
  local step = 0
  while slot ~= 0 and slot < 0x80 and step < MAX_ACTIVE_CHAIN and not seen[slot] do
    seen[slot] = true
    lines[#lines+1] = csv_line({step, hex2(slot), hex2(wram_read(0x0A61+slot)), hex2(wram_read(0x0A1F+slot)), hex2(wram_read(0x0AA3+slot)), hex2(wram_read(0x0B25+slot)), hex2(wram_read(0x0AE5+slot)), hex2(wram_read(0x0BA5+slot)), hex2(wram_read(0x0C65+slot)), hex2(wram_read(0x0E27+slot))})
    slot = wram_read(0x0A61+slot)
    step = step + 1
  end
  write_text(join(dir, "object_active_chain_guess.csv"), table.concat(lines))
end

local WATCH = {
  {"phase_1F9D",0x1F9D,2},{"subfunc_1FAA",0x1FAA,4},{"item_id_1923",0x1923,2},{"char_id_193B",0x193B,2},
  {"logical_actor_1569",0x1569,0x40},{"script_stage_1958",0x1958,0x50},{"display_stack_7189",0x7189,0x20},
  {"asset_stage_390B",0x390B,0x100},{"dma_queue_8000",0x8000,0x80},{"oam_mirror_0EE9",0x0EE9,0x220},
  {"object_head_0A61",0x0A61,0x20},{"object_prev_0A1F",0x0A1F,0x20},{"object_sort_0AA3",0x0AA3,0x20}
}

local function dump_wram_watch_values(dir)
  local lines = {csv_line({"name","addr","len","hash","bytes_hex_prefix"})}
  for _,w in ipairs(WATCH) do
    local name,addr,len = w[1],w[2],w[3]
    local h = 2166136261
    local prefix = {}
    for i=0,len-1 do
      local v = wram_read(addr+i)
      h = fnv1a_update(h, v)
      if i < 64 then prefix[#prefix+1] = hex2(v) end
    end
    lines[#lines+1] = csv_line({name, hex4(addr), len, hex8(h), table.concat(prefix," ")})
  end
  write_text(join(dir, "wram_watch_values.csv"), table.concat(lines))
end

local function dump_wram_ranges(dir)
  if not DUMP_WRAM_RANGES then return end
  write_bin(join(dir, "wram_0000_1fff.bin"), read_wram_range(0x0000, 0x2000))
  write_bin(join(dir, "wram_3900_03ff.bin"), read_wram_range(0x3900, 0x0400))
  write_bin(join(dir, "wram_7000_0200.bin"), read_wram_range(0x7000, 0x0200))
  write_bin(join(dir, "wram_dma_queue_8000_0800.bin"), read_wram_range(0x8000, 0x0800))
  write_bin(join(dir, "wram_oam_mirror_0ee9_0220.bin"), read_wram_range(0x0EE9, 0x0220))
end

------------------------------------------------------------
-- Snapshot
------------------------------------------------------------

local function ppu_signature()
  local keys = {0x2100,0x2101,0x2105,0x2107,0x2108,0x2109,0x210A,0x210B,0x210C,0x212C,0x212D,0x2130,0x2131,0x2132,0x2133,0x420B,0x420C}
  local t = {}
  for _,a in ipairs(keys) do t[#t+1] = hex2(ppu[a]) end
  return table.concat(t, ":")
end

local last_ppu_sig = ""
local last_dump_frame = -999999
local dump_index = 0

local function dump_snapshot(reason)
  local f = current_frame()
  local dir = join(OUT_DIR, string.format("frame_%06d", f))
  ensure_dir(dir)
  dump_index = dump_index + 1

  local vram = read_domain_bytes(VRAM_DOMAIN, 0, 0x10000)
  local cgram = read_domain_bytes(CGRAM_DOMAIN, 0, 0x200)
  local oam = read_domain_bytes(OAM_DOMAIN, 0, 0x220)

  local vh = simple_hash(vram)
  local ch = simple_hash(cgram)
  local oh = simple_hash(oam)
  local sig = ppu_signature()

  write_text(join(dir, "frame_info.csv"), csv_line({"key","value"}) ..
    csv_line({"frame", f}) ..
    csv_line({"dump_index", dump_index}) ..
    csv_line({"reason", reason}) ..
    csv_line({"vram_domain", VRAM_DOMAIN or ""}) ..
    csv_line({"cgram_domain", CGRAM_DOMAIN or ""}) ..
    csv_line({"oam_domain", OAM_DOMAIN or ""}) ..
    csv_line({"wram_domain", WRAM_DOMAIN or ""}) ..
    csv_line({"bus_domain", BUS_DOMAIN or ""}) ..
    csv_line({"vram_hash", hex8(vh)}) ..
    csv_line({"cgram_hash", hex8(ch)}) ..
    csv_line({"oam_hash", hex8(oh)}) ..
    csv_line({"ppu_signature", sig}) ..
    csv_line({"note", "PPU regs are write mirrors after Lua start; start Lua before entering target scene for best accuracy."})
  )

  if DUMP_RAW_BINS then
    if #vram > 0 then write_bin(join(dir, "vram.bin"), vram) end
    if #cgram > 0 then write_bin(join(dir, "cgram.bin"), cgram) end
    if #oam > 0 then write_bin(join(dir, "oam.bin"), oam) end
  end

  dump_ppu_regs(dir)
  dump_wram_watch_values(dir)
  dump_wram_ranges(dir)

  if #cgram > 0 then dump_cgram_palette_csv(dir, cgram) end
  if #vram > 0 then
    dump_bg_summary(dir)
    dump_vram_region_hashes(dir, vram)
    for bg=1,4 do
      dump_bg_tilemap_csv(dir, bg, vram)
      dump_bg_metatile_2x2(dir, bg, vram)
    end
    if DUMP_ALL_TILEMAP_PAGES then dump_all_tilemap_pages(dir, vram) end
    if DUMP_FULL_TILE_SHEETS and #cgram > 0 then
      dump_tile_sheet_ppm(dir, vram, cgram, 2)
      dump_tile_sheet_ppm(dir, vram, cgram, 4)
      dump_tile_sheet_ppm(dir, vram, cgram, 8)
    end
    if DUMP_BG_PREVIEWS and #cgram > 0 then
      for bg=1,4 do dump_bg_preview_ppm(dir, bg, vram, cgram) end
    end
  else
    append_text(notes_path, "WARN frame "..f..": VRAM domain not available.\n")
  end

  if #oam > 0 then dump_oam_csv(dir, oam) else append_text(notes_path, "WARN frame "..f..": OAM domain not available.\n") end
  if DUMP_OBJECT_SLOTS then
    dump_object_slots(dir)
    dump_active_chain_guess(dir)
  end

  append_text(manifest_path, csv_line({dump_index, f, reason, dir, hex8(vh), hex8(ch), hex8(oh), sig}))
  last_dump_frame = f
  log("shinmomo graphics full snapshot: frame="..f.." reason="..reason.." dir="..dir)
end

------------------------------------------------------------
-- Main loop
------------------------------------------------------------

local function init_output()
  ensure_dir(OUT_DIR)
  write_text(notes_path,
    "TRACE_SHINMOMO_GRAPHICS_FULL_CAPTURE_V2_READY\n" ..
    "This Lua captures VRAM/CGRAM/OAM/PPU/DMA/BG tilemap/WRAM candidates for graphics restoration.\n" ..
    "Domains: " .. table.concat(DOMAINS, ",") .. "\n" ..
    "Chosen BUS="..tostring(BUS_DOMAIN).." WRAM="..tostring(WRAM_DOMAIN).." VRAM="..tostring(VRAM_DOMAIN).." CGRAM="..tostring(CGRAM_DOMAIN).." OAM="..tostring(OAM_DOMAIN).."\n" ..
    "Important: PPU registers are write-only; this script mirrors writes after launch. Start before entering target scenes.\n"
  )
  write_text(ppu_write_log_path, csv_line({"frame","addr","name","value"}))
  write_text(vram_write_log_path, csv_line({"frame","addr","name","value","vmain","vmadd_l","vmadd_h"}))
  write_text(cgram_write_log_path, csv_line({"frame","addr","value","cgadd"}))
  write_text(dma_log_path, csv_line({"frame","trigger_addr","mask","channel","DMAP","BBAD","A1T","A1B","DAS","DASB","source_long","ppu_target"}))
  write_text(manifest_path, csv_line({"dump_index","frame","reason","dir","vram_hash","cgram_hash","oam_hash","ppu_signature"}))
end

local function tick()
  local f = current_frame()
  if f % HEARTBEAT_EVERY_FRAMES == 0 then
    log("TRACE_SHINMOMO_GRAPHICS_FULL_CAPTURE_V2_ALIVE frame="..f.." ppu="..ppu_signature())
  end

  local sig = ppu_signature()
  if DUMP_ON_PPU_SIG_CHANGE and sig ~= last_ppu_sig and (f - last_dump_frame) >= PPU_CHANGE_COOLDOWN_FRAMES then
    last_ppu_sig = sig
    dump_snapshot("ppu_signature_changed")
    return
  end
  last_ppu_sig = sig

  if f == 1 or (DUMP_EVERY_FRAMES > 0 and f % DUMP_EVERY_FRAMES == 0) then
    dump_snapshot("periodic")
  end
end

init_output()
install_write_hooks()
dump_snapshot("startup")

if event and event.onframestart then
  event.onframestart(tick, "shinmomo_graphics_full_capture_v2")
elseif emu and emu.frameadvance then
  while true do
    tick()
    emu.frameadvance()
  end
else
  log("WARN: no frame callback API found. One startup snapshot has been dumped only.")
end
