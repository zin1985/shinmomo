-- shinmomo_trace_dialogue_v31_mode02_bd98_chain_snes9x_20260427.lua
-- v31: standalone quiet logger. C0:BD98 mode02 bitstream decoder + chained stream scan
--
-- 目的:
--   YouTube等の元Luaが手元になくても、ROM静的解析から C0:BD98 の特殊sourceを実際に展開する。
--   文脈予測語・固定置換はしない。
--
-- 分かったこと:
--   $12AA=02 は plain text ではなく、C0:BD98 の bitstream/tree decoder。
--   C0:BD98 は $7E..$83 を使い、BDE4/BDEC/BEEB/BF0B/C00A のテーブルで1 symbolを復元する。
--
-- 出力:
--   TRACE_DIALOGUE_V31_MODE02_BEST
--   TRACE_DIALOGUE_V31_MODE02_CANDIDATES
--   TRACE_DIALOGUE_V31_ALIVE

local READ_SYMBOLS = 180
local DISPLAY_IDLE_FLUSH_FRAMES = 90
local TOKEN_REPEAT_SUPPRESS_FRAMES = 3
local MODE02_DECODE_MIN_GAP = 24

-- v31 flags:
-- v29 was only a paste-in patch; this v30 is a full standalone Lua.
local TRACE_TOKENS = false              -- true only when you need per-frame staging debug
local TRACE_SCREEN_OBSERVED = false     -- false by default; staging registers are noisy
local TRACE_MODE02_BEST = true          -- best decoded BD98 stream
local TRACE_MODE02_CANDIDATES = true    -- compact candidate list when best changes
local TRACE_MODE02_CHAIN = true         -- decode several consecutive <00>-terminated strings from the same BD98 bitstream state
local CHAIN_STREAMS = 6                 -- enough to catch current line when pointer is a bundle base
local TRACE_VERBOSE_EVENTS = false      -- huge; normally false
local TRACE_ALIVE_FRAMES = 600          -- heartbeat so it never looks frozen
local MIN_GOOD_SCORE = 22               -- candidate threshold

local function list_domains()
  local ok, domains = pcall(function() return memory.getmemorydomainlist() end)
  if ok and domains then return domains end
  return {}
end

local DOMAINS = list_domains()

local function choose_domain(preferred)
  for _, want in ipairs(preferred) do
    for _, got in ipairs(DOMAINS) do
      if got == want then return got end
    end
  end
  for _, want in ipairs(preferred) do
    local wl = string.lower(want)
    for _, got in ipairs(DOMAINS) do
      if string.find(string.lower(got), wl, 1, true) then return got end
    end
  end
  return nil
end

local WRAM_DOMAIN = choose_domain({"WRAM", "Snes WRAM", "SNES WRAM", "Main RAM"}) or DOMAINS[1]
local ROM_DOMAIN  = choose_domain({"CARTROM", "Cart ROM", "Cartridge ROM", "ROM", "Snes ROM", "SNES ROM"})

local function domain_size(domain)
  if domain == nil then return 0 end
  local ok, sz = pcall(function() return memory.getmemorydomainsize(domain) end)
  if ok and sz then return sz end
  if domain == WRAM_DOMAIN then return 0x20000 end
  if domain == ROM_DOMAIN then return 0x800000 end
  return 0
end

local function safe_read_u8(addr, domain)
  if domain == nil then return nil end
  local sz = domain_size(domain)
  if sz > 0 and (addr < 0 or addr >= sz) then return nil end
  local ok, v = pcall(function() return memory.read_u8(addr, domain) end)
  if ok then return v end
  return nil
end

local function wram8(addr)
  return safe_read_u8(addr, WRAM_DOMAIN) or 0
end

local function h2(v) if v == nil then return "??" end return string.format("%02X", v % 0x100) end
local function h4(v) if v == nil then return "????" end return string.format("%04X", v % 0x10000) end
local function h6(v) if v == nil then return "??????" end return string.format("%06X", v % 0x1000000) end

local function logLine(s)
  if console and console.log then console.log(s)
  elseif client and client.log then client.log(s)
  else print(s) end
end

local function trunc(s, n)
  if s == nil then return "" end
  n = n or 900
  if string.len(s) <= n then return s end
  return string.sub(s, 1, n) .. "...<truncated>"
end

local MOMO3 = {
  ["0"] = "",
  ["1"] = "",
  ["3"] = "",
  ["4"] = "",
  ["5"] = "",
  ["6"] = "",
  ["8"] = "",
  ["B"] = "",
  ["F"] = "",
  ["50"] = " ",
  ["51"] = "0",
  ["52"] = "1",
  ["53"] = "2",
  ["54"] = "3",
  ["55"] = "4",
  ["56"] = "5",
  ["57"] = "6",
  ["58"] = "7",
  ["59"] = "8",
  ["5A"] = "9",
  ["5B"] = "?",
  ["5C"] = "!",
  ["5D"] = "、",
  ["5E"] = "。",
  ["5F"] = "…",
  ["60"] = "·",
  ["61"] = "A",
  ["62"] = "B",
  ["63"] = "C",
  ["64"] = "D",
  ["65"] = "E",
  ["66"] = "F",
  ["67"] = "G",
  ["68"] = "H",
  ["69"] = "I",
  ["6A"] = "J",
  ["6B"] = "K",
  ["6C"] = "L",
  ["6D"] = "M",
  ["6E"] = "N",
  ["6F"] = "O",
  ["70"] = "P",
  ["71"] = "Q",
  ["72"] = "R",
  ["73"] = "S",
  ["74"] = "T",
  ["75"] = "U",
  ["76"] = "V",
  ["77"] = "W",
  ["78"] = "X",
  ["79"] = "Y",
  ["7A"] = "Z",
  ["7B"] = "(",
  ["7C"] = ")",
  ["7D"] = "「",
  ["7E"] = "」",
  ["7F"] = "〜",
  ["80"] = "ー",
  ["81"] = "?",
  ["82"] = "c",
  ["83"] = "+",
  ["84"] = "-",
  ["85"] = "/",
  ["86"] = "㎏",
  ["87"] = "->",
  ["88"] = "<-",
  ["89"] = "<",
  ["8A"] = ">",
  ["8B"] = "『",
  ["8C"] = "』",
  ["8D"] = "?",
  ["8E"] = "?",
  ["8F"] = "?",
  ["90"] = "あ",
  ["91"] = "い",
  ["92"] = "う",
  ["93"] = "え",
  ["94"] = "お",
  ["95"] = "か",
  ["96"] = "き",
  ["97"] = "く",
  ["98"] = "け",
  ["99"] = "こ",
  ["9A"] = "さ",
  ["9B"] = "し",
  ["9C"] = "す",
  ["9D"] = "せ",
  ["9E"] = "そ",
  ["9F"] = "た",
  ["A0"] = "ち",
  ["A1"] = "つ",
  ["A2"] = "て",
  ["A3"] = "と",
  ["A4"] = "な",
  ["A5"] = "に",
  ["A6"] = "ぬ",
  ["A7"] = "ね",
  ["A8"] = "の",
  ["A9"] = "は",
  ["AA"] = "ひ",
  ["AB"] = "ふ",
  ["AC"] = "へ",
  ["AD"] = "ほ",
  ["AE"] = "ま",
  ["AF"] = "み",
  ["B0"] = "む",
  ["B1"] = "め",
  ["B2"] = "も",
  ["B3"] = "や",
  ["B4"] = "ゆ",
  ["B5"] = "よ",
  ["B6"] = "ら",
  ["B7"] = "り",
  ["B8"] = "る",
  ["B9"] = "れ",
  ["BA"] = "ろ",
  ["BB"] = "わ",
  ["BC"] = "を",
  ["BD"] = "ん",
  ["BE"] = "で",
  ["BF"] = "?",
  ["C0"] = "?",
  ["C1"] = "?",
  ["C2"] = "?",
  ["C3"] = "?",
  ["C4"] = "?",
  ["C5"] = "?",
  ["C6"] = "?",
  ["C7"] = "?",
  ["C8"] = "?",
  ["C9"] = "?",
  ["CA"] = "?",
  ["CB"] = "?",
  ["CC"] = "?",
  ["CD"] = "?",
  ["CE"] = "?",
  ["CF"] = "?",
  ["D0"] = "が",
  ["D1"] = "ぎ",
  ["D2"] = "ぐ",
  ["D3"] = "げ",
  ["D4"] = "ご",
  ["D5"] = "ざ",
  ["D6"] = "じ",
  ["D7"] = "ず",
  ["D8"] = "ぜ",
  ["D9"] = "ぞ",
  ["DA"] = "だ",
  ["DB"] = "ぢ",
  ["DC"] = "づ",
  ["DD"] = "ど",
  ["DE"] = "ば",
  ["DF"] = "び",
  ["E0"] = "ぶ",
  ["E1"] = "べ",
  ["E2"] = "ぼ",
  ["E3"] = "ぱ",
  ["E4"] = "ぴ",
  ["E5"] = "ぷ",
  ["E6"] = "ぺ",
  ["E7"] = "ぽ",
  ["E8"] = "?",
  ["E9"] = "?",
  ["EA"] = "?",
  ["EB"] = "?",
  ["EC"] = "?",
  ["ED"] = "?",
  ["EE"] = "?",
  ["EF"] = "?",
  ["F0"] = "ぁ",
  ["F1"] = "ぃ",
  ["F2"] = "ぅ",
  ["F3"] = "ぇ",
  ["F4"] = "ぉ",
  ["F5"] = "っ",
  ["F6"] = "ゃ",
  ["F7"] = "ゅ",
  ["F8"] = "ょ",
  ["F9"] = "ゎ",
  ["FA"] = "?",
  ["FB"] = "?",
  ["FC"] = "?",
  ["FD"] = "?",
  ["FE"] = "?",
  ["FF"] = "?",
  ["1800"] = "桃",
  ["1801"] = "太",
  ["1802"] = "郎",
  ["1803"] = "金",
  ["1804"] = "浦",
  ["1805"] = "島",
  ["1806"] = "寝",
  ["1807"] = "雪",
  ["1808"] = "夜",
  ["1809"] = "叉",
  ["180A"] = "姫",
  ["180B"] = "雷",
  ["180C"] = "風",
  ["180D"] = "神",
  ["180E"] = "毒",
  ["180F"] = "強",
  ["1810"] = "東",
  ["1811"] = "西",
  ["1812"] = "南",
  ["1813"] = "北",
  ["1814"] = "村",
  ["1815"] = "体",
  ["1816"] = "力",
  ["1817"] = "心",
  ["1818"] = "段",
  ["1819"] = "両",
  ["181A"] = "話",
  ["181B"] = "術",
  ["181C"] = "道",
  ["181D"] = "具",
  ["181E"] = "調",
  ["181F"] = "装",
  ["1820"] = "備",
  ["1821"] = "命",
  ["1822"] = "令",
  ["1823"] = "素",
  ["1824"] = "母",
  ["1825"] = "乱",
  ["1826"] = "針",
  ["1827"] = "族",
  ["1828"] = "好",
  ["1829"] = "安",
  ["182A"] = "臣",
  ["182B"] = "衛",
  ["182C"] = "軌",
  ["182D"] = "然",
  ["182E"] = "校",
  ["182F"] = "徒",
  ["1830"] = "民",
  ["1831"] = "妹",
  ["1832"] = "限",
  ["1833"] = "休",
  ["1834"] = "巣",
  ["1835"] = "竿",
  ["1836"] = "背",
  ["1837"] = "絶",
  ["1838"] = "草",
  ["1839"] = "級",
  ["183A"] = "意",
  ["183B"] = "祖",
  ["183C"] = "親",
  ["183D"] = "奴",
  ["183E"] = "晩",
  ["183F"] = "読",
  ["1840"] = "大",
  ["1841"] = "王",
  ["1842"] = "技",
  ["1843"] = "松",
  ["1844"] = "竹",
  ["1845"] = "梅",
  ["1846"] = "麻",
  ["1847"] = "人",
  ["1848"] = "気",
  ["1849"] = "度",
  ["184A"] = "上",
  ["184B"] = "下",
  ["184C"] = "刀",
  ["184D"] = "割",
  ["184E"] = "小",
  ["184F"] = "霞",
  ["1850"] = "銀",
  ["1851"] = "次",
  ["1852"] = "吉",
  ["1853"] = "犬",
  ["1854"] = "何",
  ["1855"] = "制",
  ["1856"] = "総",
  ["1857"] = "揮",
  ["1858"] = "演",
  ["1859"] = "口",
  ["185A"] = "宏",
  ["185B"] = "原",
  ["185C"] = "画",
  ["185D"] = "居",
  ["185E"] = "考",
  ["185F"] = "幸",
  ["1860"] = "楽",
  ["1861"] = "関",
  ["1862"] = "之",
  ["1863"] = "監",
  ["1864"] = "督",
  ["1865"] = "哲",
  ["1866"] = "美",
  ["1867"] = "藤",
  ["1868"] = "康",
  ["1869"] = "博",
  ["186A"] = "丈",
  ["186B"] = "夫",
  ["186C"] = "鳥",
  ["186D"] = "特",
  ["186E"] = "念",
  ["186F"] = "勝",
  ["1870"] = "社",
  ["1871"] = "男",
  ["1872"] = "市",
  ["1873"] = "匹",
  ["1874"] = "巻",
  ["1875"] = "富",
  ["1876"] = "止",
  ["1877"] = "等",
  ["1878"] = "賞",
  ["1879"] = "商",
  ["187A"] = "色",
  ["187B"] = "今",
  ["187C"] = "集",
  ["187D"] = "宝",
  ["187E"] = "情",
  ["187F"] = "第",
  ["1880"] = "一",
  ["1881"] = "三",
  ["1882"] = "九",
  ["1883"] = "千",
  ["1884"] = "面",
  ["1885"] = "弦",
  ["1886"] = "待",
  ["1887"] = "満",
  ["1888"] = "子",
  ["1889"] = "山",
  ["188A"] = "女",
  ["188B"] = "木",
  ["188C"] = "天",
  ["188D"] = "牛",
  ["188E"] = "不",
  ["188F"] = "火",
  ["1890"] = "水",
  ["1891"] = "文",
  ["1892"] = "月",
  ["1893"] = "白",
  ["1894"] = "乏",
  ["1895"] = "世",
  ["1896"] = "氷",
  ["1897"] = "台",
  ["1898"] = "主",
  ["1899"] = "切",
  ["189A"] = "生",
  ["189B"] = "衣",
  ["189C"] = "地",
  ["189D"] = "虫",
  ["189E"] = "死",
  ["189F"] = "血",
  ["18A0"] = "吸",
  ["18A1"] = "多",
  ["18A2"] = "呑",
  ["18A3"] = "耳",
  ["18A4"] = "伊",
  ["18A5"] = "伏",
  ["18A6"] = "毎",
  ["18A7"] = "旬",
  ["18A8"] = "如",
  ["18A9"] = "沙",
  ["18AA"] = "貝",
  ["18AB"] = "赤",
  ["18AC"] = "邪",
  ["18AD"] = "坊",
  ["18AE"] = "吹",
  ["18AF"] = "吽",
  ["18B0"] = "見",
  ["18B1"] = "尾",
  ["18B2"] = "身",
  ["18B3"] = "魔",
  ["18B4"] = "受",
  ["18B5"] = "車",
  ["18B6"] = "父",
  ["18B7"] = "乙",
  ["18B8"] = "昔",
  ["18B9"] = "来",
  ["18BA"] = "化",
  ["18BB"] = "舟",
  ["18BC"] = "欲",
  ["18BD"] = "兄",
  ["18BE"] = "弟",
  ["18BF"] = "顔",
  ["18C0"] = "岩",
  ["18C1"] = "門",
  ["18C2"] = "青",
  ["18C3"] = "虎",
  ["18C4"] = "狗",
  ["18C5"] = "卒",
  ["18C6"] = "阿",
  ["18C7"] = "知",
  ["18C8"] = "狐",
  ["18C9"] = "怪",
  ["18CA"] = "臥",
  ["18CB"] = "苦",
  ["18CC"] = "河",
  ["18CD"] = "雨",
  ["18CE"] = "波",
  ["18CF"] = "刹",
  ["18D0"] = "勇",
  ["18D1"] = "食",
  ["18D2"] = "首",
  ["18D3"] = "炭",
  ["18D4"] = "海",
  ["18D5"] = "逆",
  ["18D6"] = "茨",
  ["18D7"] = "界",
  ["18D8"] = "蛯",
  ["18D9"] = "飛",
  ["18DA"] = "是",
  ["18DB"] = "鬼",
  ["18DC"] = "剛",
  ["18DD"] = "馬",
  ["18DE"] = "竜",
  ["18DF"] = "粉",
  ["18E0"] = "酒",
  ["18E1"] = "殺",
  ["18E2"] = "狼",
  ["18E3"] = "骨",
  ["18E4"] = "害",
  ["18E5"] = "翁",
  ["18E6"] = "黄",
  ["18E7"] = "漁",
  ["18E8"] = "黒",
  ["18E9"] = "貪",
  ["18EA"] = "異",
  ["18EB"] = "悪",
  ["18EC"] = "蛇",
  ["18ED"] = "婆",
  ["18EE"] = "魚",
  ["18EF"] = "船",
  ["18F0"] = "葉",
  ["18F1"] = "象",
  ["18F2"] = "無",
  ["18F3"] = "童",
  ["18F4"] = "嵐",
  ["18F5"] = "極",
  ["18F6"] = "喜",
  ["18F7"] = "悲",
  ["18F8"] = "儀",
  ["18F9"] = "式",
  ["18FA"] = "菩",
  ["18FB"] = "薩",
  ["18FC"] = "枯",
  ["18FD"] = "終",
  ["18FE"] = "値",
  ["18FF"] = "決",
  ["1900"] = "賊",
  ["1901"] = "獏",
  ["1902"] = "福",
  ["1903"] = "猿",
  ["1904"] = "獄",
  ["1905"] = "緑",
  ["1906"] = "漂",
  ["1907"] = "様",
  ["1908"] = "奪",
  ["1909"] = "聞",
  ["190A"] = "餓",
  ["190B"] = "魃",
  ["190C"] = "魅",
  ["190D"] = "蓮",
  ["190E"] = "霊",
  ["190F"] = "敵",
  ["1910"] = "龍",
  ["1911"] = "燈",
  ["1912"] = "醜",
  ["1913"] = "磯",
  ["1914"] = "羅",
  ["1915"] = "図",
  ["1916"] = "役",
  ["1917"] = "利",
  ["1918"] = "軍",
  ["1919"] = "沼",
  ["191A"] = "向",
  ["191B"] = "板",
  ["191C"] = "国",
  ["191D"] = "橋",
  ["191E"] = "改",
  ["191F"] = "員",
  ["1920"] = "病",
  ["1921"] = "闘",
  ["1922"] = "器",
  ["1923"] = "動",
  ["1924"] = "残",
  ["1925"] = "右",
  ["1926"] = "少",
  ["1927"] = "法",
  ["1928"] = "智",
  ["1929"] = "将",
  ["192A"] = "闇",
  ["192B"] = "味",
  ["192C"] = "頭",
  ["192D"] = "均",
  ["192E"] = "位",
  ["192F"] = "已",
  ["1930"] = "参",
  ["1931"] = "題",
  ["1932"] = "歌",
  ["1933"] = "野",
  ["1934"] = "寺",
  ["1935"] = "材",
  ["1936"] = "栄",
  ["1937"] = "思",
  ["1938"] = "直",
  ["1939"] = "君",
  ["193A"] = "徳",
  ["193B"] = "近",
  ["193C"] = "抜",
  ["193D"] = "砂",
  ["193E"] = "浜",
  ["193F"] = "隕",
  ["1940"] = "吐",
  ["1941"] = "幻",
  ["1942"] = "影",
  ["1943"] = "百",
  ["1944"] = "姥",
  ["1945"] = "歴",
  ["1946"] = "史",
  ["1947"] = "数",
  ["1948"] = "学",
  ["1949"] = "豆",
  ["194A"] = "土",
  ["194B"] = "妖",
  ["194C"] = "五",
  ["194D"] = "丁",
  ["194E"] = "鉄",
  ["194F"] = "丸",
  ["1950"] = "杖",
  ["1951"] = "指",
  ["1952"] = "姉",
  ["1953"] = "運",
  ["1954"] = "毛",
  ["1955"] = "肉",
  ["1956"] = "臼",
  ["1957"] = "歯",
  ["1958"] = "盲",
  ["1959"] = "腸",
  ["195A"] = "肛",
  ["195B"] = "助",
  ["195C"] = "代",
  ["195D"] = "曲",
  ["195E"] = "湯",
  ["195F"] = "番",
  ["1960"] = "汁",
  ["1961"] = "並",
  ["1962"] = "蜂",
  ["1963"] = "乃",
  ["1964"] = "語",
  ["1965"] = "双",
  ["1966"] = "遊",
  ["1967"] = "報",
  ["1968"] = "告",
  ["1969"] = "矛",
  ["196A"] = "盾",
  ["196B"] = "亀",
  ["196C"] = "進",
  ["196D"] = "占",
  ["196E"] = "産",
  ["196F"] = "美",
  ["1970"] = "雲",
  ["1971"] = "猛",
  ["1972"] = "嫌",
  ["1973"] = "銭",
  ["1974"] = "胸",
  ["1975"] = "祭",
  ["1976"] = "娘",
  ["1977"] = "腕",
  ["1978"] = "林",
  ["1979"] = "開",
  ["197A"] = "戻",
  ["197B"] = "英",
  ["197C"] = "泣",
  ["197D"] = "潜",
  ["197E"] = "発",
  ["197F"] = "用",
  ["1980"] = "砦",
  ["1981"] = "花",
  ["1982"] = "咲",
  ["1983"] = "屋",
  ["1984"] = "敷",
  ["1985"] = "音",
  ["1986"] = "洞",
  ["1987"] = "窟",
  ["1988"] = "仙",
  ["1989"] = "庵",
  ["198A"] = "足",
  ["198B"] = "柄",
  ["198C"] = "養",
  ["198D"] = "老",
  ["198E"] = "滝",
  ["198F"] = "謎",
  ["1990"] = "解",
  ["1991"] = "塔",
  ["1992"] = "恨",
  ["1993"] = "持",
  ["1994"] = "重",
  ["1995"] = "職",
  ["1996"] = "路",
  ["1997"] = "溝",
  ["1998"] = "低",
  ["1999"] = "泉",
  ["199A"] = "家",
  ["199B"] = "旅",
  ["199C"] = "立",
  ["199D"] = "鹿",
  ["199E"] = "角",
  ["199F"] = "里",
  ["19A0"] = "宮",
  ["19A1"] = "城",
  ["19A2"] = "微",
  ["19A3"] = "笑",
  ["19A4"] = "希",
  ["19A5"] = "望",
  ["19A6"] = "都",
  ["19A7"] = "々",
  ["19A8"] = "蟹",
  ["19A9"] = "七",
  ["19AA"] = "夕",
  ["19AB"] = "畑",
  ["19AC"] = "名",
  ["19AD"] = "取",
  ["19AE"] = "郷",
  ["19AF"] = "雀",
  ["19B0"] = "宿",
  ["19B1"] = "静",
  ["19B2"] = "豊",
  ["19B3"] = "殿",
  ["19B4"] = "階",
  ["19B5"] = "仲",
  ["19B6"] = "間",
  ["19B7"] = "八",
  ["19B8"] = "部",
  ["19B9"] = "床",
  ["19BA"] = "谷",
  ["19BB"] = "川",
  ["19BC"] = "爪",
  ["19BD"] = "痕",
  ["19BE"] = "修",
  ["19BF"] = "行",
  ["19C0"] = "茶",
  ["19C1"] = "店",
  ["19C2"] = "袋",
  ["19C3"] = "手",
  ["19C4"] = "売",
  ["19C5"] = "品",
  ["19C6"] = "兵",
  ["19C7"] = "差",
  ["19C8"] = "額",
  ["19C9"] = "新",
  ["19CA"] = "買",
  ["19CB"] = "焼",
  ["19CC"] = "出",
  ["19CD"] = "物",
  ["19CE"] = "薬",
  ["19CF"] = "作",
  ["19D0"] = "説",
  ["19D1"] = "明",
  ["19D2"] = "堀",
  ["19D3"] = "刃",
  ["19D4"] = "包",
  ["19D5"] = "声",
  ["19D6"] = "餌",
  ["19D7"] = "入",
  ["19D8"] = "引",
  ["19D9"] = "前",
  ["19DA"] = "泊",
  ["19DB"] = "私",
  ["19DC"] = "井",
  ["19DD"] = "戸",
  ["19DE"] = "回",
  ["19DF"] = "復",
  ["19E0"] = "万",
  ["19E1"] = "皿",
  ["19E2"] = "全",
  ["19E3"] = "平",
  ["19E4"] = "和",
  ["19E5"] = "暗",
  ["19E6"] = "記",
  ["19E7"] = "時",
  ["19E8"] = "光",
  ["19E9"] = "者",
  ["19EA"] = "江",
  ["19EB"] = "穴",
  ["19EC"] = "怨",
  ["19ED"] = "牢",
  ["19EE"] = "夢",
  ["19EF"] = "虹",
  ["19F0"] = "左",
  ["19F1"] = "源",
  ["19F2"] = "内",
  ["19F3"] = "奈",
  ["19F4"] = "落",
  ["19F5"] = "縄",
  ["19F6"] = "池",
  ["19F7"] = "衆",
  ["19F8"] = "合",
  ["19F9"] = "焦",
  ["19FA"] = "熱",
  ["19FB"] = "寒",
  ["19FC"] = "鼻",
  ["19FD"] = "途",
  ["19FE"] = "ゞ",
  ["19FF"] = "最",
  ["1A00"] = "後",
  ["1A01"] = "先",
  ["1A02"] = "菓",
  ["1A03"] = "日",
  ["1A04"] = "本",
  ["1A05"] = "辰",
  ["1A06"] = "巳",
  ["1A07"] = "銘",
  ["1A08"] = "信",
  ["1A09"] = "糸",
  ["1A0A"] = "呂",
  ["1A0B"] = "年",
  ["1A0C"] = "笛",
  ["1A0D"] = "投",
  ["1A0E"] = "箱",
  ["1A0F"] = "自",
  ["1A10"] = "在",
  ["1A11"] = "歩",
  ["1A12"] = "打",
  ["1A13"] = "創",
  ["1A14"] = "崑",
  ["1A15"] = "崙",
  ["1A16"] = "順",
  ["1A17"] = "以",
  ["1A18"] = "攻",
  ["1A19"] = "撃",
  ["1A1A"] = "言",
  ["1A1B"] = "守",
  ["1A1C"] = "戦",
  ["1A1D"] = "逃",
  ["1A1E"] = "相",
  ["1A1F"] = "撲",
  ["1A20"] = "砲",
  ["1A21"] = "鳳",
  ["1A22"] = "凰",
  ["1A23"] = "冬",
  ["1A24"] = "方",
  ["1A25"] = "医",
  ["1A26"] = "工",
  ["1A27"] = "末",
  ["1A28"] = "計",
  ["1A29"] = "凶",
  ["1A2A"] = "呪",
  ["1A2B"] = "友",
  ["1A2C"] = "個",
  ["1A2D"] = "料",
  ["1A2E"] = "亭",
  ["1A2F"] = "志",
  ["1A30"] = "当",
  ["1A31"] = "理",
  ["1A32"] = "晶",
  ["1A33"] = "場",
  ["1A34"] = "所",
  ["1A35"] = "使",
  ["1A36"] = "沈",
  ["1A37"] = "汚",
  ["1A38"] = "?",
  ["1A39"] = "?",
  ["1A3A"] = "?",
  ["1A3B"] = "?",
  ["1A3C"] = "?",
  ["1A3D"] = "?",
  ["1A3E"] = "?",
  ["1A3F"] = "?",
  ["1A40"] = "瓦",
  ["1A41"] = "鎖",
  ["1A42"] = "釡",
  ["1A43"] = "兜",
  ["1A44"] = "毘",
  ["1A45"] = "剣",
  ["1A46"] = "玄",
  ["1A47"] = "武",
  ["1A48"] = "朱",
  ["1A49"] = "予",
  ["1A4A"] = "皮",
  ["1A4B"] = "胴",
  ["1A4C"] = "枚",
  ["1A4D"] = "二",
  ["1A4E"] = "鎧",
  ["1A4F"] = "腹",
  ["1A50"] = "綿",
  ["1A51"] = "防",
  ["1A52"] = "高",
  ["1A53"] = "津",
  ["1A54"] = "正",
  ["1A55"] = "義",
  ["1A56"] = "凪",
  ["1A57"] = "朝",
  ["1A58"] = "師",
  ["1A59"] = "着",
  ["1A5A"] = "潮",
  ["1A5B"] = "琥",
  ["1A5C"] = "珀",
  ["1A5D"] = "真",
  ["1A5E"] = "珠",
  ["1A5F"] = "流",
  ["1A60"] = "星",
  ["1A61"] = "愛",
  ["1A62"] = "桜",
  ["1A63"] = "十",
  ["1A64"] = "単",
  ["1A65"] = "牙",
  ["1A66"] = "深",
  ["1A67"] = "紅",
  ["1A68"] = "絹",
  ["1A69"] = "綾",
  ["1A6A"] = "折",
  ["1A6B"] = "羽",
  ["1A6C"] = "薄",
  ["1A6D"] = "菜",
  ["1A6E"] = "柳",
  ["1A6F"] = "長",
  ["1A70"] = "隼",
  ["1A71"] = "団",
  ["1A72"] = "孫",
  ["1A73"] = "六",
  ["1A74"] = "菊",
  ["1A75"] = "字",
  ["1A76"] = "染",
  ["1A77"] = "棒",
  ["1A78"] = "銅",
  ["1A79"] = "炎",
  ["1A7A"] = "怒",
  ["1A7B"] = "独",
  ["1A7C"] = "鈷",
  ["1A7D"] = "錫",
  ["1A7E"] = "稲",
  ["1A7F"] = "妻",
  ["1A80"] = "空",
  ["1A81"] = "荒",
  ["1A82"] = "越",
  ["1A83"] = "中",
  ["1A84"] = "共",
  ["1A85"] = "迦",
  ["1A86"] = "楼",
  ["1A87"] = "伐",
  ["1A88"] = "四",
  ["1A89"] = "形",
  ["1A8A"] = "息",
  ["1A8B"] = "灼",
  ["1A8C"] = "弓",
  ["1A8D"] = "矢",
  ["1A8E"] = "張",
  ["1A8F"] = "侍",
  ["1A90"] = "有",
  ["1A91"] = "献",
  ["1A92"] = "加",
  ["1A93"] = "弱",
  ["1A94"] = "誰",
  ["1A95"] = "対",
  ["1A96"] = "負",
  ["1A97"] = "飲",
  ["1A98"] = "倍",
  ["1A99"] = "連",
  ["1A9A"] = "続",
  ["1A9B"] = "釣",
  ["1A9C"] = "客",
  ["1A9D"] = "奇",
  ["1A9E"] = "?",
  ["1A9F"] = "?",
  ["1AA0"] = "?",
  ["1AA1"] = "?",
  ["1AA2"] = "?",
  ["1AA3"] = "?",
  ["1AA4"] = "?",
  ["1AA5"] = "?",
  ["1AA6"] = "?",
  ["1AA7"] = "?",
  ["1AA8"] = "?",
  ["1AA9"] = "?",
  ["1AAA"] = "?",
  ["1AAB"] = "?",
  ["1AAC"] = "?",
  ["1AAD"] = "?",
  ["1AAE"] = "?",
  ["1AAF"] = "?",
  ["1AB0"] = "?",
  ["1AB1"] = "?",
  ["1AB2"] = "?",
  ["1AB3"] = "?",
  ["1AB4"] = "?",
  ["1AB5"] = "?",
  ["1AB6"] = "?",
  ["1AB7"] = "?",
  ["1AB8"] = "退",
  ["1AB9"] = "脱",
  ["1ABA"] = "罪",
  ["1ABB"] = "魂",
  ["1ABC"] = "億",
  ["1ABD"] = "現",
  ["1ABE"] = "沓",
  ["1ABF"] = "系",
  ["1AC0"] = "鳴",
  ["1AC1"] = "電",
  ["1AC2"] = "旋",
  ["1AC3"] = "突",
  ["1AC4"] = "烈",
  ["1AC5"] = "走",
  ["1AC6"] = "忍",
  ["1AC7"] = "尻",
  ["1AC8"] = "筒",
  ["1AC9"] = "涙",
  ["1ACA"] = "壷",
  ["1ACB"] = "元",
  ["1ACC"] = "玉",
  ["1ACD"] = "恒",
  ["1ACE"] = "丹",
  ["1ACF"] = "消",
  ["1AD0"] = "寄",
  ["1AD1"] = "効",
  ["1AD2"] = "能",
  ["1AD3"] = "隱",
  ["1AD4"] = "蔵",
  ["1AD5"] = "札",
  ["1AD6"] = "根",
  ["1AD7"] = "性",
  ["1AD8"] = "照",
  ["1AD9"] = "石",
  ["1ADA"] = "晴",
  ["1ADB"] = "呼",
  ["1ADC"] = "会",
  ["1ADD"] = "塲",
  ["1ADE"] = "書",
  ["1ADF"] = "秘",
  ["1AE0"] = "伝",
  ["1AE1"] = "早",
  ["1AE2"] = "禁",
  ["1AE3"] = "断",
  ["1AE4"] = "古",
  ["1AE5"] = "券",
  ["1AE6"] = "鈴",
  ["1AE7"] = "鏡",
  ["1AE8"] = "室",
  ["1AE9"] = "樹",
  ["1AEA"] = "事",
  ["1AEB"] = "ゐ",
  ["1AEC"] = "甚",
  ["1AED"] = "痛",
  ["1AEE"] = "盗",
  ["1AEF"] = "苔",
  ["1AF0"] = "森",
  ["1AF1"] = "祠",
  ["1AF2"] = "半",
  ["1AF3"] = "分",
  ["1AF4"] = "目",
  ["1AF5"] = "点",
  ["1AF6"] = "漢",
  ["1AF7"] = "問",
  ["1AF8"] = "算",
  ["1AF9"] = "漬",
  ["1AFA"] = "細",
  ["1AFB"] = "崩",
  ["1AFC"] = "追",
  ["1AFD"] = "統",
  ["1AFE"] = "願",
  ["1AFF"] = "歳",
  ["1B00"] = "増",
  ["1B01"] = "田",
  ["1B02"] = "景",
  ["1B03"] = "良",
  ["1B04"] = "澤",
  ["1B05"] = "隆",
  ["1B06"] = "試",
  ["1B07"] = "達",
  ["1B08"] = "也",
  ["1B09"] = "崇",
  ["1B0A"] = "篤",
  ["1B0B"] = "佐",
  ["1B0C"] = "久",
  ["1B0D"] = "彦",
  ["1B0E"] = "保",
  ["1B0F"] = "若",
  ["1B10"] = "由",
  ["1B11"] = "弘",
  ["1B12"] = "恵",
  ["1B13"] = "沢",
  ["1B14"] = "笠",
  ["1B15"] = "敏",
  ["1B16"] = "秀",
  ["1B17"] = "貴",
  ["1B18"] = "昭",
  ["1B19"] = "洋",
  ["1B1A"] = "章",
  ["1B1B"] = "浩",
  ["1B1C"] = "治",
  ["1B1D"] = "茂",
  ["1B1E"] = "可",
  ["1B1F"] = "笹",
  ["1B20"] = "忠",
  ["1B21"] = "俊",
  ["1B22"] = "典",
  ["1B23"] = "熊",
  ["1B24"] = "岡",
  ["1B25"] = "経",
  ["1B26"] = "雅",
  ["1B27"] = "米",
  ["1B28"] = "捨",
  ["1B29"] = "版",
  ["1B2A"] = "外",
  ["1B2B"] = "広",
  ["1B2C"] = "果",
  ["1B2D"] = "録",
  ["1B2E"] = "登",
  ["1B2F"] = "別",
  ["1B30"] = "府",
  ["1B31"] = "温",
  ["1B32"] = "砕",
  ["1B33"] = "支",
  ["1B34"] = "配",
  ["1B35"] = "士",
  ["1B36"] = "斧",
  ["1B37"] = "那",
  ["1B38"] = "地",
  ["1B39"] = "敗",
  ["1B3A"] = "仁",
  ["1B3B"] = "礼",
  ["1B3C"] = "須",
  ["1B3D"] = "弥",
  ["1B3E"] = "州",
  ["1B3F"] = "辺",
  ["1B40"] = "葦",
  ["1B41"] = "週",
  ["1B42"] = "短",
  ["1B43"] = "公",
  ["1B44"] = "円",
  ["1B45"] = "偶",
  ["1B46"] = "変",
  ["1B47"] = "帰",
  ["1B48"] = "通",
  ["1B49"] = "評",
  ["1B4A"] = "腰",
  ["1B4B"] = "膀",
  ["1B4C"] = "胱",
  ["1B4D"] = "膚",
  ["1B4E"] = "肝",
  ["1B4F"] = "臓",
  ["1B50"] = "肥",
  ["1B51"] = "脳",
  ["1B52"] = "管",
  ["1B53"] = "盤",
  ["1B54"] = "夏",
  ["1B55"] = "腱",
  ["1B56"] = "垂",
  ["1B57"] = "乳",
  ["1B58"] = "陰",
  ["1B59"] = "筋",
  ["1B5A"] = "踵",
  ["1B5B"] = "節",
  ["1B5C"] = "房",
  ["1B5D"] = "胆",
  ["1B5E"] = "彩",
  ["1B5F"] = "尿",
  ["1B60"] = "球",
  ["1B61"] = "眼",
  ["1B62"] = "精",
  ["1B63"] = "靱",
  ["1B64"] = "帯",
  ["1B65"] = "副",
  ["1B66"] = "腎",
  ["1B67"] = "胞",
  ["1B68"] = "奥",
  ["1B69"] = "視",
  ["1B6A"] = "胃",
  ["1B6B"] = "脈",
  ["1B6C"] = "甲",
  ["1B6D"] = "鼓",
  ["1B6E"] = "膜",
  ["1B6F"] = "亜",
  ["1B70"] = "脂",
  ["1B71"] = "肪",
  ["1B72"] = "股",
  ["1B73"] = "格",
  ["1B74"] = "試",
  ["1B75"] = "尚",
  ["1B76"] = "業",
  ["1B77"] = "仕",
  ["1B78"] = "労",
  ["1B79"] = "浮",
  ["1B7A"] = "降",
  ["1B7B"] = "耐",
  ["1B7C"] = "種",
  ["1B7D"] = "類",
  ["1B7E"] = "遠",
  ["1B7F"] = "固",
  ["1B80"] = "密",
  ["1B81"] = "滴",
  ["1B82"] = "答",
  ["1B83"] = "移",
  ["1B84"] = "失",
  ["1B85"] = "堂",
  ["1B86"] = "殊",
  ["1B87"] = "頼",
  ["1B88"] = "成",
  ["1B89"] = "杉",
  ["1B8A"] = "織",
  ["1B8B"] = "陸",
  ["1B8C"] = "寿",
  ["1B8D"] = "圧",
  ["1B8E"] = "仏",
  ["1B8F"] = "像",
  ["1B90"] = "園",
  ["1B91"] = "絵",
  ["1B92"] = "辻",
  ["1B93"] = "邦",
  ["1B94"] = "氷",
  ["1B95"] = "圭",
  ["1B96"] = "祐",
  ["1B97"] = "哉",
  ["1B98"] = "脇",
  ["1B99"] = "賢",
  ["1B9A"] = "堀",
  ["1B9B"] = "渡",
  ["1B9C"] = "宣",
  ["1B9D"] = "崎",
  ["1B9E"] = "協",
  ["1B9F"] = "建",
  ["1BA0"] = "淵",
  ["1BA1"] = "幹",
  ["1BA2"] = "幹",
  ["1BA3"] = "克",
  ["1BA4"] = "昇",
}


-- small-kana correction guard
-- 2026-04-27 review: 91 F5 9B F8 = いっしょ, so F8 must be ょ.
MOMO3["F5"] = "っ"
MOMO3["F6"] = "ゃ"
MOMO3["F7"] = "ゅ"
MOMO3["F8"] = "ょ"

local DICT02 = {
  ["64"] = "人気",
  ["A0"] = "桃太郎",
  ["AC"] = "オニ",
  ["B0"] = "きんたん",
  ["B9"] = "ゆうき",
  ["C0"] = "おにぎり",
  ["CD"] = "ちから",
  ["CE"] = "あしゅら",
}

local function lookup_momo(key)
  return MOMO3[key] or "?"
end

local function lookup_dict02(low)
  return DICT02[h2(low)] or ("{02" .. h2(low) .. "}")
end

local function hirom_offset(bank, addr)
  local b = bank
  if b >= 0xC0 then b = b - 0xC0
  elseif b >= 0x80 then b = b - 0x80 end
  return b * 0x10000 + addr
end

local function rom8_hirom(bank, addr)
  if ROM_DOMAIN == nil then return nil end
  local off = hirom_offset(bank, addr)
  return safe_read_u8(off, ROM_DOMAIN)
end

local function rom8_offset(off)
  return safe_read_u8(off, ROM_DOMAIN)
end

local function src_ptr_b1()
  local lo = wram8(0x00B1)
  local hi = wram8(0x00B2)
  local bank = wram8(0x00B3)
  return bank, lo + hi * 0x100
end

local function ptr7e()
  local lo = wram8(0x007E)
  local hi = wram8(0x007F)
  local bank = wram8(0x0080)
  return bank, lo + hi * 0x100
end

local function valid_rom_ptr(bank, addr)
  if bank == nil or addr == nil then return false end
  if bank < 0xC0 or bank > 0xDF then return false end
  if addr < 0x8000 or addr > 0xFFFF then return false end
  return true
end

local function ptr_text(bank, addr)
  return h2(bank) .. ":" .. h4(addr)
end

-- The v28 logs showed source_state like:
--   $1274=DD00 $1276=A700 $1278=C800
-- Meaning the useful byte is often the HIGH byte of each 16-bit word:
--   DD / A7 / C8 => C8:A7DD
local function source_triplet_high(a)
  local lo = wram8(a + 1)
  local hi = wram8(a + 3)
  local bank = wram8(a + 5)
  return bank, lo + hi * 0x100
end

local function source_triplet_low(a)
  local lo = wram8(a)
  local hi = wram8(a + 2)
  local bank = wram8(a + 4)
  return bank, lo + hi * 0x100
end

local function add_candidate(cands, seen, name, bank, addr)
  if not valid_rom_ptr(bank, addr) then return end
  local k = ptr_text(bank, addr)
  if seen[k] then return end
  seen[k] = true
  cands[#cands+1] = {name=name, bank=bank, addr=addr}
end

local function collect_mode02_candidates()
  local cands = {}
  local seen = {}

  local b1_bank, b1_addr = src_ptr_b1()
  add_candidate(cands, seen, "B1", b1_bank, b1_addr)

  local e_bank, e_addr = ptr7e()
  add_candidate(cands, seen, "PTR7E", e_bank, e_addr)

  -- Scan compact source-state area for pointer triplets.
  -- Both high-byte and low-byte layouts are tried.
  for a = 0x1264, 0x1282, 2 do
    local hb, ha = source_triplet_high(a)
    add_candidate(cands, seen, "SRC" .. h4(a) .. "H", hb, ha)

    local lb, la = source_triplet_low(a)
    add_candidate(cands, seen, "SRC" .. h4(a) .. "L", lb, la)
  end

  return cands
end

local function hex_bytes(t)
  local out = {}
  for _, b in ipairs(t or {}) do out[#out+1] = h2(b) end
  return table.concat(out, " ")
end

-- ===== C0:BD98 tables =====
local function table_byte(snes_addr)
  -- tables are in bank C0.
  return rom8_hirom(0xC0, snes_addr) or 0
end

local TERM_ADDR = 0xBDE4
local T0_ADDR   = 0xBDEC
local M0_ADDR   = 0xBEEB
local T1_ADDR   = 0xBF0B
local M1_ADDR   = 0xC00A

local function bd98_next_symbol(st)
  -- faithful simulation of C0:BD98.
  -- st.ptr_bank / st.ptr_addr / st.bitbuf / st.bitcnt are local simulation state.
  local node = 0

  while true do
    local old = node
    local low = old % 8
    local hi = math.floor(old / 8)

    st.bitcnt = (st.bitcnt - 1) % 0x100
    if st.bitcnt >= 0x80 then
      local b = rom8_hirom(st.ptr_bank, st.ptr_addr)
      if b == nil then return nil, "source_oob" end
      st.bitbuf = b
      st.bitcnt = 7
      st.ptr_addr = (st.ptr_addr + 1) % 0x10000
      if st.ptr_addr == 0 then st.ptr_bank = (st.ptr_bank + 1) % 0x100 end
    end

    local carry = 0
    if (st.bitbuf & 0x80) ~= 0 then carry = 1 end
    st.bitbuf = (st.bitbuf * 2) % 0x100

    local mask
    if carry == 0 then
      node = table_byte(T0_ADDR + old)
      mask = table_byte(M0_ADDR + hi)
    else
      node = table_byte(T1_ADDR + old)
      mask = table_byte(M1_ADDR + hi)
    end

    local term = table_byte(TERM_ADDR + low)
    if (mask & term) == 0 then
      return node, nil
    end
  end
end

local function decode_mode02_symbols_from(bank, addr, max_symbols)
  local st = {
    ptr_bank = bank,
    ptr_addr = addr,
    bitbuf = 0,
    bitcnt = 0
  }
  local symbols = {}
  local err = nil
  for i=1,max_symbols do
    local sym, e = bd98_next_symbol(st)
    if sym == nil then err = e or "decode_error"; break end
    symbols[#symbols+1] = sym
    if sym == 0x00 then break end
  end
  return symbols, err, st
end

local function render_symbols(symbols)
  local out = {}
  local events = {}
  local i = 1
  while i <= #symbols do
    local b = symbols[i]
    if b == 0x00 then
      out[#out+1] = "<00>"
      events[#events+1] = string.format("%d:00:<00>", i)
      i = i + 1
    elseif b == 0x01 then
      out[#out+1] = "\n"
      events[#events+1] = string.format("%d:01:<NL>", i)
      i = i + 1
    elseif b == 0x02 and i < #symbols then
      local low = symbols[i+1]
      local s = lookup_dict02(low)
      out[#out+1] = s
      events[#events+1] = string.format("%d:02%02X:%s", i, low, s)
      i = i + 2
    elseif b >= 0x18 and b < 0x20 and i < #symbols then
      local low = symbols[i+1]
      local key = h2(b) .. h2(low)
      local s = lookup_momo(key)
      if s == "?" then s = "{K" .. key .. "}" end
      out[#out+1] = s
      events[#events+1] = string.format("%d:%s:%s", i, key, s)
      i = i + 2
    else
      local key = h2(b)
      local s = lookup_momo(key)
      if s == "?" then s = "{" .. key .. "}" end
      out[#out+1] = s
      events[#events+1] = string.format("%d:%s:%s", i, key, s)
      i = i + 1
    end
  end
  return table.concat(out, ""), table.concat(events, " | ")
end

local function score_symbols(symbols, decoded, err)
  if symbols == nil or #symbols == 0 then return -999 end
  local score = 0
  local good = 0
  local bad = 0
  local has_end = false
  local has_quote = false
  local has_nl = false

  local i = 1
  while i <= #symbols do
    local b = symbols[i]
    if b == 0x00 then
      has_end = true
      score = score + 14
      i = i + 1
    elseif b == 0x01 then
      has_nl = true
      good = good + 1
      i = i + 1
    elseif b == 0x02 and i < #symbols then
      good = good + 3
      i = i + 2
    elseif b >= 0x18 and b < 0x20 and i < #symbols then
      good = good + 3
      i = i + 2
    elseif (b >= 0x90 and b <= 0xBE) or (b >= 0xD0 and b <= 0xF8) or b == 0x50 or b == 0x5C or b == 0x5D or b == 0x5E or b == 0x5F or b == 0x7D or b == 0x7E then
      good = good + 1
      if b == 0x7D or b == 0x7E then has_quote = true end
      i = i + 1
    elseif b >= 0x61 and b <= 0x7A then
      bad = bad + 2
      i = i + 1
    elseif b >= 0x80 and b <= 0xFF then
      -- Unknown high byte is less bad than ASCII garbage; many tables remain incomplete.
      bad = bad + 1
      i = i + 1
    else
      bad = bad + 1
      i = i + 1
    end
  end

  score = score + good - bad
  if has_quote then score = score + 5 end
  if has_nl then score = score + 3 end
  if err ~= nil then score = score - 20 end
  if decoded and string.find(decoded, "{", 1, true) then score = score - 2 end
  return score
end

local function decode_candidate(c)
  local syms, err, st = decode_mode02_symbols_from(c.bank, c.addr, READ_SYMBOLS)
  local dec, ev = render_symbols(syms or {})
  local score = score_symbols(syms, dec, err)
  return {
    name = c.name,
    bank = c.bank,
    addr = c.addr,
    symbols = syms,
    err = err,
    st = st,
    decoded = dec,
    events = ev,
    score = score
  }
end

local function copy_decode_state(st)
  return {
    ptr_bank = st.ptr_bank,
    ptr_addr = st.ptr_addr,
    bitbuf = st.bitbuf,
    bitcnt = st.bitcnt
  }
end

local function state_ptr_text(st)
  if st == nil then return "??:????/bc??/buf??" end
  return ptr_text(st.ptr_bank, st.ptr_addr) .. "/bc" .. h2(st.bitcnt) .. "/buf" .. h2(st.bitbuf)
end

local function decode_one_stream_from_state(st, max_symbols)
  local symbols = {}
  local err = nil
  for i=1,max_symbols do
    local sym, e = bd98_next_symbol(st)
    if sym == nil then err = e or "decode_error"; break end
    symbols[#symbols+1] = sym
    if sym == 0x00 then break end
  end
  return symbols, err, st
end

local function decode_chain_candidate(c, nstreams)
  local st = {
    ptr_bank = c.bank,
    ptr_addr = c.addr,
    bitbuf = 0,
    bitcnt = 0
  }
  local out = {}
  for idx=0,(nstreams or CHAIN_STREAMS)-1 do
    local begin = copy_decode_state(st)
    local syms, err = decode_one_stream_from_state(st, READ_SYMBOLS)
    local dec, ev = render_symbols(syms or {})
    local score = score_symbols(syms, dec, err)
    out[#out+1] = {
      idx = idx,
      name = c.name,
      bank = c.bank,
      addr = c.addr,
      begin_state = begin,
      end_state = copy_decode_state(st),
      symbols = syms,
      err = err,
      decoded = dec,
      events = ev,
      score = score
    }
    if syms == nil or #syms == 0 or err ~= nil then break end
  end
  return out
end

local function compact_chain_list(chain)
  local out = {}
  for _, d in ipairs(chain or {}) do
    out[#out+1] =
      "seg" .. tostring(d.idx) ..
      "/s" .. tostring(d.score) ..
      "/begin" .. state_ptr_text(d.begin_state) ..
      "/end" .. state_ptr_text(d.end_state) ..
      "/" .. trunc(string.gsub(d.decoded or "", "\n", "\\n"), 220)
  end
  return table.concat(out, " || ")
end

local function find_best_mode02_candidate()
  local cands = collect_mode02_candidates()
  local decoded = {}
  local best = nil
  for _, c in ipairs(cands) do
    local d = decode_candidate(c)
    decoded[#decoded+1] = d
    if best == nil or d.score > best.score then best = d end
  end
  table.sort(decoded, function(a,b) return a.score > b.score end)
  return best, decoded
end

local function compact_candidate_list(decoded)
  local out = {}
  for i, d in ipairs(decoded or {}) do
    if i > 8 then break end
    out[#out+1] = d.name .. "=" .. ptr_text(d.bank, d.addr) .. "/s" .. tostring(d.score) .. "/end" .. ptr_text(d.st and d.st.ptr_bank or 0, d.st and d.st.ptr_addr or 0) .. "/bc" .. h2(d.st and d.st.bitcnt or 0)
  end
  return table.concat(out, " | ")
end

local function state()
  return table.concat({
    "12AA=" .. h2(wram8(0x12AA)),
    "12A9=" .. h2(wram8(0x12A9)),
    "12AD=" .. h2(wram8(0x12AD)),
    "12B2=" .. h2(wram8(0x12B2)),
    "12B3=" .. h2(wram8(0x12B3)),
    "12B4=" .. h2(wram8(0x12B4)),
    "12B5=" .. h2(wram8(0x12B5)),
    "12B6=" .. h2(wram8(0x12B6)),
    "12BC=" .. h2(wram8(0x12BC)),
    "12C4=" .. h2(wram8(0x12C4)),
    "12C5=" .. h2(wram8(0x12C5))
  }, ",")
end

local function source_state_words()
  local out = {}
  for a = 0x1264, 0x1286, 2 do
    local lo = wram8(a)
    local hi = wram8(a+1)
    if lo ~= 0 or hi ~= 0 then out[#out+1] = "$" .. h4(a) .. "=" .. h2(hi) .. h2(lo) end
  end
  return table.concat(out, " ")
end

local function active_text()
  return wram8(0x12B4) == 0x50 or wram8(0x12AD) == 0x00 or wram8(0x12B2) ~= 0x00
end

-- simple observed display token too. This is not reconstruction.
local function decode_display_observed()
  local b2 = wram8(0x12B2)
  local b3 = wram8(0x12B3)
  local c4 = wram8(0x12C4)
  local c5 = wram8(0x12C5)

  if c5 == 0x02 then return lookup_dict02(c4), "c4c5_dict02_rev" end
  if b2 >= 0x18 and b2 < 0x20 then
    local key = h2(b2) .. h2(b3)
    local s = lookup_momo(key)
    if s == "?" then s = "{K" .. key .. "}" end
    return s, "b2b3_kanji"
  end
  if c4 >= 0x18 and c4 < 0x20 then
    local key = h2(c4) .. h2(c5)
    local s = lookup_momo(key)
    if s == "?" then s = "{K" .. key .. "}" end
    return s, "c4c5_kanji"
  end
  local a = lookup_momo(h2(c4)); if a == "?" then a = "" end
  local b = lookup_momo(h2(b2)); if b == "?" then b = "" end
  if a ~= "" and b ~= "" and c4 == b2 then return a, "dedup_same_c4_b2" end
  return a .. b, "single_mix"
end

logLine("shinmomo dialogue v31 standalone loaded. BD98 mode02 chained decoder + source-state pointer scan. small kana: F5=っ F6=ゃ F7=ゅ F8=ょ")
logLine("domains=" .. table.concat(DOMAINS, "|") .. ", WRAM=" .. tostring(WRAM_DOMAIN) .. ", ROM=" .. tostring(ROM_DOMAIN))
logLine("No context word insertion. Implements C0:BD98 bitstream decoder.")
logLine("TRACE_DIALOGUE_V31_READY,frame=" .. emu.framecount() .. "," .. state())

local last_mode02_key = ""
local last_mode02_frame = -9999

local decoded_buf = ""
local token_events = {}
local last_token_key = ""
local last_token_frame = -9999
local last_display_frame = emu.framecount()

while true do
  emu.frameadvance()
  local f = emu.framecount()

  if TRACE_ALIVE_FRAMES > 0 and (f % TRACE_ALIVE_FRAMES) == 0 then
    logLine("TRACE_DIALOGUE_V31_ALIVE,frame=" .. f .. "," .. state() .. ",source_state=" .. source_state_words())
  end

  if active_text() then
    local mode = wram8(0x12AA)

    if mode == 0x02 and TRACE_MODE02_BEST then
      local best, decoded = find_best_mode02_candidate()

      if best ~= nil and best.score >= MIN_GOOD_SCORE then
        local best_key = best.name .. ":" .. ptr_text(best.bank, best.addr) .. ":" .. best.decoded
        if best_key ~= last_mode02_key and (f - last_mode02_frame) > MODE02_DECODE_MIN_GAP then
          logLine(table.concat({
            "TRACE_DIALOGUE_V31_MODE02_BEST",
            "frame=" .. f,
            "source=" .. best.name,
            "ptr=" .. ptr_text(best.bank, best.addr),
            "score=" .. tostring(best.score),
            "decoded=" .. trunc(best.decoded, 1400),
            "end=" .. ptr_text(best.st.ptr_bank, best.st.ptr_addr) .. "/bitcnt" .. h2(best.st.bitcnt) .. "/err" .. tostring(best.err),
            "source_state=" .. source_state_words(),
            state()
          }, ","))

          if TRACE_MODE02_CANDIDATES then
            logLine(table.concat({
              "TRACE_DIALOGUE_V31_MODE02_CANDIDATES",
              "frame=" .. f,
              "best=" .. best.name .. "@" .. ptr_text(best.bank, best.addr),
              "candidates=" .. compact_candidate_list(decoded)
            }, ","))
          end

          if TRACE_MODE02_CHAIN then
            local chain = decode_chain_candidate({name=best.name, bank=best.bank, addr=best.addr}, CHAIN_STREAMS)
            logLine(table.concat({
              "TRACE_DIALOGUE_V31_MODE02_CHAIN",
              "frame=" .. f,
              "source=" .. best.name,
              "base=" .. ptr_text(best.bank, best.addr),
              "chain=" .. compact_chain_list(chain)
            }, ","))
          end

          if TRACE_VERBOSE_EVENTS then
            logLine(table.concat({
              "TRACE_DIALOGUE_V31_MODE02_EVENTS",
              "frame=" .. f,
              "source=" .. best.name,
              "ptr=" .. ptr_text(best.bank, best.addr),
              "events=" .. trunc(best.events, 2500)
            }, ","))
          end

          last_mode02_key = best_key
          last_mode02_frame = f
        end
      end
    end

    if TRACE_SCREEN_OBSERVED or TRACE_TOKENS then
      local tok, via = decode_display_observed()
      local raw_key = table.concat({
        h2(wram8(0x12B2)), h2(wram8(0x12B3)),
        h2(wram8(0x12C4)), h2(wram8(0x12C5)),
        h2(wram8(0x12AD)), h2(wram8(0x12BC)),
        tostring(tok)
      }, ":")

      if tok ~= "" and (raw_key ~= last_token_key or (f - last_token_frame) > TOKEN_REPEAT_SUPPRESS_FRAMES) then
        if TRACE_SCREEN_OBSERVED then
          decoded_buf = decoded_buf .. tok
          token_events[#token_events+1] = string.format(
            "f%d:%s:b2%02X%02X:c4%02X%02X:via=%s:m%02X",
            f, tok,
            wram8(0x12B2), wram8(0x12B3), wram8(0x12C4), wram8(0x12C5),
            via, wram8(0x12AA)
          )
          if #token_events > 80 then table.remove(token_events, 1) end
        end

        if TRACE_TOKENS then
          logLine(table.concat({
            "TRACE_DIALOGUE_V31_TOKEN",
            "frame=" .. f,
            "token=" .. tok,
            "via=" .. via,
            "mode=" .. h2(wram8(0x12AA)),
            state()
          }, ","))
        end

        last_token_key = raw_key
        last_token_frame = f
        last_display_frame = f
      end

      if TRACE_SCREEN_OBSERVED and decoded_buf ~= "" and (f - last_display_frame) > DISPLAY_IDLE_FLUSH_FRAMES then
        logLine(table.concat({
          "TRACE_DIALOGUE_V31_SCREEN_LINE",
          "frame=" .. f,
          "decoded_observed=" .. decoded_buf,
          "token_events=" .. table.concat(token_events, " | "),
          "source_state=" .. source_state_words(),
          state()
        }, ","))
        decoded_buf = ""
        token_events = {}
        last_token_key = ""
      end
    end
  end
end
