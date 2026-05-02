-- shinmomo_graphics_mapchip_probe_v2_bizhawk_snes9x_20260501.lua
-- v2 changes:
--   * fixes ppu_reg_name scoping bug in v1
--   * adds DMA source -> inferred ROM offset mapping
--   * adds frame_summary.csv for scene comparison
--   * adds BG used tile histogram for mapchip reconstruction
--   * adds WRAM visible-object linked-list snapshot ($0A61/$0A1F/$0AA3/$0B25...)
--   * keeps v1 outputs compatible
-- 新桃太郎伝説 グラフィック/マップチップ復元用プローブ v1
--
-- 目的:
--   VRAM / CGRAM / OAM / PPU register writes / DMA trigger / BG tilemap / tile sheet preview をまとめて採取し、
--   グラフィック・マップチップ復元の足場を作る。
--
-- 想定:
--   BizHawk系 Lua API（memory.read_u8, memory.getmemorydomainlist, event.onmemorywrite, emu.frameadvance）
--   既存shinmomo Luaと同系統の環境を想定。
--
-- 出力:
--   shinmomo_graphics_probe_out/
--     manifest.csv
--     ppu_write_log.csv
--     dma_trigger_log.csv
--     frame_000000/
--       vram.bin
--       cgram.bin
--       oam.bin
--       ppu_regs_capture.csv
--       bg_summary.csv
--       bg1_tilemap.csv ... bg4_tilemap.csv
--       bg1_map_preview.ppm ... bg4_map_preview.ppm
--       tiles_2bpp_sheet.ppm
--       tiles_4bpp_sheet.ppm
--       tiles_8bpp_sheet.ppm
--
-- 使い方:
--   1. ROM起動後、このLuaを実行
--   2. タイトル、フィールド、町、戦闘、メニューなど画面を切り替える
--   3. DUMP_EVERY_FRAMES間隔、またはPPU/BG設定変化時にsnapshotが作られる
--   4. PPMはGIMP/IrfanView等で開ける。CSVとbinを併用して復元する

------------------------------------------------------------
-- Config
------------------------------------------------------------

local OUT_DIR = "shinmomo_graphics_probe_out_v2"
local DUMP_EVERY_FRAMES = 300        -- 5秒相当（60fps）。増やすと軽い
local HEARTBEAT_EVERY_FRAMES = 60
local DUMP_FULL_TILE_SHEETS = true
local DUMP_BG_PREVIEWS = true
local DUMP_RAW_BINS = true
local MAX_DMA_LOG_LINES_PER_FRAME = 64

-- 手動で場面名を変えてから実行すると、manifest/frame_summaryに残る。
-- 例: "town_start", "field_world", "battle_normal"
local SCENE_LABEL = "town"

-- $0A61 active linked listを追う最大数。重い場合は 0。
local DUMP_VISIBLE_OBJECTS = true
local MAX_VISIBLE_OBJECT_SLOTS = 64

-- BG previewが重い時は false
local ENABLE_REGISTER_WRITE_HOOKS = true

------------------------------------------------------------
-- Small utilities
------------------------------------------------------------

local function log(s)
  if console and console.log then console.log(s) else print(s) end
end

local function hex2(v) return string.format("%02X", (v or 0) & 0xFF) end
local function hex4(v) return string.format("%04X", (v or 0) & 0xFFFF) end
local function hex6(v) return string.format("%06X", (v or 0) & 0xFFFFFF) end

local function path_sep()
  if package and package.config then return package.config:sub(1,1) end
  return "/"
end

local SEP = path_sep()

local function join(a, b)
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
  f:write(text)
  f:close()
end

local function append_text(path, text)
  local f = io.open(path, "a")
  if not f then
    f = assert(io.open(path, "w"))
  end
  f:write(text)
  f:close()
end

local function write_bin(path, bytes)
  local f = assert(io.open(path, "wb"))
  for i = 1, #bytes do
    f:write(string.char(bytes[i] & 0xFF))
  end
  f:close()
end

local function csv_escape(s)
  s = tostring(s or "")
  if s:find("[,\n\"]") then
    s = '"' .. s:gsub('"', '""') .. '"'
  end
  return s
end

local function csv_line(t)
  local out = {}
  for i, v in ipairs(t) do out[#out+1] = csv_escape(v) end
  return table.concat(out, ",") .. "\n"
end

------------------------------------------------------------
-- Memory domain detection
------------------------------------------------------------

local function get_domains()
  local ok, domains = pcall(memory.getmemorydomainlist)
  if ok and domains then return domains end
  return {}
end

local DOMAINS = get_domains()

local function find_domain(candidates)
  for _, want in ipairs(candidates) do
    for _, got in ipairs(DOMAINS) do
      if got == want then return got end
    end
  end
  -- case-insensitive contains fallback
  for _, want in ipairs(candidates) do
    local lw = want:lower()
    for _, got in ipairs(DOMAINS) do
      if got:lower():find(lw, 1, true) then return got end
    end
  end
  return nil
end

local BUS_DOMAIN   = find_domain({"System Bus", "Bus", "Snes Bus", "SNES Bus"})
local WRAM_DOMAIN  = find_domain({"WRAM", "Snes WRAM", "SNES WRAM", "Main RAM", "System Bus"})
local VRAM_DOMAIN  = find_domain({"VRAM", "Snes VRAM", "SNES VRAM"})
local CGRAM_DOMAIN = find_domain({"CGRAM", "Snes CGRAM", "SNES CGRAM", "CRAM"})
local OAM_DOMAIN   = find_domain({"OAM", "Snes OAM", "SNES OAM", "Sprite RAM"})

local function safe_read_u8(addr, domain)
  if not domain then return 0 end
  local ok, v = pcall(memory.read_u8, addr, domain)
  if ok and v ~= nil then return v & 0xFF end
  return 0
end

local function bus_read(addr)
  if BUS_DOMAIN then return safe_read_u8(addr, BUS_DOMAIN) end
  return safe_read_u8(addr, "System Bus")
end

local function read_domain_bytes(domain, size)
  local t = {}
  if not domain then return t end
  for i = 0, size - 1 do
    t[#t+1] = safe_read_u8(i, domain)
  end
  return t
end

local function simple_hash(bytes)
  local h = 2166136261
  for i = 1, #bytes do
    h = (h ~ bytes[i]) & 0xFFFFFFFF
    h = (h * 16777619) & 0xFFFFFFFF
  end
  return h
end

------------------------------------------------------------
-- PPU register capture
------------------------------------------------------------

-- PPU write-only regs cannot reliably be polled. We mirror writes here.
local ppu = {}
for a = 0x2100, 0x213F do ppu[a] = 0 end
for a = 0x4200, 0x421F do ppu[a] = 0 end
for a = 0x4300, 0x437F do ppu[a] = 0 end

local ppu_write_log_path = join(OUT_DIR, "ppu_write_log.csv")
local dma_log_path = join(OUT_DIR, "dma_trigger_log.csv")
local manifest_path = join(OUT_DIR, "manifest.csv")
local frame_summary_path = join(OUT_DIR, "frame_summary.csv")
local object_summary_path = join(OUT_DIR, "visible_object_summary.csv")

local ppu_reg_name

local function current_frame()
  if emu and emu.framecount then return emu.framecount() end
  return 0
end

local function record_ppu_write(addr, value)
  ppu[addr] = value & 0xFF
  append_text(ppu_write_log_path, csv_line({
    current_frame(), hex4(addr), hex2(value), ppu_reg_name(addr)
  }))
end

ppu_reg_name = function(addr)
  local names = {
    [0x2100]="INIDISP", [0x2101]="OBSEL", [0x2102]="OAMADDL", [0x2103]="OAMADDH", [0x2104]="OAMDATA",
    [0x2105]="BGMODE", [0x2106]="MOSAIC", [0x2107]="BG1SC", [0x2108]="BG2SC", [0x2109]="BG3SC", [0x210A]="BG4SC",
    [0x210B]="BG12NBA", [0x210C]="BG34NBA", [0x210D]="BG1HOFS", [0x210E]="BG1VOFS", [0x210F]="BG2HOFS", [0x2110]="BG2VOFS",
    [0x2111]="BG3HOFS", [0x2112]="BG3VOFS", [0x2113]="BG4HOFS", [0x2114]="BG4VOFS", [0x2115]="VMAIN",
    [0x2116]="VMADDL", [0x2117]="VMADDH", [0x2118]="VMDATAL", [0x2119]="VMDATAH", [0x211A]="M7SEL",
    [0x2121]="CGADD", [0x2122]="CGDATA", [0x212C]="TM", [0x212D]="TS", [0x2130]="CGWSEL", [0x2131]="CGADSUB",
    [0x420B]="MDMAEN", [0x420C]="HDMAEN"
  }
  if names[addr] then return names[addr] end
  if addr >= 0x4300 and addr <= 0x437F then
    local ch = math.floor((addr - 0x4300) / 0x10)
    local off = (addr - 0x4300) & 0x0F
    local n = {"DMAP","BBAD","A1T_L","A1T_H","A1B","DAS_L","DAS_H","DASB","A2A_L","A2A_H","NLTR","UNUSED","UNUSED","UNUSED","UNUSED","UNUSED"}
    return "DMA" .. ch .. "_" .. (n[off+1] or hex2(off))
  end
  return ""
end

local function read_dma_channel(ch)
  local b = 0x4300 + ch * 0x10
  local dmap = ppu[b+0]
  local bbad = ppu[b+1]
  local src = ppu[b+2] + ppu[b+3] * 0x100 + ppu[b+4] * 0x10000
  local size = ppu[b+5] + ppu[b+6] * 0x100
  if size == 0 then size = 0x10000 end
  return dmap, bbad, src, size
end

local function dma_target_label(bbad)
  if bbad == 0x04 then return "OAMDATA_2104" end
  if bbad == 0x18 then return "VRAM_2118" end
  if bbad == 0x19 then return "VRAM_2119" end
  if bbad == 0x22 then return "CGRAM_2122" end
  return "PPU_21" .. hex2(bbad)
end

local function snes_source_to_rom_offset(src)
  local bank = (src >> 16) & 0xFF
  local addr = src & 0xFFFF

  -- 新桃はヘッダ上 0x31 系で、実解析上は C0:0000 が raw 0x000000 に対応する線が強い。
  -- C0-DF / 80-9F を linear HiROM-like mirror として推定する。
  if bank >= 0xC0 and bank <= 0xDF then
    return (bank - 0xC0) * 0x10000 + addr, "hirom_c0_linear"
  end
  if bank >= 0x80 and bank <= 0x9F then
    return (bank - 0x80) * 0x10000 + addr, "hirom_80_mirror"
  end

  -- LoROM風に見えるDMA sourceが出た場合の参考値。
  if addr >= 0x8000 and (bank >= 0x80 and bank <= 0xFF) then
    local b = bank & 0x7F
    return b * 0x8000 + (addr - 0x8000), "lorom_guess"
  end

  return -1, "wram_or_unknown"
end

local function record_dma_trigger(value)
  local f = current_frame()
  for ch = 0, 7 do
    if (value & (1 << ch)) ~= 0 then
      local dmap, bbad, src, size = read_dma_channel(ch)
      local romoff, mapguess = snes_source_to_rom_offset(src)
      local vram_word = (ppu[0x2116] or 0) + (ppu[0x2117] or 0) * 0x100
      append_text(dma_log_path, csv_line({
        f, ch, hex2(dmap), hex2(bbad), dma_target_label(bbad), hex6(src),
        romoff >= 0 and hex6(romoff) or "", mapguess, size,
        hex2(ppu[0x2115]), hex2(ppu[0x2116]), hex2(ppu[0x2117]),
        hex4(vram_word), hex4(vram_word * 2), hex2(ppu[0x2121]),
        "MDMAEN", SCENE_LABEL
      }))
    end
  end
end

local function register_write_hook(addr)
  if event and event.onmemorywrite then
    local ok = pcall(event.onmemorywrite, function(a, v)
      record_ppu_write(addr, v)
      if addr == 0x420B then record_dma_trigger(v) end
    end, addr, "shinmomo_gfx_probe_" .. hex4(addr), BUS_DOMAIN or "System Bus")
    if ok then return true end
  end
  if memory and memory.registerwrite then
    local ok = pcall(memory.registerwrite, addr, function(a, v)
      record_ppu_write(addr, v)
      if addr == 0x420B then record_dma_trigger(v) end
    end)
    if ok then return true end
    ok = pcall(memory.registerwrite, addr, 1, function(a, v)
      record_ppu_write(addr, v)
      if addr == 0x420B then record_dma_trigger(v) end
    end)
    if ok then return true end
  end
  return false
end

local function setup_hooks()
  if not ENABLE_REGISTER_WRITE_HOOKS then return 0 end
  local count = 0
  for a = 0x2100, 0x213F do if register_write_hook(a) then count = count + 1 end end
  for a = 0x4200, 0x421F do if register_write_hook(a) then count = count + 1 end end
  for a = 0x4300, 0x437F do if register_write_hook(a) then count = count + 1 end end
  return count
end

------------------------------------------------------------
-- CGRAM palette
------------------------------------------------------------

local function snes_color_to_rgb(lo, hi)
  local v = lo + hi * 0x100
  local r = (v & 0x1F)
  local g = (v >> 5) & 0x1F
  local b = (v >> 10) & 0x1F
  return math.floor(r * 255 / 31), math.floor(g * 255 / 31), math.floor(b * 255 / 31)
end

local function cgram_palette(cgram)
  local pal = {}
  for i = 0, 255 do
    local lo = cgram[i*2 + 1] or 0
    local hi = cgram[i*2 + 2] or 0
    local r, g, b = snes_color_to_rgb(lo, hi)
    pal[i] = {r,g,b}
  end
  return pal
end

------------------------------------------------------------
-- SNES tile decode and previews
------------------------------------------------------------

local function vram_byte(vram, addr)
  addr = (addr % 0x10000) + 1
  return vram[addr] or 0
end

local function tile_pixel(vram, base, tile_num, bpp, x, y)
  local tile_size = ({[2]=16, [4]=32, [8]=64})[bpp] or 32
  local addr = base + tile_num * tile_size
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
  for i = 1, width * height do
    local p = pixels[i] or {0,0,0}
    f:write(string.char(p[1] & 0xFF, p[2] & 0xFF, p[3] & 0xFF))
  end
  f:close()
end

local function dump_tile_sheet_ppm(dir, vram, cgram, bpp)
  local pal = cgram_palette(cgram)
  local tile_size = ({[2]=16, [4]=32, [8]=64})[bpp]
  local tile_count = math.floor(0x10000 / tile_size)
  local cols = 32
  local rows = math.ceil(tile_count / cols)
  local w = cols * 8
  local h = rows * 8
  local pixels = {}
  for i = 1, w*h do pixels[i] = {0,0,0} end

  for t = 0, tile_count - 1 do
    local tx = (t % cols) * 8
    local ty = math.floor(t / cols) * 8
    for y = 0, 7 do
      for x = 0, 7 do
        local ci = tile_pixel(vram, 0, t, bpp, x, y)
        local rgb = pal[ci] or {0,0,0}
        pixels[(ty+y)*w + (tx+x) + 1] = rgb
      end
    end
  end

  write_ppm(join(dir, "tiles_" .. bpp .. "bpp_sheet.ppm"), w, h, pixels)
end

------------------------------------------------------------
-- BG mode / map helpers
------------------------------------------------------------

local function bgmode()
  return ppu[0x2105] & 0x07
end

local function bg_bpp(bg)
  local m = bgmode()
  if m == 0 then return 2 end
  if m == 1 then
    if bg == 3 then return 2 else return 4 end
  end
  if m == 2 then return 4 end
  if m == 3 then
    if bg == 1 then return 8 else return 4 end
  end
  if m == 4 then
    if bg == 1 then return 8 else return 2 end
  end
  if m == 5 then
    if bg == 1 then return 4 else return 2 end
  end
  if m == 6 then return 4 end
  if m == 7 then return 8 end
  return 4
end

local function bg_sc_reg(bg)
  return ppu[0x2106 + bg] or 0
end

local function bg_map_base(bg)
  local r = bg_sc_reg(bg)
  return (r & 0xFC) << 8
end

local function bg_map_size_code(bg)
  return bg_sc_reg(bg) & 0x03
end

local function bg_dims(bg)
  local s = bg_map_size_code(bg)
  if s == 0 then return 32,32 end
  if s == 1 then return 64,32 end
  if s == 2 then return 32,64 end
  return 64,64
end

local function bg_char_base(bg)
  if bg <= 2 then
    local r = ppu[0x210B] or 0
    local nib = (bg == 1) and (r & 0x0F) or ((r >> 4) & 0x0F)
    return nib << 12
  else
    local r = ppu[0x210C] or 0
    local nib = (bg == 3) and (r & 0x0F) or ((r >> 4) & 0x0F)
    return nib << 12
  end
end

local function tilemap_entry_addr(base, tx, ty, width, height)
  local screen_x = math.floor(tx / 32)
  local screen_y = math.floor(ty / 32)
  local inner_x = tx % 32
  local inner_y = ty % 32

  local screen_index = 0
  if width == 64 and height == 32 then
    screen_index = screen_x
  elseif width == 32 and height == 64 then
    screen_index = screen_y
  elseif width == 64 and height == 64 then
    screen_index = screen_y * 2 + screen_x
  end

  return base + screen_index * 0x800 + (inner_y * 32 + inner_x) * 2
end

local function read_tilemap_entry(vram, base, tx, ty, width, height)
  local a = tilemap_entry_addr(base, tx, ty, width, height)
  local lo = vram_byte(vram, a)
  local hi = vram_byte(vram, a + 1)
  return lo + hi * 0x100, a
end

local function dump_bg_tilemap_csv(dir, bg, vram)
  local base = bg_map_base(bg)
  local cb = bg_char_base(bg)
  local width, height = bg_dims(bg)
  local path = join(dir, "bg" .. bg .. "_tilemap.csv")
  local lines = {}
  lines[#lines+1] = csv_line({
    "bg","tx","ty","vram_addr","entry_hex","tile","palette","priority","hflip","vflip",
    "map_base","char_base","bpp","mode"
  })
  for ty = 0, height - 1 do
    for tx = 0, width - 1 do
      local e, addr = read_tilemap_entry(vram, base, tx, ty, width, height)
      local tile = e & 0x03FF
      local pal = (e >> 10) & 0x07
      local pri = (e >> 13) & 0x01
      local hf = (e >> 14) & 0x01
      local vf = (e >> 15) & 0x01
      lines[#lines+1] = csv_line({
        bg, tx, ty, hex4(addr), hex4(e), tile, pal, pri, hf, vf,
        hex4(base), hex4(cb), bg_bpp(bg), bgmode()
      })
    end
  end
  write_text(path, table.concat(lines))
end


local function dump_bg_tile_usage_csv(dir, bg, vram)
  local base = bg_map_base(bg)
  local cb = bg_char_base(bg)
  local width, height = bg_dims(bg)
  local counts = {}
  local attrs = {}
  for ty = 0, height - 1 do
    for tx = 0, width - 1 do
      local e = read_tilemap_entry(vram, base, tx, ty, width, height)
      local tile = e & 0x03FF
      local pal = (e >> 10) & 0x07
      local pri = (e >> 13) & 0x01
      local hf = (e >> 14) & 0x01
      local vf = (e >> 15) & 0x01
      counts[tile] = (counts[tile] or 0) + 1
      attrs[tile] = attrs[tile] or {}
      local k = "p" .. pal .. "_r" .. pri .. "_h" .. hf .. "_v" .. vf
      attrs[tile][k] = (attrs[tile][k] or 0) + 1
    end
  end

  local lines = {}
  lines[#lines+1] = csv_line({"bg","tile","count","attr_variants","map_base","char_base","bpp","mode","scene_label"})
  for tile, count in pairs(counts) do
    local av = {}
    for k, c in pairs(attrs[tile]) do av[#av+1] = k .. ":" .. c end
    table.sort(av)
    lines[#lines+1] = csv_line({bg, tile, count, table.concat(av, " "), hex4(base), hex4(cb), bg_bpp(bg), bgmode(), SCENE_LABEL})
  end
  write_text(join(dir, "bg" .. bg .. "_tile_usage.csv"), table.concat(lines))
end

local function dump_bg_preview_ppm(dir, bg, vram, cgram)
  local base = bg_map_base(bg)
  local cb = bg_char_base(bg)
  local width, height = bg_dims(bg)
  local bpp = bg_bpp(bg)
  local pal = cgram_palette(cgram)
  local w = width * 8
  local h = height * 8
  local pixels = {}
  for i = 1, w*h do pixels[i] = {0,0,0} end

  for ty = 0, height - 1 do
    for tx = 0, width - 1 do
      local e = read_tilemap_entry(vram, base, tx, ty, width, height)
      local tile = e & 0x03FF
      local palno = (e >> 10) & 0x07
      local hf = ((e >> 14) & 1) ~= 0
      local vf = ((e >> 15) & 1) ~= 0
      local pal_base = 0
      if bpp == 2 then pal_base = palno * 4
      elseif bpp == 4 then pal_base = palno * 16
      else pal_base = 0 end

      for py = 0, 7 do
        for px = 0, 7 do
          local sx = hf and (7 - px) or px
          local sy = vf and (7 - py) or py
          local ci = tile_pixel(vram, cb, tile, bpp, sx, sy)
          local rgb = {0,0,0}
          if ci ~= 0 then rgb = pal[(pal_base + ci) & 0xFF] or {0,0,0} end
          local x = tx*8 + px
          local y = ty*8 + py
          pixels[y*w + x + 1] = rgb
        end
      end
    end
  end

  write_ppm(join(dir, "bg" .. bg .. "_map_preview.ppm"), w, h, pixels)
end

------------------------------------------------------------
-- OAM dump
------------------------------------------------------------

local function dump_oam_csv(dir, oam)
  local lines = {}
  lines[#lines+1] = csv_line({
    "sprite","x","y","tile","attr","palette","priority","hflip","vflip","x_high","size_bit"
  })
  for i = 0, 127 do
    local base = i * 4
    local xlo = oam[base + 1] or 0
    local y = oam[base + 2] or 0
    local tile = oam[base + 3] or 0
    local attr = oam[base + 4] or 0
    local hi_byte = oam[512 + math.floor(i / 4) + 1] or 0
    local pair = (hi_byte >> ((i % 4) * 2)) & 0x03
    local x_high = pair & 0x01
    local size_bit = (pair >> 1) & 0x01
    local x = xlo + x_high * 256
    if x >= 256 then x = x - 512 end
    lines[#lines+1] = csv_line({
      i, x, y, tile, hex2(attr), (attr >> 1) & 0x07, (attr >> 4) & 0x03,
      (attr >> 6) & 0x01, (attr >> 7) & 0x01, x_high, size_bit
    })
  end
  write_text(join(dir, "oam_sprites.csv"), table.concat(lines))
end


------------------------------------------------------------
-- Visible object / map object linked-list dump
------------------------------------------------------------

local function wram_read(addr)
  if WRAM_DOMAIN and WRAM_DOMAIN ~= BUS_DOMAIN then
    return safe_read_u8(addr, WRAM_DOMAIN)
  end
  if BUS_DOMAIN then
    return bus_read(0x7E0000 + addr)
  end
  return safe_read_u8(addr, WRAM_DOMAIN)
end

local function dump_visible_objects_csv(dir)
  if not DUMP_VISIBLE_OBJECTS then return 0, "" end
  local lines = {}
  lines[#lines+1] = csv_line({
    "scene_label","frame","slot","next_0A61","prev_0A1F","sort_0AA3",
    "xlo_0DA5","xhi_0DE5","ylo_0D25","yhi_0D65","type_0B25",
    "attr_0AE5","state_0E27","raw0C65","raw0BA5"
  })

  local head = wram_read(0x0A61)
  local seen = {}
  local slot = head
  local count = 0
  local safety = 0
  while slot ~= 0 and slot ~= 0xFF and safety < MAX_VISIBLE_OBJECT_SLOTS do
    safety = safety + 1
    if seen[slot] then break end
    seen[slot] = true
    count = count + 1
    local nx = wram_read(0x0A61 + slot)
    local pv = wram_read(0x0A1F + slot)
    local sort = wram_read(0x0AA3 + slot)
    lines[#lines+1] = csv_line({
      SCENE_LABEL, current_frame(), slot, nx, pv, hex2(sort),
      hex2(wram_read(0x0DA5 + slot)), hex2(wram_read(0x0DE5 + slot)),
      hex2(wram_read(0x0D25 + slot)), hex2(wram_read(0x0D65 + slot)),
      hex2(wram_read(0x0B25 + slot)), hex2(wram_read(0x0AE5 + slot)),
      hex2(wram_read(0x0E27 + slot)), hex2(wram_read(0x0C65 + slot)),
      hex2(wram_read(0x0BA5 + slot))
    })
    slot = nx
  end
  write_text(join(dir, "visible_objects.csv"), table.concat(lines))
  return count, hex2(head)
end

------------------------------------------------------------
-- Snapshot
------------------------------------------------------------

local last_vram_hash = nil
local last_cgram_hash = nil
local last_ppu_sig = ""

local function ppu_signature()
  return table.concat({
    hex2(ppu[0x2100]), hex2(ppu[0x2101]), hex2(ppu[0x2105]), hex2(ppu[0x2107]),
    hex2(ppu[0x2108]), hex2(ppu[0x2109]), hex2(ppu[0x210A]), hex2(ppu[0x210B]),
    hex2(ppu[0x210C]), hex2(ppu[0x212C]), hex2(ppu[0x212D])
  }, ":")
end

local function dump_ppu_regs(dir)
  local lines = {}
  lines[#lines+1] = csv_line({"addr","name","value"})
  for a = 0x2100, 0x213F do
    lines[#lines+1] = csv_line({hex4(a), ppu_reg_name(a), hex2(ppu[a])})
  end
  for a = 0x4200, 0x421F do
    lines[#lines+1] = csv_line({hex4(a), ppu_reg_name(a), hex2(ppu[a])})
  end
  for a = 0x4300, 0x437F do
    if ppu[a] ~= 0 then
      lines[#lines+1] = csv_line({hex4(a), ppu_reg_name(a), hex2(ppu[a])})
    end
  end
  write_text(join(dir, "ppu_regs_capture.csv"), table.concat(lines))
end

local function dump_bg_summary(dir)
  local lines = {}
  lines[#lines+1] = csv_line({
    "frame","mode","bg","sc_reg","map_base","size_code","width_tiles","height_tiles","char_base","bpp",
    "tm_main_screen","ts_sub_screen"
  })
  for bg = 1, 4 do
    local w,h = bg_dims(bg)
    lines[#lines+1] = csv_line({
      current_frame(), bgmode(), bg, hex2(bg_sc_reg(bg)), hex4(bg_map_base(bg)),
      bg_map_size_code(bg), w, h, hex4(bg_char_base(bg)), bg_bpp(bg),
      hex2(ppu[0x212C]), hex2(ppu[0x212D])
    })
  end
  write_text(join(dir, "bg_summary.csv"), table.concat(lines))
end

local function dump_snapshot(reason)
  local f = current_frame()
  local dir = join(OUT_DIR, string.format("frame_%06d", f))
  ensure_dir(dir)

  local vram = read_domain_bytes(VRAM_DOMAIN, 0x10000)
  local cgram = read_domain_bytes(CGRAM_DOMAIN, 0x200)
  local oam = read_domain_bytes(OAM_DOMAIN, 0x220)

  if #vram == 0 then log("WARN: VRAM domain not found; raw/preview dump skipped.") end
  if #cgram == 0 then log("WARN: CGRAM domain not found; palette dump skipped.") end
  if #oam == 0 then log("WARN: OAM domain not found; sprite dump skipped.") end

  local vh = simple_hash(vram)
  local ch = simple_hash(cgram)

  if DUMP_RAW_BINS then
    if #vram > 0 then write_bin(join(dir, "vram.bin"), vram) end
    if #cgram > 0 then write_bin(join(dir, "cgram.bin"), cgram) end
    if #oam > 0 then write_bin(join(dir, "oam.bin"), oam) end
  end

  dump_ppu_regs(dir)
  dump_bg_summary(dir)

  local visible_count, active_head = dump_visible_objects_csv(dir)
  append_text(object_summary_path, csv_line({current_frame(), SCENE_LABEL, visible_count, active_head}))

  if #oam > 0 then dump_oam_csv(dir, oam) end

  if #vram > 0 and #cgram > 0 then
    for bg = 1, 4 do
      dump_bg_tilemap_csv(dir, bg, vram)
      dump_bg_tile_usage_csv(dir, bg, vram)
      if DUMP_BG_PREVIEWS then dump_bg_preview_ppm(dir, bg, vram, cgram) end
    end

    if DUMP_FULL_TILE_SHEETS then
      dump_tile_sheet_ppm(dir, vram, cgram, 2)
      dump_tile_sheet_ppm(dir, vram, cgram, 4)
      dump_tile_sheet_ppm(dir, vram, cgram, 8)
    end
  end

  append_text(frame_summary_path, csv_line({
    f, reason, SCENE_LABEL, bgmode(),
    hex4(bg_map_base(1)), hex4(bg_char_base(1)), bg_bpp(1),
    hex4(bg_map_base(2)), hex4(bg_char_base(2)), bg_bpp(2),
    hex4(bg_map_base(3)), hex4(bg_char_base(3)), bg_bpp(3),
    hex4(bg_map_base(4)), hex4(bg_char_base(4)), bg_bpp(4),
    hex2(ppu[0x212C]), hex2(ppu[0x212D]), visible_count, active_head,
    hex4(vh), hex4(ch), ppu_signature()
  }))

  append_text(manifest_path, csv_line({
    f, reason, SCENE_LABEL, dir, hex4(vh), hex4(ch), ppu_signature(),
    VRAM_DOMAIN or "", CGRAM_DOMAIN or "", OAM_DOMAIN or "", BUS_DOMAIN or ""
  }))

  last_vram_hash = vh
  last_cgram_hash = ch
  last_ppu_sig = ppu_signature()
  log("GFX_SNAPSHOT,frame=" .. f .. ",reason=" .. reason .. ",dir=" .. dir .. ",vram_hash=" .. hex4(vh) .. ",cgram_hash=" .. hex4(ch))
end

------------------------------------------------------------
-- Init
------------------------------------------------------------

ensure_dir(OUT_DIR)

write_text(manifest_path, csv_line({
  "frame","reason","scene_label","dir","vram_hash","cgram_hash","ppu_signature",
  "vram_domain","cgram_domain","oam_domain","bus_domain"
}))

write_text(ppu_write_log_path, csv_line({"frame","addr","value","name"}))
write_text(dma_log_path, csv_line({
  "frame","channel","dmap","bbad","target","source","rom_offset_guess","rom_map_guess","size",
  "vmain","vmaddl","vmaddh","vram_word_addr","vram_byte_addr","cgadd","trigger","scene_label"
}))

write_text(frame_summary_path, csv_line({
  "frame","reason","scene_label","mode","bg1_map","bg1_chr","bg1_bpp","bg2_map","bg2_chr","bg2_bpp",
  "bg3_map","bg3_chr","bg3_bpp","bg4_map","bg4_chr","bg4_bpp","tm","ts","oam_visible_count","active_head",
  "vram_hash","cgram_hash","ppu_signature"
}))

write_text(object_summary_path, csv_line({
  "frame","scene_label","oam_visible_count","active_head"
}))

local hook_count = setup_hooks()

log("shinmomo graphics/mapchip probe v1 loaded")
log("domains: BUS=" .. tostring(BUS_DOMAIN) .. " WRAM=" .. tostring(WRAM_DOMAIN) ..
    " VRAM=" .. tostring(VRAM_DOMAIN) .. " CGRAM=" .. tostring(CGRAM_DOMAIN) ..
    " OAM=" .. tostring(OAM_DOMAIN))
log("write hooks installed=" .. tostring(hook_count))
log("output dir=" .. OUT_DIR)

dump_snapshot("init")

------------------------------------------------------------
-- Main loop
------------------------------------------------------------

while true do
  emu.frameadvance()
  local f = current_frame()

  if f % HEARTBEAT_EVERY_FRAMES == 0 then
    log("GFX_PROBE_HEARTBEAT,frame=" .. f ..
        ",scene=" .. SCENE_LABEL ..
        ",mode=" .. tostring(bgmode()) ..
        ",sig=" .. ppu_signature())
  end

  if f % DUMP_EVERY_FRAMES == 0 then
    dump_snapshot("interval")
  else
    -- PPU layout change detection: light snapshot trigger.
    local sig = ppu_signature()
    if last_ppu_sig ~= "" and sig ~= last_ppu_sig then
      dump_snapshot("ppu_layout_change")
    end
  end
end
