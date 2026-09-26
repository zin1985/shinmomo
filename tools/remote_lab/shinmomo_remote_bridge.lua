-- Shin Momotarou Densetsu remote experiment bridge for BizHawk.
-- Host commands are issued by shinmomo_lab.ps1 through a tiny TSV mailbox.
-- ROM path, savestates, and raw captures stay outside GitHub.

local LAB_DIR = os.getenv("SHINMOMO_LAB_DIR") or "."
local SEP = (package and package.config and package.config:sub(1,1)) or "\\"
local COMMAND = LAB_DIR .. SEP .. "command.tsv"
local RESPONSES = LAB_DIR .. SEP .. "responses"
local CAPTURES = LAB_DIR .. SEP .. "captures"

local pending_gamepad = nil
local goal13_trace_active = false
local goal13_trace_rows = {}

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

local function goal13_emit(kind, target)
  if not goal13_trace_active then return end

  local x = reg("X")
  local parts = {
    "{",
    '"frame":' .. tostring(framecount()) .. ",",
    '"kind":' .. json_quote(kind) .. ",",
    '"target":' .. json_quote(target) .. ",",
    '"pc":' .. json_num(reg("PC")) .. ",",
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

  if x and x >= 0 and x < 0x40 then
    parts[#parts + 1] = ',"ctrl0619":' .. json_num(read8(0x0619 + x, "WRAM"))
    parts[#parts + 1] = ',"ctrl0759":' .. json_num(read8(0x0759 + x, "WRAM"))
    parts[#parts + 1] = ',"ctrl0799":' .. json_num(read8(0x0799 + x, "WRAM"))
    parts[#parts + 1] = ',"ctrl07d9":' .. json_num(read8(0x07D9 + x, "WRAM"))
    parts[#parts + 1] = ',"ctrl0819":' .. json_num(read8(0x0819 + x, "WRAM"))
    parts[#parts + 1] = ',"ctrl0859":' .. json_num(read8(0x0859 + x, "WRAM"))
    parts[#parts + 1] = ',"ctrl0899":' .. json_num(read8(0x0899 + x, "WRAM"))
    parts[#parts + 1] = ',"ctrl08d9":' .. json_num(read8(0x08D9 + x, "WRAM"))
    parts[#parts + 1] = ',"ctrl0919":' .. json_num(read8(0x0919 + x, "WRAM"))
    parts[#parts + 1] = ',"ctrl0959":' .. json_num(read8(0x0959 + x, "WRAM"))
  end

  if x and x >= 0 and x < 0x42 then
    parts[#parts + 1] = ',"vis_prev":' .. json_num(read8(0x0A1F + x, "WRAM"))
    parts[#parts + 1] = ',"vis_next":' .. json_num(read8(0x0A61 + x, "WRAM"))
    parts[#parts + 1] = ',"vis_sort":' .. json_num(read8(0x0AA3 + x, "WRAM"))
    parts[#parts + 1] = ',"vis_group":' .. json_num(read8(0x0B27 + x, "WRAM"))
    parts[#parts + 1] = ',"vis_frame":' .. json_num(read8(0x0AE5 + x, "WRAM"))
    parts[#parts + 1] = ',"vis_x_lo":' .. json_num(read8(0x0BA5 + x, "WRAM"))
    parts[#parts + 1] = ',"vis_x_hi":' .. json_num(read8(0x0BE5 + x, "WRAM"))
    parts[#parts + 1] = ',"vis_y_lo":' .. json_num(read8(0x0C65 + x, "WRAM"))
    parts[#parts + 1] = ',"vis_y_hi":' .. json_num(read8(0x0CA5 + x, "WRAM"))
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

  for i=1,frames do
    local ok, joyerr = pcall(joypad.set, buttons, player)
    if not ok then
      respond(id, "ERR", "joypad.set failed: " .. tostring(joyerr))
      return
    end
    emu.frameadvance()
    snapshots[#snapshots + 1] =
      snapshot_json("input_" .. tostring(i), domain, start, length)
  end

  pcall(joypad.set, {}, player)

  for i=1,post_frames do
    emu.frameadvance()
    snapshots[#snapshots + 1] =
      snapshot_json("post_" .. tostring(i), domain, start, length)
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

local function process_command()
  if pending_gamepad then return end

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
    if frames < 1 or frames > 600 then
      respond(id, "ERR", "frames must be 1..600")
      return
    end
    pending_gamepad = {
      id=id, player=player, buttons=buttons,
      frames=frames, remaining=frames
    }
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

  if cmd == "CAPTURE_MEMORY" then
    do_capture(id, p[3] or "WRAM", p[4] or "0", p[5] or "256")
    return
  end

  respond(id, "ERR", "unknown bridge command: " .. tostring(cmd))
end

local function apply_gamepad()
  if not pending_gamepad then return end
  local g = pending_gamepad
  local ok, err = pcall(joypad.set, g.buttons, g.player)
  if not ok then
    respond(g.id, "ERR", "joypad.set failed: " .. tostring(err))
    pending_gamepad = nil
    return
  end
  g.remaining = g.remaining - 1
  if g.remaining <= 0 then
    respond(g.id, "OK", "applied " .. tostring(g.frames) .. " frame(s)")
    pending_gamepad = nil
  end
end


local goal13_targets = {
  {0x89BA36, "controller", "89:BA36"},
  {0x89BA48, "controller", "89:BA48"},
  {0x89BA70, "controller", "89:BA70"},
  {0x89BA76, "controller", "89:BA76_read0799x"},
  {0x89BA81, "controller", "89:BA81_write0799x"},
  {0x89BA89, "controller", "89:BA89_dec0799x"},
  {0x89BAC8, "controller", "89:BAC8"},
  {0x89BACD, "controller", "89:BACD_write0799x"},
  {0x80AF33, "visible", "80:AF33_alloc"},
  {0x80AFAA, "visible", "80:AFAA_remove"},
  {0x80AFEC, "visible", "80:AFEC_reorder"},
  {0x80B03D, "render", "80:B03D_begin"},
  {0x80B100, "render", "80:B100_object"},
  {0xC0AF33, "visible", "C0:AF33_alloc"},
  {0xC0AFAA, "visible", "C0:AFAA_remove"},
  {0xC0AFEC, "visible", "C0:AFEC_reorder"},
  {0xC0B03D, "render", "C0:B03D_begin"},
  {0xC0B100, "render", "C0:B100_object"},
}

for i,t in ipairs(goal13_targets) do
  local addr = t[1]
  local kind = t[2]
  local label = t[3]
  pcall(
    event.onmemoryexecute,
    function() goal13_emit(kind, label) end,
    addr,
    "System Bus",
    "shinmomo_remote_goal13_" .. tostring(i)
  )
end

if console and console.log then
  console.log("SHINMOMO_REMOTE_BRIDGE_LOADED lab=" .. LAB_DIR)
end

while true do
  process_command()
  apply_gamepad()
  emu.frameadvance()
end
