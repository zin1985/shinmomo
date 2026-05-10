-- Runtime logger skeleton for Shinmomo graphics/core bridge.
-- This file intentionally contains no ROM data.
-- Fill emulator-specific memory hooks locally.

local out_dir = "runtime_out"

local function csv_line(...)
  local t = {...}
  for i = 1, #t do
    t[i] = tostring(t[i])
  end
  return table.concat(t, ",") .. "\n"
end

local function log_frame(frame, execution_frame, cutoff_index)
  -- TODO: write summarized frame row only.
  -- Keep raw VRAM/OAM/CGRAM dumps out of the repository.
end

local function log_visible(frame, rank, cluster_track_id, visible, termination_flag)
  -- TODO: write visible.csv rows.
end

local function log_oam(frame)
  -- TODO: summarize OAM ownership only.
end

local function log_dma(frame)
  -- TODO: summarize DMA channel activity only.
end

return {
  log_frame = log_frame,
  log_visible = log_visible,
  log_oam = log_oam,
  log_dma = log_dma,
}
