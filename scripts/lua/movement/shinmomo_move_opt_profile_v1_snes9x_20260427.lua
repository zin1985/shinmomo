-- shinmomo_move_opt_profile_v1_snes9x_20260427.lua
-- 移動/表示更新最適化候補の効果見積り用 polling tracer
--
-- 出力:
--   TRACE_MOVE_OPT_PROFILE
--
-- 見るもの:
--   projection_skip_slots: $00DF==0 かつ $15D5,X==0 のslot数
--   depth_same_key_slots : C1:90CEのsort keyと$0AA3[handle+2]が一致しているslot数
--   depth_invalid_slots  : handleが範囲外っぽいslot数
--
-- 注意:
--   実行回数そのものではなく、毎フレームの「スキップ可能性」推定です。

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

local function r8(addr)
  if DOMAIN == "System Bus" then
    return memory.read_u8(0x7E0000 + addr, DOMAIN)
  else
    return memory.read_u8(addr, DOMAIN)
  end
end

local function h2(v)
  return string.format("%02X", v % 0x100)
end

local function calc_sort_key(x)
  local a = (r8(0x157D) - r8(0x15E9 + x)) & 0xFF
  a = (a + 0x38) & 0xFF
  if a < 0x30 then a = 0x38 end
  if a >= 0x40 then a = 0x48 end
  return a
end

local function log(s)
  if console and console.log then console.log(s) else print(s) end
end

log("shinmomo move optimization profile loaded. domain=" .. tostring(DOMAIN))
log("TRACE_MOVE_OPT_PROFILE_READY,frame=" .. emu.framecount())

local last = ""
local interval = 30

while true do
  emu.frameadvance()
  local f = emu.framecount()

  if f % interval == 0 then
    local global_step = r8(0x00DF)
    local projection_skip = 0
    local projection_active = 0
    local depth_same = 0
    local depth_diff = 0
    local depth_invalid = 0
    local detail = {}

    for x = 0, 9 do
      local d5 = r8(0x15D5 + x)
      if global_step == 0 and d5 == 0 then
        projection_skip = projection_skip + 1
      else
        projection_active = projection_active + 1
      end

      local handle = r8(0x1591 + x)
      local phys = handle + 2
      if phys >= 0 and phys < 0x40 then
        local newkey = calc_sort_key(x)
        local oldkey = r8(0x0AA3 + phys)
        if newkey == oldkey then
          depth_same = depth_same + 1
        else
          depth_diff = depth_diff + 1
        end
        detail[#detail+1] = string.format("x%d:h%02X:p%02X:k%02X/%02X:d5%02X", x, handle, phys, newkey, oldkey, d5)
      else
        depth_invalid = depth_invalid + 1
        detail[#detail+1] = string.format("x%d:h%02X:invalid:d5%02X", x, handle, d5)
      end
    end

    local line = table.concat({
      "TRACE_MOVE_OPT_PROFILE",
      "frame=" .. f,
      "00DF=" .. h2(global_step),
      "projection_skip_slots=" .. projection_skip,
      "projection_active_slots=" .. projection_active,
      "depth_same_key_slots=" .. depth_same,
      "depth_diff_key_slots=" .. depth_diff,
      "depth_invalid_slots=" .. depth_invalid,
      "detail=" .. table.concat(detail, " ")
    }, ",")

    if line ~= last then
      log(line)
      last = line
    end
  end
end
