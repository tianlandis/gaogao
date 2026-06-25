#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复2024年投档表匹配 — 专业代码跨年变化，改用名称关键字匹配
"""
import sys, io, os, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd

BASE = "downloads"

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

def parse_admission_2024(filepath, batch_label):
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
        
        major_full = str(row.iloc[1]).strip()
        major_match = re.match(r'^([0-9A-Za-z]+)\s*(.+)$', major_full)
        if not major_match:
            continue
        major_code = major_match.group(1)
        major_name = major_match.group(2).strip()
        
        school_full = str(row.iloc[2]).strip()
        school_match = re.match(r'^([A-Z]\d+)\s*(.+)$', school_full)
        if not school_match:
            continue
        school_code = school_match.group(1)
        school_name = school_match.group(2).strip()
        
        # 列3=计划数, 列4=最低分，检查哪个是数字
        plan = 0
        line = 0.0
        plan_col = 3
        score_col = 4 if ncols >= 5 else 3
        
        if not pd.isna(row.iloc[plan_col]):
            plan_match = re.search(r'(\d+)', str(row.iloc[plan_col]))
            if plan_match:
                plan = int(plan_match.group(1))
        
        if not pd.isna(row.iloc[score_col]):
            line_match = re.search(r'([\d.]+)', str(row.iloc[score_col]))
            if line_match:
                line = float(line_match.group(1))
        
        rows_list.append({
            "code": school_code,
            "name": school_name,
            "major_code": major_code,
            "major": major_name,
            "batch": batch_label,
            "line": line,
            "plan": plan
        })
    
    return rows_list


def clean_major_name(name):
    """清洗专业名，提取核心关键词用于模糊匹配"""
    name = str(name).replace('*', '').strip()
    name = re.sub(r'[（(]\d+年[)）]', '', name)  # 去掉(1年)
    name = re.sub(r'[（(][^)）]*中外合作[^)）]*[)）]', '', name)
    return name.strip()


def major_keywords(name):
    """从专业名提取关键词组"""
    c = clean_major_name(name)
    # 提取分类关键词
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
    """两个专业名关键词组的匹配分：交集越大越好"""
    if not kw1 or not kw2:
        return 0
    common = kw1 & kw2
    return len(common) / max(len(kw1), len(kw2))


# === MAIN ===
print("=" * 60)
print("  修复2024年投档匹配 — 关键字模糊匹配")
print("=" * 60)

# 解析2024年投档表
admission_2024 = [
    (os.path.join(BASE, "2024toudang", "山东省2024年艺术类本科批音乐类第1次志愿投档情况表(公布).xls"), "本科批第1次投档"),
    (os.path.join(BASE, "2024toudang", "山东省2024年艺术类本科批音乐类第2次志愿投档情况表(公布).xls"), "本科批第2次投档"),
]

records_2024 = []
for path, batch in admission_2024:
    recs = parse_admission_2024(path, batch)
    records_2024.extend(recs)
    print(f"  {batch}: {len(recs)} 条")

print(f"  2024总记录: {len(records_2024)}")

# 建两个索引
# 索引1: (code, major_code) → list of records (精确匹配)
idx_code = {}
for r in records_2024:
    key = (r["code"], r["major_code"])
    if key not in idx_code:
        idx_code[key] = []
    idx_code[key].append(r)

# 索引2: code → list of records (用于同校模糊匹配)
idx_school = {}
for r in records_2024:
    key = r["code"]
    if key not in idx_school:
        idx_school[key] = []
    idx_school[key].append(r)

# 读取 data.json
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

schools = data.get("schools", [])
print(f"\n  2025年记录: {len(schools)} 条")

matched_exact = 0
matched_fuzzy = 0
not_matched = 0

# 为每条2025年记录预计算关键词
for s in schools:
    s["_kw"] = major_keywords(s.get("major", ""))

for school in schools:
    code = school["code"]
    mc = school["major_code"]
    
    # 策略1: 精确 code + major_code 匹配 (但需验证方向关键词一致)
    key = (code, mc)
    if key in idx_code:
        school_kw = school["_kw"]
        # 提取方向性关键词 (vocal/instrumental/education)
        school_dir = school_kw & {'vocal', 'instrumental', 'education'}
        candidates = idx_code[key]
        valid = []
        for c in candidates:
            c_kw = major_keywords(c["major"])
            c_dir = c_kw & {'vocal', 'instrumental', 'education'}
            # 必须方向关键词一致 或 双方都没有方向关键词
            if school_dir == c_dir:
                valid.append(c)
            elif not school_dir and not c_dir:
                valid.append(c)
        if valid:
            best = min(valid, key=lambda x: x["line"])
            school["line2024"] = best["line"]
            school["plan2024"] = best["plan"]
            matched_exact += 1
            continue
        # 代码匹配但方向不一致，继续走模糊匹配
    
    # 策略2: 同校模糊专业名匹配 (方向关键词必须一致)
    if code in idx_school:
        school_kw = school["_kw"]
        school_dir = school_kw & {'vocal', 'instrumental', 'education'}
        candidates = idx_school[code]
        best_score = 0
        best_candidate = None
        
        for c in candidates:
            c_kw = major_keywords(c["major"])
            c_dir = c_kw & {'vocal', 'instrumental', 'education'}
            # 方向关键词必须一致 (或双方都没有)
            if school_dir != c_dir:
                if school_dir and c_dir:
                    continue  # 方向不同，跳过
            s = major_score(school_kw, c_kw)
            if s > best_score:
                best_score = s
                best_candidate = c
        
        if best_score >= 0.3 and best_candidate:
            school["line2024"] = best_candidate["line"]
            school["plan2024"] = best_candidate["plan"]
            matched_fuzzy += 1
            continue
    
    # 策略3: 同校专业名子串匹配 (也需方向一致)
    m25 = clean_major_name(school.get("major", ""))
    school_dir = school_kw & {'vocal', 'instrumental', 'education'}
    found = False
    if code in idx_school:
        for c in idx_school[code]:
            c_kw = major_keywords(c["major"])
            c_dir = c_kw & {'vocal', 'instrumental', 'education'}
            if school_dir and c_dir and school_dir != c_dir:
                continue
            m24 = clean_major_name(c["major"])
            if m25 and m24 and (m25 in m24 or m24 in m25):
                school["line2024"] = c["line"]
                school["plan2024"] = c["plan"]
                found = True
                matched_fuzzy += 1
                break
    
    if not found:
        school["line2024"] = None
        school["plan2024"] = None
        not_matched += 1

# 清理临时字段
for s in schools:
    s.pop("_kw", None)

print(f"\n  匹配结果:")
print(f"    精确匹配(code+major_code): {matched_exact} 条")
print(f"    模糊匹配(同校+专业名):     {matched_fuzzy} 条")
print(f"    未匹配:                    {not_matched} 条")
print(f"    总匹配:                    {matched_exact + matched_fuzzy} 条 ({100*(matched_exact+matched_fuzzy)//len(schools)}%)")

# 验证关键案例
print("\n  验证江汉大学 B072:")
for s in schools:
    if s["code"] == "B072":
        print(f"    {s['major_code']} {clean_major_name(s['major'])} | 2024line={s.get('line2024')} 2025line={s['line']}")

# 更新metadata
data["metadata"]["version"] = "4.1"
data["metadata"]["update_time"] = "2026-06-26"
data["metadata"]["description"] = "2024-2025年山东省艺术类本科/专科批音乐类投档录取数据（修复专业代码跨年不匹配问题）"
data["metadata"]["years"] = [2024, 2025]

# 保存
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

size = os.path.getsize("data.json") / 1024
print(f"\n✅ data.json 已更新 ({size:.1f} KB)")

# 展示一些匹配样例
samples = [s for s in schools if s.get("line2024") is not None][:5]
print("\n  匹配样例:")
for s in samples:
    trend = "📈" if s["line"] > s["line2024"] else ("📉" if s["line"] < s["line2024"] else "➡️")
    diff = s["line"] - s["line2024"]
    print(f"    {s['code']} {s['name'][:12]:12s} | {s['major_code']} {clean_major_name(s['major'])[:20]:20s} | 2024={s['line2024']:.2f} → 2025={s['line']:.2f} {trend} {diff:+.2f}")
