-- Shin Momotarou Densetsu remote experiment bridge for BizHawk.
-- Host commands are issued by shinmomo_lab.ps1 through a tiny TSV mailbox.
-- ROM path, savestates, and raw captures stay outside GitHub.

local LAB_DIR = os.getenv("SHINMOMO_LAB_DIR") or "."
local SEP = (package and package.config and package.config:sub(1,1)) or "\\"
local COMMAND = LAB_DIR .. SEP .. "command.tsv"
local RESPONSES = LAB_DIR .. SEP .. "responses"
local CAPTURES = LAB_DIR .. SEP .. "captures"

local pending_gamepad = nil

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

if console and console.log then
  console.log("SHINMOMO_REMOTE_BRIDGE_LOADED lab=" .. LAB_DIR)
end

while true do
  process_command()
  apply_gamepad()
  emu.frameadvance()
end
