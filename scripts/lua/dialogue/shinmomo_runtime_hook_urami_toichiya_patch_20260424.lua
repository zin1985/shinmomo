-- 新桃太郎伝説 runtime hook 追加パッチ案
-- 目的:
-- 1. といちや説明文の lineID ($12B4) 取得
-- 2. 怨みの洞窟 名前入力3本のRAM差分取得
-- 3. といちや雇用/預け金条件の金額RAM差分取得

-- 既存 main.lua の tracing toggles 付近に追加
TRACE_WINDOW_NAME_A = true -- 0x1200..0x127F
TRACE_WINDOW_NAME_B = true -- 0x1280..0x12FF
TRACE_WINDOW_WORK_D = true -- 0x1D00..0x1FFF
TRACE_WINDOW_UI     = true -- 0x1900..0x19FF
TRACE_WINDOW_MONEY  = true -- focused money/ledger variables

-- 既存 buildContextRecord(hookName, textValue) の rec 追加部分に挿入
-- ※ readRangeHex / safeHex は既存関数を利用
function appendExtraShinmomoTraceWindows(rec)
  if TRACE_WINDOW_NAME_A then
    rec[#rec+1] = "<br><b>RAM[1200..127F]</b>=" .. readRangeHex(0x1200, 0x127F)
  end
  if TRACE_WINDOW_NAME_B then
    rec[#rec+1] = "<br><b>RAM[1280..12FF]</b>=" .. readRangeHex(0x1280, 0x12FF)
  end
  if TRACE_WINDOW_WORK_D then
    rec[#rec+1] = "<br><b>RAM[1D00..1FFF]</b>=" .. readRangeHex(0x1D00, 0x1FFF)
  end
  if TRACE_WINDOW_UI then
    rec[#rec+1] = "<br><b>RAM[1900..19FF]</b>=" .. readRangeHex(0x1900, 0x19FF)
  end
  if TRACE_WINDOW_MONEY then
    local money = {}
    money[#money+1] = "1936=" .. safeHex(getMemory(0x1936, 2), 4)
    money[#money+1] = "1969=" .. safeHex(getMemory(0x1969, 2), 4)
    money[#money+1] = "001E=" .. safeHex(getMemory(0x001E, 2), 4)
    money[#money+1] = "1986=" .. safeHex(getMemory(0x1986, 1), 2)
    money[#money+1] = "198D=" .. safeHex(getMemory(0x198D, 1), 2)
    money[#money+1] = "19D5=" .. safeHex(getMemory(0x19D5, 1), 2)
    money[#money+1] = "19E5=" .. safeHex(getMemory(0x19E5, 1), 2)
    rec[#rec+1] = "<br><b>MONEY/CHOICE</b>=" .. table.concat(money, " ")
    rec[#rec+1] = "<br><b>LEDGER[1B15..1B45]</b>=" .. readRangeHex(0x1B15, 0x1B45)
  end
end

-- 既存 buildContextRecord 内の RAM[1180..119F] 出力後に以下を1行追加する:
-- appendExtraShinmomoTraceWindows(rec)

-- 推奨 marker 運用:
-- marker:toichiya_before_explain
-- marker:toichiya_after_explain
-- marker:toichiya_deposit_30000_minus
-- marker:toichiya_deposit_30001_plus
-- marker:toichiya_before_hire
-- marker:toichiya_after_hire
-- marker:urami_before_prompt
-- marker:urami_prompt_1_before_input
-- marker:urami_prompt_1_after_input_aaaa
-- marker:urami_prompt_2_before_input
-- marker:urami_prompt_2_after_input_iiii
-- marker:urami_prompt_3_before_input
-- marker:urami_prompt_3_after_input_uuuu
-- marker:urami_enemy_name_display
