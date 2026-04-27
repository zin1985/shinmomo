-- shinmomo_move_opt_profile_v2_snes9x_20260427.lua
-- 新桃太郎伝説 移動/表示最適化 追加候補プロファイラ v2
--
-- 目的:
--   v2 IPSの次に効きそうな候補を、実行ログで見極める。
--
-- 出力:
--   TRACE_MOVE_OPT_PROFILE_V2
--
-- 主な観測:
--   actor_active_slots        $1569,X != 0
--   projection_skip_slots     $00DF==0 and $15D5,X==0
--   depth_same_key_slots      C1:90CEでAFECをskipできそうなslot
--   object_static_slots       coords/frame/group/flagsが前回サンプルから不変
--   object_draw_skip_slots    $0B25,slot bit40が立っている候補
--   offscreen_like_slots      screen座標が大きく外れていそうな候補
--
-- 注意:
--   Snes9x pollingなので厳密な実行回数ではなく「最適化余地の推定」です。

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

local function hx4(v)
  return string.format("%04X", v % 0x10000)
end

local function calc_sort_key(x)
  local a = (r8(0x157D) - r8(0x15E9 + x)) & 0xFF
  a = (a + 0x38) & 0xFF
  if a < 0x30 then a = 0x38 end
  if a >= 0x40 then a = 0x48 end
  return a
end

local function signed16(lo, hi)
  local v = lo + hi * 0x100
  if v >= 0x8000 then v = v - 0x10000 end
  return v
end

local function log(s)
  if console and console.log then console.log(s) else print(s) end
end

local prev_obj = {}

local function object_snapshot(phys)
  local x = signed16(r8(0x0BA7 + phys), r8(0x0BE7 + phys))
  local y = signed16(r8(0x0C67 + phys), r8(0x0CA7 + phys))
  local flags = r8(0x0B25 + phys)
  local frame = r8(0x0AE5 + phys)
  local group = flags & 0x0F
  local attrish = flags & 0xF0
  return table.concat({x, y, flags, frame, group, attrish}, ":")
end

local function is_offscreen_like(phys)
  local x = signed16(r8(0x0BA7 + phys), r8(0x0BE7 + phys))
  local y = signed16(r8(0x0C67 + phys), r8(0x0CA7 + phys))

  -- かなり緩い判定。画面外/待機座標候補を見るための目安。
  if x < -32 or x > 288 then return true end
  if y < -32 or y > 256 then return true end
  return false
end

log("shinmomo move optimization profile v2 loaded. domain=" .. tostring(DOMAIN))
log("TRACE_MOVE_OPT_PROFILE_V2_READY,frame=" .. emu.framecount())

local interval = 30
local last_line = ""

while true do
  emu.frameadvance()
  local f = emu.framecount()

  if f % interval == 0 then
    local global_step = r8(0x00DF)

    local actor_active = 0
    local actor_empty = 0
    local projection_skip = 0
    local projection_active = 0

    local depth_same = 0
    local depth_diff = 0
    local depth_invalid = 0

    local object_static = 0
    local object_changed = 0
    local object_draw_skip = 0
    local offscreen_like = 0

    local detail = {}

    for x = 0, 9 do
      local actor_id = r8(0x1569 + x)
      if actor_id ~= 0 then actor_active = actor_active + 1 else actor_empty = actor_empty + 1 end

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
        if newkey == oldkey then depth_same = depth_same + 1 else depth_diff = depth_diff + 1 end

        local flags = r8(0x0B25 + phys)
        if (flags & 0x40) ~= 0 then object_draw_skip = object_draw_skip + 1 end
        if is_offscreen_like(phys) then offscreen_like = offscreen_like + 1 end

        local snap = object_snapshot(phys)
        local prev = prev_obj[phys]
        if prev ~= nil and prev == snap then
          object_static = object_static + 1
        else
          object_changed = object_changed + 1
        end
        prev_obj[phys] = snap

        detail[#detail+1] = string.format(
          "x%d:id%02X:h%02X:p%02X:k%02X/%02X:d5%02X:fd%02X:f%02X:a%02X",
          x, actor_id, handle, phys, newkey, oldkey, d5, r8(0x15FD+x), r8(0x0B25+phys), r8(0x0AE5+phys)
        )
      else
        depth_invalid = depth_invalid + 1
        detail[#detail+1] = string.format("x%d:id%02X:h%02X:invalid:d5%02X", x, actor_id, handle, d5)
      end
    end

    local line = table.concat({
      "TRACE_MOVE_OPT_PROFILE_V2",
      "frame=" .. f,
      "00DF=" .. h2(global_step),
      "actor_active_slots=" .. actor_active,
      "actor_empty_slots=" .. actor_empty,
      "projection_skip_slots=" .. projection_skip,
      "projection_active_slots=" .. projection_active,
      "depth_same_key_slots=" .. depth_same,
      "depth_diff_key_slots=" .. depth_diff,
      "depth_invalid_slots=" .. depth_invalid,
      "object_static_slots=" .. object_static,
      "object_changed_slots=" .. object_changed,
      "object_draw_skip_slots=" .. object_draw_skip,
      "offscreen_like_slots=" .. offscreen_like,
      "detail=" .. table.concat(detail, " ")
    }, ",")

    if line ~= last_line then
      log(line)
      last_line = line
    end
  end
end
