-- Shin Momotarou Densetsu remote experiment bridge for BizHawk.
-- Host commands are issued by shinmomo_lab.ps1 through a tiny TSV mailbox.
-- ROM path, savestates, and raw captures stay outside GitHub.

local LAB_DIR = os.getenv("SHINMOMO_LAB_DIR") or "."
local SEP = (package and package.config and package.config:sub(1,1)) or "\\"
local COMMAND = LAB_DIR .. SEP .. "command.tsv"
local RESPONSES = LAB_DIR .. SEP .. "responses"
local CAPTURES = LAB_DIR .. SEP .. "captures"
local SCREENS = LAB_DIR .. SEP .. "screens"
local MAP_CAPTURES = LAB_DIR .. SEP .. "map_captures"
local STATES = LAB_DIR .. SEP .. "states"

local pending_gamepad = nil -- retained for compatibility; command mode is synchronous
local goal13_trace_active = false
local goal13_trace_rows = {}
local goal13_hook_registered = 0
local goal13_hook_errors = {}

local function split_tabs(s)
  local out = {}
  for field in (s .. "\t"):gmatch("(.-)\t") do out[#out + 1] = field end
  return out
end

local function clean_id(s)
  return (tostring(s or ""):gsub("[^%w%-%_]", "_"))
end

local function json_quote(s)
  s = tostring(s or "")
  s = s:gsub("\\", "\\\\"):gsub('"', '\\"'):gsub("\r", "\\r"):gsub("\n", "\\n")
  return '"' .. s .. '"'
end

local function read_all(path)
  local f = io.open(path, "rb")
  if not f then return nil end
  local s = f:read("*a")
  f:close()
  return s
end

local function write_all(path, s)
  local f, err = io.open(path, "wb")
  if not f then return nil, err end
  f:write(s)
  f:close()
  return true
end

local function ensure_dir(path)
  if SEP == "\\" then
    os.execute('mkdir "' .. path .. '" >nul 2>nul')
  else
    os.execute('mkdir -p "' .. path .. '" >/dev/null 2>/dev/null')
  end
end

local function memory_domains()
  if memory and memory.getmemorydomainlist then
    local ok, domains = pcall(memory.getmemorydomainlist)
    if ok and domains then return domains end
  end
  return {}
end

local function find_domain(candidates)
  local domains = memory_domains()
  for _,want in ipairs(candidates) do
    for _,got in ipairs(domains) do
      if got == want then return got end
    end
  end
  for _,want in ipairs(candidates) do
    local lw = string.lower(want)
    for _,got in ipairs(domains) do
      if string.find(string.lower(got), lw, 1, true) then return got end
    end
  end
  return nil
end

local MAP_VRAM_DOMAIN = find_domain({"VRAM", "Snes VRAM", "SNES VRAM"})
local MAP_CGRAM_DOMAIN = find_domain({"CGRAM", "Snes CGRAM", "SNES CGRAM", "CRAM"})
local MAP_OAM_DOMAIN = find_domain({"OAM", "Snes OAM", "SNES OAM", "Sprite RAM"})
local MAP_BUS_DOMAIN = find_domain({"System Bus", "Bus", "Snes Bus", "SNES Bus"}) or "System Bus"

local function write_byte_table_bin(path, values, size)
  local f, err = io.open(path, "wb")
  if not f then return nil, err end
  local chunk = {}
  for i=0,size-1 do
    chunk[#chunk + 1] = string.char((values[i] or 0) % 256)
    if #chunk >= 4096 then
      f:write(table.concat(chunk))
      chunk = {}
    end
  end
  if #chunk > 0 then f:write(table.concat(chunk)) end
  f:close()
  return true
end

local function write_domain_bin(path, domain, size)
  if not domain then return nil, "memory domain unavailable" end
  local f, err = io.open(path, "wb")
  if not f then return nil, err end
  local chunk = {}
  for i=0,size-1 do
    local v = nil
    if memory and memory.read_u8 then
      local ok, got = pcall(memory.read_u8, i, domain)
      if ok then v = got end
    end
    if v == nil and memory and memory.readbyte then
      local ok, got = pcall(memory.readbyte, i, domain)
      if ok then v = got end
    end
    chunk[#chunk + 1] = string.char((v or 0) % 256)
    if #chunk >= 4096 then
      f:write(table.concat(chunk))
      chunk = {}
    end
  end
  if #chunk > 0 then f:write(table.concat(chunk)) end
  f:close()
  return true
end

local function respond(id, status, payload)
  id = clean_id(id)
  payload = tostring(payload or ""):gsub("[\t\r\n]", " ")
  local path = RESPONSES .. SEP .. id .. ".tsv"
  local ok, err = write_all(path, table.concat({id, status, payload}, "\t"))
  if not ok and console and console.log then
    console.log("SHINMOMO_REMOTE response error: " .. tostring(err))
  end
end

local function parse_num(s)
  s = tostring(s or "")
  if s:match("^0[xX][0-9a-fA-F]+$") then return tonumber(s:sub(3), 16) end
  return tonumber(s)
end

local function read8(addr, domain)
  if memory and memory.read_u8 then
    local ok, v = pcall(memory.read_u8, addr, domain)
    if ok then return v end
  end
  if memory and memory.readbyte then
    local ok, v = pcall(memory.readbyte, addr, domain)
    if ok then return v end
  end
  return nil
end

local function framecount()
  return (emu and emu.framecount and emu.framecount()) or -1
end

local function reg(name)
  if emu and emu.getregister then
    local ok, v = pcall(emu.getregister, name)
    if ok then return v end
  end
  return nil
end

local function json_num(v)
  return v == nil and "null" or tostring(v)
end

local function goal13_emit(kind, target, slot_override)
  if not goal13_trace_active then return end

  local x = reg("X")
  local slot = slot_override ~= nil and slot_override or x
  local parts = {
    "{",
    '"frame":' .. tostring(framecount()) .. ",",
    '"kind":' .. json_quote(kind) .. ",",
    '"target":' .. json_quote(target) .. ",",
    '"pc":' .. json_num(reg("PC")) .. ",",
    '"pbr":' .. json_num(reg("PBR")) .. ",",
    '"db":' .. json_num(reg("DB")) .. ",",
    '"a":' .. json_num(reg("A")) .. ",",
    '"x":' .. json_num(x) .. ",",
    '"y":' .. json_num(reg("Y")) .. ",",
    '"p":' .. json_num(reg("P")) .. ",",
    '"w030b":' .. json_num(read8(0x030B, "WRAM")) .. ",",
    '"w030d":' .. json_num(read8(0x030D, "WRAM")) .. ",",
    '"w1395":' .. json_num(read8(0x1395, "WRAM")) .. ",",
    '"w1396":' .. json_num(read8(0x1396, "WRAM")) .. ",",
    '"active_count":' .. json_num(read8(0x0AE5, "WRAM")) .. ",",
    '"oam_dirty":' .. json_num(read8(0x0A1B, "WRAM"))
  }

  if slot and slot >= 0 and slot < 0x40 then
    parts[#parts + 1] = ',"slot":' .. tostring(slot)
    parts[#parts + 1] = ',"ctrl0619":' .. json_num(read8(0x0619 + slot, "WRAM"))
    parts[#parts + 1] = ',"ctrl0759":' .. json_num(read8(0x0759 + slot, "WRAM"))
    parts[#parts + 1] = ',"ctrl0799":' .. json_num(read8(0x0799 + slot, "WRAM"))
    parts[#parts + 1] = ',"ctrl07d9":' .. json_num(read8(0x07D9 + slot, "WRAM"))
    parts[#parts + 1] = ',"ctrl0819":' .. json_num(read8(0x0819 + slot, "WRAM"))
    parts[#parts + 1] = ',"ctrl0859":' .. json_num(read8(0x0859 + slot, "WRAM"))
    parts[#parts + 1] = ',"ctrl0899":' .. json_num(read8(0x0899 + slot, "WRAM"))
    parts[#parts + 1] = ',"ctrl08d9":' .. json_num(read8(0x08D9 + slot, "WRAM"))
    parts[#parts + 1] = ',"ctrl0919":' .. json_num(read8(0x0919 + slot, "WRAM"))
    parts[#parts + 1] = ',"ctrl0959":' .. json_num(read8(0x0959 + slot, "WRAM"))
  end

  if slot and slot >= 0 and slot < 0x42 then
    parts[#parts + 1] = ',"vis_prev":' .. json_num(read8(0x0A1F + slot, "WRAM"))
    parts[#parts + 1] = ',"vis_next":' .. json_num(read8(0x0A61 + slot, "WRAM"))
    parts[#parts + 1] = ',"vis_sort":' .. json_num(read8(0x0AA3 + slot, "WRAM"))
    parts[#parts + 1] = ',"vis_group":' .. json_num(read8(0x0B27 + slot, "WRAM"))
    parts[#parts + 1] = ',"vis_frame":' .. json_num(read8(0x0AE5 + slot, "WRAM"))
    parts[#parts + 1] = ',"vis_x_lo":' .. json_num(read8(0x0BA5 + slot, "WRAM"))
    parts[#parts + 1] = ',"vis_x_hi":' .. json_num(read8(0x0BE5 + slot, "WRAM"))
    parts[#parts + 1] = ',"vis_y_lo":' .. json_num(read8(0x0C65 + slot, "WRAM"))
    parts[#parts + 1] = ',"vis_y_hi":' .. json_num(read8(0x0CA5 + slot, "WRAM"))
  end

  parts[#parts + 1] = "}"
  goal13_trace_rows[#goal13_trace_rows + 1] = table.concat(parts)
end

local function read_range(start, length, domain)
  local out = {}
  for i=0,length-1 do
    out[#out + 1] = read8(start + i, domain)
  end
  return out
end

local function bytes_json(bytes)
  local parts = {"["}
  for i=1,#bytes do
    if i > 1 then parts[#parts + 1] = "," end
    local v = bytes[i]
    parts[#parts + 1] = v == nil and "null" or tostring(v)
  end
  parts[#parts + 1] = "]"
  return table.concat(parts)
end

local function snapshot_json(label, domain, start, length)
  return table.concat({
    "{",
    '"label":' .. json_quote(label) .. ",",
    '"frame":' .. tostring(framecount()) .. ",",
    '"bytes":' .. bytes_json(read_range(start, length, domain)),
    "}"
  })
end

local map_ppu = {}
local map_cgram = {}
for i=0,0x1FF do map_cgram[i] = 0 end
local map_cgram_index = 0
local map_cgram_high = false

local map_ppu_addrs = {
  0x2100,0x2101,0x2105,0x2106,0x2107,0x2108,0x2109,0x210A,
  0x210B,0x210C,0x210D,0x210E,0x210F,0x2110,0x2111,0x2112,
  0x2113,0x2114,0x2115,0x2116,0x2117,0x212C,0x212D
}
for _,addr in ipairs(map_ppu_addrs) do map_ppu[addr] = nil end

local map_ppu_hook_count = 0
local map_ppu_hook_errors = {}

local function record_map_ppu_write(logical, a, v)
  local value = v
  if type(a) == "number" and type(v) ~= "number" then value = a end
  if type(value) ~= "number" then return end
  value = value % 256
  map_ppu[logical] = value

  if logical == 0x2121 then
    map_cgram_index = (value % 256) * 2
    map_cgram_high = false
  elseif logical == 0x2122 then
    map_cgram[map_cgram_index % 0x200] = value
    map_cgram_index = (map_cgram_index + 1) % 0x200
    map_cgram_high = not map_cgram_high
  end
end

for i,addr in ipairs(map_ppu_addrs) do
  local logical = addr
  local function cb(a, v) record_map_ppu_write(logical, a, v) end

  -- Proven convention from graphics/f000012.lua:
  --   3 args: callback, address, hook_name
  --   4 args: callback, address, domain, hook_name
  local ok_short, err_short = pcall(
    event.onmemorywrite,
    cb,
    addr,
    "shinmomo_remote_map_ppu_short_" .. tostring(i)
  )
  if ok_short then
    map_ppu_hook_count = map_ppu_hook_count + 1
  else
    map_ppu_hook_errors[#map_ppu_hook_errors + 1] =
      string.format("short:%04X:%s", addr, tostring(err_short))
  end

  if MAP_BUS_DOMAIN then
    local ok_bus, err_bus = pcall(
      event.onmemorywrite,
      cb,
      addr,
      MAP_BUS_DOMAIN,
      "shinmomo_remote_map_ppu_bus_" .. tostring(i)
    )
    if ok_bus then
      map_ppu_hook_count = map_ppu_hook_count + 1
    else
      map_ppu_hook_errors[#map_ppu_hook_errors + 1] =
        string.format("bus:%04X:%s", addr, tostring(err_bus))
    end
  end
end

local function ppu_json()
  local rows = {"{"}
  local first = true
  for _,addr in ipairs(map_ppu_addrs) do
    if not first then rows[#rows + 1] = "," end
    first = false
    rows[#rows + 1] = json_quote(string.format("%04X", addr)) .. ":" .. json_num(map_ppu[addr])
  end
  rows[#rows + 1] = "}"
  return table.concat(rows)
end

local function do_map_capture(id, scene_tag)
  local tag = clean_id(scene_tag or "scene")
  local capture_id = clean_id(id)
  local dir = MAP_CAPTURES .. SEP .. capture_id .. "_" .. tag
  ensure_dir(MAP_CAPTURES)
  ensure_dir(dir)

  local files = {}
  local function dump(name, domain, size)
    local path = dir .. SEP .. name
    local ok, err = write_domain_bin(path, domain, size)
    if ok then
      files[#files + 1] = name
      return true
    end
    return nil, err
  end

  local ok_v, err_v = dump("vram.bin", MAP_VRAM_DOMAIN, 0x10000)

  local ok_c, err_c
  if MAP_CGRAM_DOMAIN then
    ok_c, err_c = dump("cgram.bin", MAP_CGRAM_DOMAIN, 0x200)
  else
    ok_c, err_c = write_byte_table_bin(dir .. SEP .. "cgram.bin", map_cgram, 0x200)
    if ok_c then files[#files + 1] = "cgram.bin" end
  end

  local ok_o, err_o = dump("oam.bin", MAP_OAM_DOMAIN, 0x220)

  local shot_name = "screen.png"
  local shot_path = dir .. SEP .. shot_name
  local shot_ok = false
  local shot_err = ""
  if client and client.screenshot then
    local ok, err = pcall(client.screenshot, shot_path)
    shot_ok = ok
    shot_err = ok and "" or tostring(err)
    if ok then files[#files + 1] = shot_name end
  else
    shot_err = "client.screenshot unavailable"
  end

  local manifest = table.concat({
    "{",
    '"schema_version":2,',
    '"capture_id":' .. json_quote(capture_id) .. ",",
    '"scene_tag":' .. json_quote(tag) .. ",",
    '"frame":' .. tostring(framecount()) .. ",",
    '"map_state":{',
      '"current_pack_0305":' .. json_num(read8(0x0305, "WRAM")) .. ",",
      '"vm_pack_126e":' .. json_num(read8(0x126E, "WRAM")) .. ",",
      '"resolved_pack_12b4":' .. json_num(read8(0x12B4, "WRAM")) .. ",",
      '"mode_1398":' .. json_num(read8(0x1398, "WRAM")) .. ",",
      '"pending_mode_1399":' .. json_num(read8(0x1399, "WRAM")) .. ",",
      '"map_variant_139b":' .. json_num(read8(0x139B, "WRAM")) .. ",",
      '"primary_tileset_139c":' .. json_num(read8(0x139C, "WRAM")) .. ",",
      '"secondary_tileset_139d":' .. json_num(read8(0x139D, "WRAM")) .. ",",
      '"primary_layout_139e":' .. json_num(read8(0x139E, "WRAM")) .. ",",
      '"secondary_layout_139f":' .. json_num(read8(0x139F, "WRAM")) ..
    "},",
    '"domains":{',
      '"vram":' .. json_quote(MAP_VRAM_DOMAIN or "") .. ",",
      '"cgram":' .. json_quote(MAP_CGRAM_DOMAIN or "") .. ",",
      '"oam":' .. json_quote(MAP_OAM_DOMAIN or "") .. ",",
      '"bus":' .. json_quote(MAP_BUS_DOMAIN or "") ..
    "},",
    '"all_memory_domains":[' .. (function()
      local x = {}
      for i,name in ipairs(memory_domains()) do x[i] = json_quote(name) end
      return table.concat(x, ",")
    end)() .. "],",
    '"ppu_hook_count":' .. tostring(map_ppu_hook_count) .. ",",
    '"ppu_hook_errors":' .. json_quote(table.concat(map_ppu_hook_errors, " | ")) .. ",",
    '"ppu":' .. ppu_json() .. ",",
    '"files":[' .. (function()
      local x = {}
      for i,name in ipairs(files) do x[i] = json_quote(name) end
      return table.concat(x, ",")
    end)() .. "],",
    '"errors":{',
      '"vram":' .. json_quote(ok_v and "" or tostring(err_v)) .. ",",
      '"cgram":' .. json_quote(ok_c and "" or tostring(err_c)) .. ",",
      '"oam":' .. json_quote(ok_o and "" or tostring(err_o)) .. ",",
      '"screenshot":' .. json_quote(shot_err) ..
    "}",
    "}"
  })
  local manifest_path = dir .. SEP .. "manifest.json"
  local ok_m, err_m = write_all(manifest_path, manifest)
  if not ok_m then
    respond(id, "ERR", "map manifest write failed: " .. tostring(err_m))
    return
  end
  respond(id, "OK", manifest_path)
end

local valid_buttons = {
  A=true,B=true,X=true,Y=true,L=true,R=true,Up=true,Down=true,
  Left=true,Right=true,Start=true,Select=true
}

local function parse_buttons(csv)
  local t = {}
  for name in tostring(csv or ""):gmatch("[^,%s]+") do
    if not valid_buttons[name] then
      return nil, "unsupported SNES button: " .. name
    end
    t[name] = true
  end
  if next(t) == nil then return nil, "no buttons supplied" end
  return t
end

local function advance_exact(frames, buttons, player, after_each)
  if not frames or frames < 1 then return true, 0 end

  local completed = 0
  local done = false
  local input_hook = nil
  local end_hook = nil
  local callback_error = nil

  if buttons and player then
    local ok, hook_or_err = pcall(
      event.onframestart,
      function()
        local joy_ok, joy_err = pcall(joypad.set, buttons, player)
        if not joy_ok then
          callback_error = "joypad.set failed: " .. tostring(joy_err)
        end
      end,
      "shinmomo_remote_exact_input"
    )
    if not ok then return nil, "input hook failed: " .. tostring(hook_or_err) end
    input_hook = hook_or_err
  else
    for p=1,4 do pcall(joypad.set, {}, p) end
  end

  local ok_end, end_or_err = pcall(
    event.onframeend,
    function()
      completed = completed + 1
      if after_each then
        local cb_ok, cb_err = pcall(after_each, completed)
        if not cb_ok then callback_error = "after_each failed: " .. tostring(cb_err) end
      end
      if callback_error or completed >= frames then
        done = true
      end
    end,
    "shinmomo_remote_exact_frame_gate"
  )

  if not ok_end then
    if input_hook then pcall(event.unregisterbyid, input_hook) end
    return nil, "frame-end hook failed: " .. tostring(end_or_err)
  end
  end_hook = end_or_err

  if client and client.unpause then
    local ok_unpause, unpause_err = pcall(client.unpause)
    if not ok_unpause then
      if input_hook then pcall(event.unregisterbyid, input_hook) end
      if end_hook then pcall(event.unregisterbyid, end_hook) end
      return nil, "client.unpause failed: " .. tostring(unpause_err)
    end
  else
    if input_hook then pcall(event.unregisterbyid, input_hook) end
    if end_hook then pcall(event.unregisterbyid, end_hook) end
    return nil, "client.unpause unavailable"
  end

  while not done do emu.yield() end

  if client and client.pause then pcall(client.pause) end
  if input_hook then pcall(event.unregisterbyid, input_hook) end
  if end_hook then pcall(event.unregisterbyid, end_hook) end
  if player then pcall(joypad.set, {}, player) end

  if callback_error then return nil, callback_error end
  return true, completed
end

local function do_screenshot(id)
  local path = SCREENS .. SEP .. "game_" .. clean_id(id) .. ".png"
  if not client or not client.screenshot then
    respond(id, "ERR", "client.screenshot unavailable")
    return
  end
  local ok, err = pcall(client.screenshot, path)
  if not ok then
    respond(id, "ERR", "screenshot failed: " .. tostring(err))
    return
  end
  respond(id, "OK", path)
end

local function do_capture(id, domain, start_s, length_s)
  local start = parse_num(start_s)
  local length = tonumber(length_s)
  if not start or start < 0 then
    respond(id, "ERR", "invalid start address")
    return
  end
  if not length or length < 1 or length > 4096 then
    respond(id, "ERR", "length must be 1..4096")
    return
  end

  local path = CAPTURES .. SEP .. "mem_" .. clean_id(id) .. ".json"
  local parts = {
    "{",
    '"id":' .. json_quote(id) .. ",",
    '"frame":' .. tostring((emu and emu.framecount and emu.framecount()) or -1) .. ",",
    '"domain":' .. json_quote(domain) .. ",",
    '"start":' .. tostring(start) .. ",",
    '"length":' .. tostring(length) .. ",",
    '"bytes":['
  }

  for i=0,length-1 do
    local v = read8(start+i, domain)
    if i > 0 then parts[#parts+1] = "," end
    parts[#parts+1] = v == nil and "null" or tostring(v)
  end
  parts[#parts+1] = "]}"
  local ok, err = write_all(path, table.concat(parts))
  if not ok then
    respond(id, "ERR", "capture write failed: " .. tostring(err))
    return
  end
  respond(id, "OK", path)
end

local function do_atomic_gamepad_capture(id, player_s, button_csv, frames_s,
                                         domain, start_s, length_s, post_s,
                                         enable_goal13_trace)
  local player = tonumber(player_s) or 1
  local frames = tonumber(frames_s) or 1
  local post_frames = tonumber(post_s) or 0
  local start = parse_num(start_s)
  local length = tonumber(length_s)
  local buttons, err = parse_buttons(button_csv)

  if not buttons then
    respond(id, "ERR", err)
    return
  end
  if player < 1 or player > 4 then
    respond(id, "ERR", "player must be 1..4")
    return
  end
  if frames < 1 or frames > 600 then
    respond(id, "ERR", "frames must be 1..600")
    return
  end
  if post_frames < 0 or post_frames > 120 then
    respond(id, "ERR", "post frames must be 0..120")
    return
  end
  if not start or start < 0 then
    respond(id, "ERR", "invalid start address")
    return
  end
  if not length or length < 1 or length > 4096 then
    respond(id, "ERR", "length must be 1..4096")
    return
  end

  local snapshots = {}
  if enable_goal13_trace then
    goal13_trace_rows = {}
    goal13_trace_active = true
  end
  snapshots[#snapshots + 1] = snapshot_json("before", domain, start, length)

  local ok_input, input_result = advance_exact(
    frames,
    buttons,
    player,
    function(i)
      snapshots[#snapshots + 1] =
        snapshot_json("input_" .. tostring(i), domain, start, length)
    end
  )
  if not ok_input then
    if enable_goal13_trace then goal13_trace_active = false end
    respond(id, "ERR", tostring(input_result))
    return
  end

  if post_frames > 0 then
    local ok_post, post_result = advance_exact(
      post_frames,
      nil,
      nil,
      function(i)
        snapshots[#snapshots + 1] =
          snapshot_json("post_" .. tostring(i), domain, start, length)
      end
    )
    if not ok_post then
      if enable_goal13_trace then goal13_trace_active = false end
      respond(id, "ERR", tostring(post_result))
      return
    end
  end

  if enable_goal13_trace then
    goal13_trace_active = false
  end

  local path = CAPTURES .. SEP .. "atomic_" .. clean_id(id) .. ".json"
  local payload = table.concat({
    "{",
    '"id":' .. json_quote(id) .. ",",
    '"domain":' .. json_quote(domain) .. ",",
    '"start":' .. tostring(start) .. ",",
    '"length":' .. tostring(length) .. ",",
    '"player":' .. tostring(player) .. ",",
    '"buttons":' .. json_quote(button_csv) .. ",",
    '"input_frames":' .. tostring(frames) .. ",",
    '"post_frames":' .. tostring(post_frames) .. ",",
    '"goal13_hook_registered":' .. tostring(goal13_hook_registered) .. ",",
    '"goal13_hook_errors":' .. json_quote(table.concat(goal13_hook_errors, " | ")) .. ",",
    '"snapshots":[' .. table.concat(snapshots, ",") .. "],",
    '"goal13_trace":[' .. table.concat(goal13_trace_rows, ",") .. "]",
    "}"
  })

  local ok, writeerr = write_all(path, payload)
  if not ok then
    respond(id, "ERR", "atomic capture write failed: " .. tostring(writeerr))
    return
  end
  respond(id, "OK", path)
end

local function do_save_state(id, name)
  local base = clean_id(name or "mole_remote")
  if base == "" then base = "mole_remote" end
  ensure_dir(STATES)
  local path = STATES .. SEP .. base .. ".State"
  if not savestate or not savestate.save then
    respond(id, "ERR", "savestate.save unavailable")
    return
  end
  local ok, result = pcall(savestate.save, path)
  if not ok or result == false then
    respond(id, "ERR", ok and "savestate.save returned false" or tostring(result))
    return
  end
  respond(id, "OK", path)
end

local function do_load_state(id, name)
  local base = clean_id(name or "mole_remote")
  if base == "" then base = "mole_remote" end
  ensure_dir(STATES)
  local path = STATES .. SEP .. base .. ".State"
  local f = io.open(path, "rb")
  if not f then
    respond(id, "ERR", "savestate not found: " .. path)
    return
  end
  f:close()
  if not savestate or not savestate.load then
    respond(id, "ERR", "savestate.load unavailable")
    return
  end
  local ok, result = pcall(savestate.load, path)
  if not ok or result == false then
    respond(id, "ERR", ok and "savestate.load returned false" or tostring(result))
    return
  end
  respond(id, "OK", path)
end

local function process_command()
  local line = read_all(COMMAND)
  if not line or line == "" then return end
  os.remove(COMMAND)

  line = line:gsub("[\r\n]+$", "")
  local p = split_tabs(line)
  local id = p[1]
  local cmd = p[2]

  if not id or not cmd then return end

  if cmd == "GAMEPAD" then
    local player = tonumber(p[3]) or 1
    local buttons, err = parse_buttons(p[4])
    local frames = tonumber(p[5]) or 1
    if not buttons then
      respond(id, "ERR", err)
      return
    end
    if player < 1 or player > 4 then
      respond(id, "ERR", "player must be 1..4")
      return
    end
    if frames < 1 or frames > 600 then
      respond(id, "ERR", "frames must be 1..600")
      return
    end

    local ok_advance, advanced_or_err = advance_exact(frames, buttons, player, nil)
    if not ok_advance then
      respond(id, "ERR", tostring(advanced_or_err))
      return
    end
    respond(id, "OK", "applied " .. tostring(advanced_or_err) .. " frame(s)")
    return
  end

  if cmd == "STEP" then
    local frames = tonumber(p[3]) or 1
    if frames < 1 or frames > 600 then
      respond(id, "ERR", "frames must be 1..600")
      return
    end
    local ok_advance, advanced_or_err = advance_exact(frames, nil, nil, nil)
    if not ok_advance then
      respond(id, "ERR", tostring(advanced_or_err))
      return
    end
    respond(id, "OK", "advanced " .. tostring(advanced_or_err) .. " neutral frame(s)")
    return
  end

  if cmd == "ATOMIC_GAMEPAD_CAPTURE" or cmd == "ATOMIC_GOAL13_CAPTURE" then
    do_atomic_gamepad_capture(
      id,
      p[3] or "1",
      p[4] or "",
      p[5] or "1",
      p[6] or "WRAM",
      p[7] or "0",
      p[8] or "256",
      p[9] or "0",
      cmd == "ATOMIC_GOAL13_CAPTURE"
    )
    return
  end

  if cmd == "SCREENSHOT" then
    do_screenshot(id)
    return
  end

  if cmd == "MAP_CAPTURE" then
    do_map_capture(id, p[3] or "scene")
    return
  end

  if cmd == "CAPTURE_MEMORY" then
    do_capture(id, p[3] or "WRAM", p[4] or "0", p[5] or "256")
    return
  end

  if cmd == "SAVE_STATE" then
    do_save_state(id, p[3] or "mole_remote")
    return
  end

  if cmd == "LOAD_STATE" then
    do_load_state(id, p[3] or "mole_remote")
    return
  end

  respond(id, "ERR", "unknown bridge command: " .. tostring(cmd))
end

local goal13_targets = {
  {0x89BA36, "controller", "89:BA36"}, {0xC9BA36, "controller", "C9:BA36"},
  {0x89BA48, "controller", "89:BA48"}, {0xC9BA48, "controller", "C9:BA48"},
  {0x89BA70, "controller", "89:BA70"}, {0xC9BA70, "controller", "C9:BA70"},
  {0x89BA76, "controller", "89:BA76_read0799x"}, {0xC9BA76, "controller", "C9:BA76_read0799x"},
  {0x89BA81, "controller", "89:BA81_write0799x"}, {0xC9BA81, "controller", "C9:BA81_write0799x"},
  {0x89BA89, "controller", "89:BA89_dec0799x"}, {0xC9BA89, "controller", "C9:BA89_dec0799x"},
  {0x89BAC8, "controller", "89:BAC8"}, {0xC9BAC8, "controller", "C9:BAC8"},
  {0x89BACD, "controller", "89:BACD_write0799x"}, {0xC9BACD, "controller", "C9:BACD_write0799x"},

  {0x00AF33, "visible", "00:AF33_alloc"}, {0x40AF33, "visible", "40:AF33_alloc"},
  {0x80AF33, "visible", "80:AF33_alloc"}, {0xC0AF33, "visible", "C0:AF33_alloc"},
  {0x00AFAA, "visible", "00:AFAA_remove"}, {0x40AFAA, "visible", "40:AFAA_remove"},
  {0x80AFAA, "visible", "80:AFAA_remove"}, {0xC0AFAA, "visible", "C0:AFAA_remove"},
  {0x00AFEC, "visible", "00:AFEC_reorder"}, {0x40AFEC, "visible", "40:AFEC_reorder"},
  {0x80AFEC, "visible", "80:AFEC_reorder"}, {0xC0AFEC, "visible", "C0:AFEC_reorder"},
  {0x00B03D, "render", "00:B03D_begin"}, {0x40B03D, "render", "40:B03D_begin"},
  {0x80B03D, "render", "80:B03D_begin"}, {0xC0B03D, "render", "C0:B03D_begin"},
  {0x00B100, "render", "00:B100_object"}, {0x40B100, "render", "40:B100_object"},
  {0x80B100, "render", "80:B100_object"}, {0xC0B100, "render", "C0:B100_object"},
}

for i,t in ipairs(goal13_targets) do
  local addr = t[1]
  local kind = t[2]
  local label = t[3]
  local hook_name = "shinmomo_remote_goal13_" .. tostring(i) .. "_" .. label
  local ok, err = pcall(
    event.onmemoryexecute,
    function() goal13_emit(kind, label) end,
    addr,
    hook_name,
    "System Bus"
  )
  if ok then
    goal13_hook_registered = goal13_hook_registered + 1
  else
    goal13_hook_errors[#goal13_hook_errors + 1] =
      label .. ":" .. tostring(err)
  end
end

-- BizHawk's bundled SNES examples also register 16-bit execution addresses
-- without an explicit memory scope. Keep these short-PC hooks in parallel
-- with the 24-bit System Bus hooks so the active SNES core's callback address
-- convention can be determined empirically. They are active only while an
-- atomic Goal13 experiment is collecting rows.
local goal13_short_targets = {
  {0xBA36, "controller", "short:BA36"},
  {0xBA48, "controller", "short:BA48"},
  {0xBA70, "controller", "short:BA70"},
  {0xBA76, "controller", "short:BA76_read0799x"},
  {0xBA81, "controller", "short:BA81_write0799x"},
  {0xBA89, "controller", "short:BA89_dec0799x"},
  {0xBAC8, "controller", "short:BAC8"},
  {0xBACD, "controller", "short:BACD_write0799x"},
  {0xAF33, "visible", "short:AF33_alloc"},
  {0xAFAA, "visible", "short:AFAA_remove"},
  {0xAFEC, "visible", "short:AFEC_reorder"},
  {0xB03D, "render", "short:B03D_begin"},
  {0xB100, "render", "short:B100_object"},
}

for i,t in ipairs(goal13_short_targets) do
  local addr = t[1]
  local kind = t[2]
  local label = t[3]
  local hook_name = "shinmomo_remote_goal13_short_" .. tostring(i) .. "_" .. label
  local ok, err = pcall(
    event.onmemoryexecute,
    function() goal13_emit(kind, label) end,
    addr,
    hook_name
  )
  if ok then
    goal13_hook_registered = goal13_hook_registered + 1
  else
    goal13_hook_errors[#goal13_hook_errors + 1] =
      label .. ":" .. tostring(err)
  end
end

-- Direct WRAM write watches are the primary Goal13 runtime trigger. The prior
-- 2026-09-25 field run already showed that the BAxx execution targets are not
-- guaranteed to run in an arbitrary movement window, while $0799,X itself can
-- change. Register each indexed byte on the System Bus and capture the exact
-- frame/register context when it is written.
for slot=0,0x3F do
  local watched_slot = slot
  local bus_addr = 0x7E0799 + watched_slot
  local label = string.format("WRAM:0799+%02X", watched_slot)
  local hook_name = "shinmomo_remote_goal13_w0799_" .. tostring(watched_slot)
  local ok, err = pcall(
    event.onmemorywrite,
    function() goal13_emit("w0799_write", label, watched_slot) end,
    bus_addr,
    hook_name
  )
  if ok then
    goal13_hook_registered = goal13_hook_registered + 1
  else
    goal13_hook_errors[#goal13_hook_errors + 1] =
      label .. ":" .. tostring(err)
  end
end

-- Active-list and sort-key writes are much rarer, so watching the 64 physical
-- slots is cheap and gives an exact frame for controller-to-visible-list
-- transitions when allocation/reorder happens.
for slot=0,0x3F do
  local watched_slot = slot
  local next_addr = 0x7E0A61 + watched_slot
  local sort_addr = 0x7E0AA3 + watched_slot

  local next_label = string.format("WRAM:0A61+%02X", watched_slot)
  local next_name = "shinmomo_remote_goal13_w0a61_" .. tostring(watched_slot)
  local ok_next, err_next = pcall(
    event.onmemorywrite,
    function() goal13_emit("active_next_write", next_label, watched_slot) end,
    next_addr,
    next_name
  )
  if ok_next then
    goal13_hook_registered = goal13_hook_registered + 1
  else
    goal13_hook_errors[#goal13_hook_errors + 1] =
      next_label .. ":" .. tostring(err_next)
  end

  local sort_label = string.format("WRAM:0AA3+%02X", watched_slot)
  local sort_name = "shinmomo_remote_goal13_w0aa3_" .. tostring(watched_slot)
  local ok_sort, err_sort = pcall(
    event.onmemorywrite,
    function() goal13_emit("active_sort_write", sort_label, watched_slot) end,
    sort_addr,
    sort_name
  )
  if ok_sort then
    goal13_hook_registered = goal13_hook_registered + 1
  else
    goal13_hook_errors[#goal13_hook_errors + 1] =
      sort_label .. ":" .. tostring(err_sort)
  end
end

if console and console.log then
  console.log(
    "SHINMOMO_REMOTE_BRIDGE_LOADED lab=" .. LAB_DIR ..
    " map_domains=" .. tostring(MAP_VRAM_DOMAIN) .. "/" ..
    tostring(MAP_CGRAM_DOMAIN) .. "/" .. tostring(MAP_OAM_DOMAIN) ..
    " map_ppu_hooks=" .. tostring(map_ppu_hook_count)
  )
end

-- Command-driven deterministic mode.
-- Keep emulation paused between mailbox commands so host/RDC latency cannot
-- advance hundreds or thousands of uncontrolled frames. emu.yield() keeps the
-- Lua mailbox responsive while paused; GAMEPAD/STEP/atomic commands explicitly
-- advance only the requested frames.
if client and client.pause then pcall(client.pause) end

while true do
  process_command()
  emu.yield()
end