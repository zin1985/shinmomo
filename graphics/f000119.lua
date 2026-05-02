-- shinmomo_trace_graphics_mapchip_oam_unified_polling_v1_20260502.lua
-- BG/mapchip と visible object/OAM を同一frameでpollingする。
local OUT_PREFIX="graphics_mapchip_oam_unified_20260502"
local SAMPLE_EVERY=10
local MAX_CHAIN=96
local function list_domains()
  local r={}
  if memory and memory.getmemorydomainlist then for _,d in ipairs(memory.getmemorydomainlist()) do table.insert(r,d) end end
  return r
end
local function choose_domain(candidates)
  if not memory or not memory.getmemorydomainlist then return nil end
  local have={}; for _,d in ipairs(memory.getmemorydomainlist()) do have[d]=true end
  for _,c in ipairs(candidates) do if have[c] then return c end end
  return nil
end
local WRAM=choose_domain({"WRAM","System Bus"}) or "WRAM"
local VRAM=choose_domain({"VRAM"})
local CGRAM=choose_domain({"CGRAM"})
local OAM=choose_domain({"OAM"})
local function rb(addr,dom) dom=dom or WRAM; local ok,v=pcall(memory.readbyte,addr,dom); if ok and v then return v end; return 0 end
local function rw(addr,dom) return rb(addr,dom)+rb(addr+1,dom)*256 end
local function hash_range(start_addr,len,dom)
  if not dom then return 0 end
  local h=2166136261
  for i=0,len-1 do h=((h ~ rb(start_addr+i,dom))*16777619)&0xffffffff end
  return h
end
local function append(path,line) local f=io.open(path,"a"); if f then f:write(line,"\n"); f:close() end end
append(OUT_PREFIX.."_notes.txt","TRACE_GRAPHICS_MAPCHIP_OAM_READY")
append(OUT_PREFIX.."_notes.txt","domains="..table.concat(list_domains(),","))
append(OUT_PREFIX..".csv","frame,bg_hash0,bg_hash1,bg_hash2,cgram_hash,oam_hash,obj_head,obj_count,obj_chain_hash,oam_visible_count")
append(OUT_PREFIX.."_objects.csv","frame,slot,next,prev,sort_key,pattern,anim_state,x_lo,x_hi,y_lo,y_hi")
append(OUT_PREFIX.."_oam.csv","frame,index,y,tile,attr,x")
local function trace_frame()
  local frame=emu.framecount and emu.framecount() or 0
  local bg0=hash_range(0x0000,0x800,VRAM); local bg1=hash_range(0x0800,0x800,VRAM); local bg2=hash_range(0x1000,0x800,VRAM)
  local cg=hash_range(0x0000,0x200,CGRAM); local oh=hash_range(0x0000,0x220,OAM)
  local head=rw(0x0A61,WRAM); local slot=head&0xff; local count=0; local chain_hash=2166136261; local seen={}
  while slot~=0 and slot<0x80 and count<MAX_CHAIN and not seen[slot] do
    seen[slot]=true; count=count+1
    local nextv=rb(0x0A61+slot,WRAM); local prevv=rb(0x0A1F+slot,WRAM); local sort=rb(0x0AA3+slot,WRAM)
    local pat=rb(0x0AE5+slot,WRAM); local anim=rb(0x0E27+slot,WRAM); local xlo=rb(0x0BA5+slot,WRAM); local xhi=rb(0x0BA7+slot,WRAM); local ylo=rb(0x0C65+slot,WRAM); local yhi=rb(0x0C67+slot,WRAM)
    append(OUT_PREFIX.."_objects.csv",string.format("%d,%02X,%02X,%02X,%02X,%02X,%02X,%02X,%02X,%02X,%02X",frame,slot,nextv,prevv,sort,pat,anim,xlo,xhi,ylo,yhi))
    chain_hash=((chain_hash ~ slot ~ (sort<<8) ~ (nextv<<16))*16777619)&0xffffffff; slot=nextv
  end
  local visible=0
  if OAM then
    for i=0,127 do
      local b=i*4; local y=rb(b,OAM); local tile=rb(b+1,OAM); local attr=rb(b+2,OAM); local x=rb(b+3,OAM)
      if not (y==0xE0 and tile==0 and attr==0 and x==0) then visible=visible+1; if visible<=96 then append(OUT_PREFIX.."_oam.csv",string.format("%d,%d,%02X,%02X,%02X,%02X",frame,i,y,tile,attr,x)) end end
    end
  end
  append(OUT_PREFIX..".csv",string.format("%d,%08X,%08X,%08X,%08X,%08X,%04X,%d,%08X,%d",frame,bg0,bg1,bg2,cg,oh,head,count,chain_hash,visible))
end
local function tick() local f=emu.framecount and emu.framecount() or 0; if f%SAMPLE_EVERY==0 then trace_frame() end end
event.onframestart(tick,"shinmomo_graphics_mapchip_oam_unified_polling")
