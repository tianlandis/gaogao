#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加2024年数据：
1. 解析2024年一分一段表(专业/文化/综合) → 更新 compressed_ranks.json
2. 解析2024年投档表 → 匹配并丰富 data.json (添加 line2024, plan2024 字段)
"""
import sys, io, os, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd

BASE = "downloads"

# ============================================================
# STEP 1: 解析2024年一分一段表
# ============================================================

# 2024年文化成绩一分一段表 (实际为xls/OLE2格式，已改名)
CULTURE_2024 = {
    "vocal_culture_2024": os.path.join(BASE, "2024年文化成绩一分一段表", "2024年本科艺术统考音乐类（音乐表演-声乐）双达线考生文化成绩一分一段表.xls"),
    "instrumental_culture_2024": os.path.join(BASE, "2024年文化成绩一分一段表", "2024年本科艺术统考音乐类（音乐表演-器乐）双达线考生文化成绩一分一段表.xls"),
    "education_culture_2024": os.path.join(BASE, "2024年文化成绩一分一段表", "2024年本科艺术统考音乐类（音乐教育）双达线考生文化成绩一分一段表.xls"),
}

# 2024年专业成绩一分一段表 (xls格式)
PROFESSIONAL_2024 = {
    "vocal_art_2024": os.path.join(BASE, "2024年专业成绩一分一段表", "山东省2024年普通高等学校招生音乐类（音乐表演-声乐）专业统一考试成绩一分一段表.xls"),
    "instrumental_art_2024": os.path.join(BASE, "2024年专业成绩一分一段表", "山东省2024年普通高等学校招生音乐类（音乐表演-器乐）专业统一考试成绩一分一段表.xls"),
    "education_art_2024": os.path.join(BASE, "2024年专业成绩一分一段表", "山东省2024年普通高等学校招生音乐类（音乐教育）专业统一考试成绩一分一段表.xls"),
}

# 2024年综合成绩分段表 (实际为xls/OLE2格式，已改名)
COMPREHENSIVE_2024 = {
    "vocal_2024": os.path.join(BASE, "2024年综合一分一段表", "2024年本科艺术统考音乐类（音乐表演-声乐）综合成绩分段表.xls"),
    "instrumental_2024": os.path.join(BASE, "2024年综合一分一段表", "2024年本科艺术统考音乐类（音乐表演-器乐）综合成绩分段表.xls"),
    "education_2024": os.path.join(BASE, "2024年综合一分一段表", "2024年本科艺术统考音乐类（音乐教育）综合成绩分段表.xls"),
}


def parse_rank_xls(filepath, label):
    """解析一分一段 XLS (xlrd引擎)"""
    if not os.path.exists(filepath):
        print(f"  ❌ 文件不存在: {filepath}")
        return {}
    
    try:
        df = pd.read_excel(filepath, engine='xlrd', header=None)
    except Exception as e:
        print(f"  ⚠️ xlrd失败尝试openpyxl: {label} - {e}")
        try:
            df = pd.read_excel(filepath, engine='openpyxl', header=None)
        except Exception as e2:
            print(f"  ❌ 无法读取: {filepath} - {e2}")
            return {}
    
    result = {}
    header_found = False
    
    for _, row in df.iterrows():
        if pd.isna(row.iloc[0]) if hasattr(row, 'iloc') else pd.isna(row[0]):
            continue
        
        text = str(row.iloc[0]) if hasattr(row, 'iloc') else str(row[0])
        if any(kw in text for kw in ['分数段', '成绩', '本段人数', '累计人数', '合计', '分数']):
            header_found = True
            continue
        if not header_found:
            continue
        
        # 提取分数
        score_raw = str(row.iloc[0]) if hasattr(row, 'iloc') else str(row[0])
        score_raw = score_raw.strip()
        score_match = re.search(r'(\d+\.?\d*)', score_raw)
        if not score_match:
            continue
        score = score_match.group(1)
        if '.' in score and score.split('.')[1] == '0':
            score = score.split('.')[0]
        
        # 提取累计人数 (第2列或第3列)
        ncols = len(row) if hasattr(row, '__len__') else df.shape[1]
        cum_val = None
        for col_idx in [2, 1]:
            if col_idx < ncols:
                val = row.iloc[col_idx] if hasattr(row, 'iloc') else row[col_idx]
                if not pd.isna(val):
                    cum_match = re.search(r'(\d+)', str(val))
                    if cum_match:
                        cum_val = int(cum_match.group(1))
                        break
        if cum_val is not None:
            result[score] = cum_val
    
    print(f"  ✅ {label}: {len(result)} 个分数点")
    return result


def parse_rank_xlsx(filepath, label):
    """解析一分一段 XLSX (先尝试xlrd, 很多.xlsx实际是.xls格式)"""
    if not os.path.exists(filepath):
        print(f"  ❌ 文件不存在: {filepath}")
        return {}
    
    df = None
    # 先尝试 xlrd (很多.xlsx后缀的文件实际是OLE2/.xls格式)
    try:
        df = pd.read_excel(filepath, engine='xlrd', header=None)
    except:
        pass
    
    if df is None:
        try:
            df = pd.read_excel(filepath, engine='openpyxl', header=None)
        except Exception as e:
            print(f"  ❌ 无法读取 {label}: {e}")
            return {}
    
    result = {}
    header_found = False
    
    for _, row in df.iterrows():
        if pd.isna(row.iloc[0]):
            continue
        
        text = str(row.iloc[0])
        if any(kw in text for kw in ['分数段', '成绩', '本段人数', '累计人数', '合计', '分数']):
            header_found = True
            continue
        if not header_found:
            continue
        
        score_raw = str(row.iloc[0]).strip()
        score_match = re.search(r'(\d+\.?\d*)', score_raw)
        if not score_match:
            continue
        score = score_match.group(1)
        if '.' in score and score.split('.')[1] == '0':
            score = score.split('.')[0]
        
        ncols = df.shape[1]
        cum_val = None
        for col_idx in [2, 1]:
            if col_idx < ncols:
                val = row.iloc[col_idx]
                if not pd.isna(val):
                    cum_match = re.search(r'(\d+)', str(val))
                    if cum_match:
                        cum_val = int(cum_match.group(1))
                        break
        if cum_val is not None:
            result[score] = cum_val
    
    print(f"  ✅ {label}: {len(result)} 个分数点")
    return result


def build_2024_ranks():
    """解析2024年所有一分一段表，更新compressed_ranks.json"""
    print("=" * 60)
    print("  📊 Step 1: 解析2024年一分一段表 → compressed_ranks.json")
    print("=" * 60)
    
    # 读取现有的 compressed_ranks.json
    existing = {}
    if os.path.exists("compressed_ranks.json"):
        with open("compressed_ranks.json", "r", encoding="utf-8") as f:
            existing = json.load(f)
        print(f"  现有数据集: {len(existing)} 个")
    
    # 文化成绩 (xlsx)
    print("\n📚 2024年文化成绩一分一段表:")
    for key, path in CULTURE_2024.items():
        data = parse_rank_xlsx(path, key)
        if data:
            existing[key] = dict(sorted(data.items(), key=lambda x: int(x[0]), reverse=True))
    
    # 专业成绩 (xls)
    print("\n🎵 2024年专业成绩一分一段表:")
    for key, path in PROFESSIONAL_2024.items():
        data = parse_rank_xls(path, key)
        if data:
            existing[key] = dict(sorted(data.items(), key=lambda x: float(x[0]), reverse=True))
    
    # 综合成绩 (xlsx)
    print("\n🏆 2024年综合成绩分段表:")
    for key, path in COMPREHENSIVE_2024.items():
        data = parse_rank_xlsx(path, key)
        if data:
            existing[key] = dict(sorted(data.items(), key=lambda x: float(x[0]), reverse=True))
    
    # 保存
    with open("compressed_ranks.json", "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    size = os.path.getsize("compressed_ranks.json") / 1024
    print(f"\n✅ compressed_ranks.json 已更新 ({size:.1f} KB)")
    print(f"   总数据集: {len(existing)} 个")
    for k, v in sorted(existing.items()):
        scores = list(v.keys())
        if scores:
            print(f"     {k}: {len(v)}点, 最高={scores[0]}, 最低={scores[-1]}")
    
    return existing


# ============================================================
# STEP 2: 解析2024年投档表，匹配到 data.json
# ============================================================

# 和2025年相同的UNI_DB和推断逻辑
UNI_DB = {
    "A027":("北京","公办"),"A028":("北京","公办"),"A031":("北京","公办"),
    "A033":("北京","公办"),"A045":("北京","公办"),
    "A047":("北京","公办"),"A048":("北京","公办"),
    "A064":("上海","公办"),"A065":("上海","公办"),
    "A110":("山西","公办"),
    "A220":("黑龙江","公办"),
    "A514":("湖北","公办"),
    "A635":("重庆","公办"),"A647":("重庆","公办"),
    "A656":("四川","公办"),
    "A694":("西藏","公办"),
    "A742":("甘肃","公办"),
    "B407":("宁夏","公办"),"B959":("黑龙江","公办"),
    "D678":("陕西","民办"),
    "E437":("山东","公办"),"E438":("山东","公办"),"E439":("山东","公办"),
    "E440":("山东","公办"),"E442":("山东","公办"),"E447":("山东","公办"),
    "E448":("山东","公办"),"E452":("山东","公办"),"E453":("山东","公办"),
    "E454":("山东","公办"),"E456":("山东","公办"),"E457":("山东","公办"),
    "E458":("山东","公办"),"E459":("山东","公办"),"E460":("山东","公办"),
    "E462":("山东","公办"),"E463":("山东","公办"),"E464":("山东","公办"),
    "E465":("山东","公办"),
}

PROVINCE_KW = {
    "山东":["山东","齐鲁","济南","青岛","烟台","潍坊","临沂","聊城","曲阜",
            "菏泽","枣庄","德州","滨州","济宁","日照","威海","东营","淄博",
            "泰山","鲁东","临大"],
    "北京":["北京","首都","中央","中国","北师"],
    "上海":["上海","华东","同济"],
    "天津":["天津"],
    "江苏":["江苏","南京","苏州","无锡","常州","徐州","南通","淮阴","连云港",
             "扬州","盐城","镇江","宿迁","江南","淮安"],
    "浙江":["浙江","杭州","宁波","温州","湖州","台州","绍兴"],
    "广东":["广东","广州","深圳","珠海","东莞","暨南","中山","华南","星海"],
    "四川":["四川","成都","绵阳","内江","西华","南充","攀枝花"],
    "湖北":["湖北","武汉","黄石","荆州","三峡","江汉","长江大学",
             "武昌","汉口","华中","黄冈"],
    "湖南":["湖南","长沙","张家界","邵阳","怀化","湘南","吉首","衡阳"],
    "河南":["河南","郑州","安阳","平顶山","南阳","商丘","周口","洛阳","开封"],
    "河北":["河北","石家庄","保定","邯郸","唐山","衡水","廊坊","沧州","邢台"],
    "辽宁":["辽宁","沈阳","大连","鞍山","渤海","锦州","朝阳"],
    "吉林":["吉林","长春","延边","北华","白城","通化"],
    "黑龙江":["黑龙江","哈尔滨","齐齐哈尔","伊春","牡丹江","大庆","佳木斯",
               "黑河","鸡西","绥化","鹤岗"],
    "陕西":["陕西","西安","延安","宝鸡","渭南","商洛","咸阳"],
    "福建":["福建","福州","厦门","华侨","集美","泉州"],
    "江西":["江西","南昌","九江","上饶","宜春","景德镇","赣南","吉安"],
    "安徽":["安徽","合肥","淮北","滁州","芜湖","黄山","安庆"],
    "广西":["广西","桂林","南宁","贺州"],
    "海南":["海南","海口","琼台","三亚"],
    "新疆":["新疆","乌鲁木齐","巴音郭楞","和田","喀什","伊犁","石河子"],
    "云南":["云南","昆明","楚雄","玉溪","红河","大理","滇池"],
    "贵州":["贵州","贵阳","遵义","凯里","兴义","六盘水"],
    "重庆":["重庆","长江师范"],
    "甘肃":["甘肃","兰州","天水"],
    "青海":["青海","西宁"],
    "宁夏":["宁夏","银川"],
    "内蒙古":["内蒙古","呼和浩特","包头","赤峰","呼伦贝尔"],
    "山西":["山西","太原","吕梁","忻州","长治","大同"],
    "西藏":["西藏","拉萨"],
}

DIR_KW = {
    "vocal":["声乐","流行演唱","演唱","音乐剧","美声","民族唱法"],
    "instrumental":["器乐","钢琴","管弦","中国乐器","键盘","电吉他",
                    "弦乐","管乐","打击乐","民乐","西洋乐","流行"],
    "education":["音乐教育","师范","作曲","录音艺术","音乐学","音乐治疗",
                 "艺术管理","音乐表演"],
}

def guess_direction(major):
    for d,kws in DIR_KW.items():
        for kw in kws:
            if kw in major: return d
    return "education"

def guess_meta(code, name):
    if code in UNI_DB:
        return UNI_DB[code]
    for p, kws in PROVINCE_KW.items():
        for kw in kws:
            if kw in name:
                nat = "民办" if any(x in name for x in ["民办","独立学院","城市学院","职业技术","职业学院"]) else "公办"
                return (p, nat)
    return ("", "公办")


def parse_admission_2024(filepath, batch_label, is_vocational=False):
    """解析2024年投档表 XLS"""
    if not os.path.exists(filepath):
        print(f"  ⚠️  文件不存在: {filepath}")
        return []
    
    try:
        df = pd.read_excel(filepath, engine='xlrd', header=None)
    except:
        try:
            df = pd.read_excel(filepath, engine='openpyxl', header=None)
        except Exception as e:
            print(f"  ❌ 无法读取: {filepath} - {e}")
            return []
    
    rows_list = []
    header_found = False
    ncols = df.shape[1]
    
    for _, row in df.iterrows():
        if pd.isna(row.iloc[2]) or pd.isna(row.iloc[1]):
            continue
        
        row_text = ''.join(str(c) for c in row if not pd.isna(c))
        if any(kw in row_text for kw in ['院校代号及名称', '专业代号及名称', '投档计划', '投档最低', '录取最低']):
            header_found = True
            continue
        if not header_found:
            continue
        
        # 专业代码和名称
        major_full = str(row.iloc[1]).strip()
        major_match = re.match(r'^([0-9A-Za-z]+)\s*(.+)$', major_full)
        if not major_match:
            continue
        major_code = major_match.group(1)
        major_name = major_match.group(2).strip()
        
        # 院校代码和名称
        school_full = str(row.iloc[2]).strip()
        school_match = re.match(r'^([A-Z]\d+)\s*(.+)$', school_full)
        if not school_match:
            continue
        school_code = school_match.group(1)
        school_name = school_match.group(2).strip()
        
        # 计划数和最低分
        plan = 0
        plan_col = 3
        score_col = 3 if ncols <= 4 else 4
        
        if ncols >= 5 and not pd.isna(row.iloc[plan_col]):
            plan_match = re.search(r'(\d+)', str(row.iloc[plan_col]))
            if plan_match:
                plan = int(plan_match.group(1))
        
        line = 0.0
        if not pd.isna(row.iloc[score_col]):
            line_match = re.search(r'([\d.]+)', str(row.iloc[score_col]))
            if line_match:
                line = float(line_match.group(1))
        
        direction = guess_direction(major_name)
        province, nature = guess_meta(school_code, school_name)
        level = "专科" if is_vocational else "本科"
        
        rows_list.append({
            "code": school_code,
            "name": school_name,
            "major_code": major_code,
            "major": major_name,
            "direction": direction,
            "province": province,
            "level": level,
            "nature": nature,
            "batch": batch_label,
            "line": line,
            "plan": plan
        })
    
    return rows_list


def clean_major_name(name):
    """清洗专业名"""
    name = str(name).replace('*', '').strip()
    name = re.sub(r'[（(]\d+年[)）]', '', name)
    name = re.sub(r'[（(][^)）]*中外合作[^)）]*[)）]', '', name)
    return name.strip()

def major_keywords(name):
    """从专业名提取关键词组"""
    c = clean_major_name(name)
    kw = set()
    if any(w in c for w in ['声乐', '演唱']):
        kw.add('vocal')
    if any(w in c for w in ['器乐', '钢琴', '管弦', '二胡', '琵琶', '古筝', '大提琴', 
                              '小提琴', '长笛', '小号', '长号', '民族器乐', '西洋器乐',
                              '打击乐', '弦乐', '管乐', '民乐', '键盘', '手风琴', '萨克斯',
                              '竹笛', '唢呐', '笙', '扬琴', '中阮', '柳琴', '单簧管', '双簧管',
                              '圆号', '大管', '中提琴', '低音提琴', '电吉他', '吉他', '贝斯']):
        kw.add('instrumental')
    if any(w in c for w in ['师范', '音乐教育', '教育']):
        kw.add('education')
    if any(w in c for w in ['音乐学', '音乐治疗']):
        kw.add('musicology')
    if any(w in c for w in ['音乐表演']):
        kw.add('performance')
    if any(w in c for w in ['作曲', '录音', '艺术管理']):
        kw.add('other')
    return kw

def major_score(kw1, kw2):
    """两个专业名关键词组的匹配分"""
    if not kw1 or not kw2:
        return 0
    common = kw1 & kw2
    return len(common) / max(len(kw1), len(kw2))


def build_2024_admission():
    """解析2024年投档表，匹配到data.json的schools中（使用多策略模糊匹配）"""
    print("\n" + "=" * 60)
    print("  🏫 Step 2: 解析2024年投档表 → 匹配到 data.json")
    print("=" * 60)
    
    # 读取现有的 data.json
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    schools = data.get("schools", [])
    print(f"  现有2025年记录: {len(schools)} 条")
    
    # 解析2024年投档表
    admission_2024 = [
        (os.path.join(BASE, "2024toudang", "山东省2024年艺术类本科批音乐类第1次志愿投档情况表(公布).xls"), "本科批第1次投档"),
        (os.path.join(BASE, "2024toudang", "山东省2024年艺术类本科批音乐类第2次志愿投档情况表(公布).xls"), "本科批第2次投档"),
    ]
    
    records_2024 = []
    for path, batch in admission_2024:
        recs = parse_admission_2024(path, batch)
        records_2024.extend(recs)
        print(f"  {batch}: {len(recs)} 条记录")
    
    print(f"\n  2024年总记录: {len(records_2024)} 条")
    
    # 建两个索引
    idx_code = {}    # (code, major_code) → list
    idx_school = {}  # code → list
    for r in records_2024:
        key = (r["code"], r["major_code"])
        if key not in idx_code:
            idx_code[key] = []
        idx_code[key].append(r)
        if r["code"] not in idx_school:
            idx_school[r["code"]] = []
        idx_school[r["code"]].append(r)
    
    # 匹配: 对每条2025年school，查找对应2024年数据
    matched_exact = 0
    matched_fuzzy = 0
    not_matched = 0
    
    for school in schools:
        code = school["code"]
        mc = school["major_code"]
        school_kw = major_keywords(school.get("major", ""))
        school_dir = school_kw & {'vocal', 'instrumental', 'education'}
        
        matched = False
        
        # 策略1: 精确 code + major_code 匹配 (方向关键词一致)
        key = (code, mc)
        if key in idx_code:
            valid = []
            for c in idx_code[key]:
                c_kw = major_keywords(c["major"])
                c_dir = c_kw & {'vocal', 'instrumental', 'education'}
                if school_dir == c_dir or (not school_dir and not c_dir):
                    valid.append(c)
            if valid:
                best = min(valid, key=lambda x: x["line"])
                school["line2024"] = best["line"]
                school["plan2024"] = best["plan"]
                matched_exact += 1
                matched = True
        
        # 策略2: 同校模糊专业名匹配 (方向关键词必须一致)
        if not matched and code in idx_school:
            best_score = 0
            best_candidate = None
            for c in idx_school[code]:
                c_kw = major_keywords(c["major"])
                c_dir = c_kw & {'vocal', 'instrumental', 'education'}
                if school_dir and c_dir and school_dir != c_dir:
                    continue
                s = major_score(school_kw, c_kw)
                if s > best_score:
                    best_score = s
                    best_candidate = c
            if best_score >= 0.3 and best_candidate:
                school["line2024"] = best_candidate["line"]
                school["plan2024"] = best_candidate["plan"]
                matched_fuzzy += 1
                matched = True
        
        # 策略3: 同校专业名子串匹配
        if not matched and code in idx_school:
            m25 = clean_major_name(school.get("major", ""))
            for c in idx_school[code]:
                c_kw = major_keywords(c["major"])
                c_dir = c_kw & {'vocal', 'instrumental', 'education'}
                if school_dir and c_dir and school_dir != c_dir:
                    continue
                m24 = clean_major_name(c["major"])
                if m25 and m24 and (m25 in m24 or m24 in m25):
                    school["line2024"] = c["line"]
                    school["plan2024"] = c["plan"]
                    matched_fuzzy += 1
                    matched = True
                    break
        
        if not matched:
            school["line2024"] = None
            school["plan2024"] = None
            not_matched += 1
    
    print(f"\n  匹配结果: 精确 {matched_exact} 条, 模糊 {matched_fuzzy} 条, 未匹配 {not_matched} 条")
    
    # 更新metadata
    data["metadata"]["version"] = "4.0"
    data["metadata"]["update_time"] = "2026-06-25"
    data["metadata"]["description"] = "2024-2025年山东省艺术类本科/专科批音乐类投档录取数据（含两年对比）"
    data["metadata"]["years"] = [2024, 2025]
    
    # 保存
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    size = os.path.getsize("data.json") / 1024
    print(f"\n✅ data.json 已更新 ({size:.1f} KB)")
    
    # 展示一些匹配样例
    samples_with_2024 = [s for s in schools if s.get("line2024") is not None][:5]
    print("\n  匹配样例:")
    for s in samples_with_2024:
        trend = "📈" if s["line"] > s["line2024"] else ("📉" if s["line"] < s["line2024"] else "➡️")
        diff = s["line"] - s["line2024"]
        print(f"    {s['code']} {s['name'][:12]:12s} | {s['major_code']} {s['major'][:20]:20s} | 2024={s['line2024']:.2f} → 2025={s['line']:.2f} {trend} {diff:+.2f}")
    
    return data


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  2024年数据集成管道")
    print("=" * 60)
    
    # Step 1: 一分一段表
    build_2024_ranks()
    
    # Step 2: 投档表
    build_2024_admission()
    
    print("\n" + "=" * 60)
    print("  🎉 2024年数据集成完成！")
    print("=" * 60)
