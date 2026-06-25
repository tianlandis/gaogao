#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据管道：从正确路径读取所有 XLS/CSV，重新生成 compressed_ranks.json 和 data.json

包含：
- 9个2025年一分一段表 XLS（文化3 + 专业3 + 综合3）
- 3个2026年专业成绩 CSV
- 6个投档/录取 XLS
"""
import sys, io, os, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd

# ============================================================
# 配置：数据文件路径
# ============================================================
BASE = "downloads"

# 2025年文化成绩一分一段表
CULTURE_FILES = {
    "vocal_culture_2025":  os.path.join(BASE, "2025音乐类双达线文化成绩一分一段表", "2025年本科音乐类（音乐表演-声乐）双达线文化成绩一分一段表.xls"),
    "instrumental_culture_2025": os.path.join(BASE, "2025音乐类双达线文化成绩一分一段表", "2025年本科音乐类（音乐表演-器乐）双达线文化成绩一分一段表.xls"),
    "education_culture_2025": os.path.join(BASE, "2025音乐类双达线文化成绩一分一段表", "2025年本科音乐类（音乐教育）双达线文化成绩一分一段表.xls"),
}

# 2025年专业成绩一分一段表
PROFESSIONAL_2025 = {
    "vocal_art_2025": os.path.join(BASE, "2025音乐类双达线专业成绩一分一段表", "2025年本科艺术统考音乐类（音乐表演-声乐）双达线考生专业成绩一分一段表.xls"),
    "instrumental_art_2025": os.path.join(BASE, "2025音乐类双达线专业成绩一分一段表", "2025年本科艺术统考音乐类（音乐表演-器乐）双达线考生专业成绩一分一段表.xls"),
    "education_art_2025": os.path.join(BASE, "2025音乐类双达线专业成绩一分一段表", "2025年本科艺术统考音乐类（音乐教育）双达线考生专业成绩一分一段表.xls"),
}

# 2025年综合成绩分段表
COMPREHENSIVE_2025 = {
    "vocal_2025": os.path.join(BASE, "2025综合成绩分段表", "2025年本科音乐类（音乐表演-声乐）综合成绩分段表.xls"),
    "instrumental_2025": os.path.join(BASE, "2025综合成绩分段表", "2025年本科音乐类（音乐表演-器乐）综合成绩分段表.xls"),
    "education_2025": os.path.join(BASE, "2025综合成绩分段表", "2025年本科音乐类（音乐教育）综合成绩分段表.xls"),
}

# 2026年专业成绩 CSV
CSV_2026 = {
    "vocal_art_2026": os.path.join(BASE, "2026_vocal.csv"),
    "instrumental_art_2026": os.path.join(BASE, "2026_instrumental.csv"),
    "education_art_2026": os.path.join(BASE, "2026_education.csv"),
}

# ============================================================
# Step 1: 读取一分一段表 XLS
# ============================================================
def parse_rank_xls(filepath, label):
    """解析一分一段 XLS，返回 {分数(str): 累计人数}"""
    if not os.path.exists(filepath):
        print(f"  ❌ 文件不存在: {filepath}")
        return {}
    
    df = pd.read_excel(filepath, engine='xlrd', header=None)
    result = {}
    header_found = False
    
    for _, row in df.iterrows():
        # 跳过空行
        if pd.isna(row[0]):
            continue
        
        # 检测表头
        text = str(row[0])
        if any(kw in text for kw in ['分数段', '成绩', '本段人数', '累计人数', '合计']):
            header_found = True
            continue
        if not header_found:
            continue
        
        # 提取分数（第0列）
        score_raw = str(row[0]).strip()
        score_match = re.search(r'(\d+\.?\d*)', score_raw)
        if not score_match:
            continue
        score = score_match.group(1)
        # 去掉尾部无意义的 .0
        if '.' in score and score.split('.')[1] == '0':
            score = score.split('.')[0]
        
        # 提取累计人数（第2列）
        if len(row) >= 3 and not pd.isna(row[2]):
            cumulative = int(re.search(r'(\d+)', str(row[2])).group(1))
            result[score] = cumulative
        elif len(row) >= 2 and not pd.isna(row[1]):
            cumulative = int(re.search(r'(\d+)', str(row[1])).group(1))
            result[score] = cumulative
    
    print(f"  ✅ {label}: {len(result)} 个分数点")
    return result


def parse_rank_csv(filepath, label):
    """解析一分一段 CSV，返回 {分数(str): 累计人数}"""
    if not os.path.exists(filepath):
        print(f"  ❌ 文件不存在: {filepath}")
        return {}
    
    encodings = ['utf-8-sig', 'gbk', 'utf-8', 'gb2312']
    rows = None
    for enc in encodings:
        try:
            import csv
            with open(filepath, 'r', encoding=enc) as f:
                reader = csv.reader(f)
                rows = list(reader)
            break
        except:
            continue
    
    if rows is None:
        print(f"  ❌ 无法读取: {filepath}")
        return {}
    
    result = {}
    header_found = False
    
    for row in rows:
        if not row:
            continue
        text = ''.join(str(c).strip() for c in row)
        if any(kw in text for kw in ['分数', '人数', '成绩', '累计']):
            header_found = True
            continue
        if not header_found:
            continue
        
        score_match = re.search(r'(\d+\.?\d*)', str(row[0]))
        if not score_match:
            continue
        score = score_match.group(1)
        if '.' in score and score.split('.')[1] == '0':
            score = score.split('.')[0]
        
        cum_col = 2 if len(row) >= 3 else 1
        if cum_col < len(row):
            cum_match = re.search(r'(\d+)', str(row[cum_col]))
            if cum_match:
                result[score] = int(cum_match.group(1))
    
    print(f"  ✅ {label}: {len(result)} 个分数点")
    return result


# ============================================================
# Step 2: 生成 compressed_ranks.json
# ============================================================
def build_compressed_ranks():
    print("\n" + "=" * 60)
    print("  📊 构建 compressed_ranks.json")
    print("=" * 60)
    
    all_ranks = {}
    
    # 文化成绩
    print("\n📚 文化成绩一分一段表:")
    for key, path in CULTURE_FILES.items():
        data = parse_rank_xls(path, key)
        if data:
            all_ranks[key] = dict(sorted(data.items(), key=lambda x: int(x[0]), reverse=True))
    
    # 专业成绩 (2025)
    print("\n🎵 专业成绩一分一段表 (2025):")
    for key, path in PROFESSIONAL_2025.items():
        data = parse_rank_xls(path, key)
        if data:
            all_ranks[key] = dict(sorted(data.items(), key=lambda x: float(x[0]), reverse=True))
    
    # 综合成绩
    print("\n🏆 综合成绩分段表 (2025):")
    for key, path in COMPREHENSIVE_2025.items():
        data = parse_rank_xls(path, key)
        if data:
            all_ranks[key] = dict(sorted(data.items(), key=lambda x: float(x[0]), reverse=True))
    
    # 2026 专业成绩 CSV
    print("\n📈 专业成绩 (2026):")
    for key, path in CSV_2026.items():
        data = parse_rank_csv(path, key)
        if data:
            all_ranks[key] = dict(sorted(data.items(), key=lambda x: float(x[0]), reverse=True))
    
    # 保存
    with open("compressed_ranks.json", "w", encoding="utf-8") as f:
        json.dump(all_ranks, f, ensure_ascii=False, indent=2)
    
    size = os.path.getsize("compressed_ranks.json") / 1024
    print(f"\n✅ compressed_ranks.json 已保存 ({size:.1f} KB)")
    print(f"   包含 {len(all_ranks)} 个数据集:")
    for k, v in all_ranks.items():
        scores = list(v.keys())
        print(f"     {k}: {len(v)}点, 最高={scores[0]}, 最低={scores[-1]}")
    return all_ranks


# ============================================================
# Step 3: 生成 data.json (投档录取数据)
# ============================================================
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
                return (p, "公办")  # 默认公办
    return ("", "公办")

def parse_admission_xls(filepath, batch_label, is_vocational=False):
    """解析投档/录取 XLS
    投档表(5列): [0]=序列号, [1]=专业, [2]=院校, [3]=计划数, [4]=最低分
    录取表(4列): [0]=序列号, [1]=专业, [2]=院校, [3]=最低分
    """
    if not os.path.exists(filepath):
        print(f"  ⚠️  文件不存在: {filepath}")
        return []
    
    df = pd.read_excel(filepath, engine='xlrd', header=None)
    rows_list = []
    header_found = False
    ncols = df.shape[1]  # 判断列数: 5=投档表, 4=录取表
    
    for _, row in df.iterrows():
        # 用列2(院校)判断是否为空行
        if pd.isna(row[2]) or pd.isna(row[1]):
            continue
        
        # 检测表头行
        row_text = ''.join(str(c) for c in row if not pd.isna(c))
        if any(kw in row_text for kw in ['院校代号及名称', '专业代号及名称', '投档计划', '投档最低', '录取最低']):
            header_found = True
            continue
        if not header_found:
            continue
        
        # 解析专业代码和名称 (第1列: "1D音乐学(声乐)")
        major_full = str(row[1]).strip()
        major_match = re.match(r'^([0-9A-Za-z]+)\s*(.+)$', major_full)
        if not major_match:
            continue
        major_code = major_match.group(1)
        major_name = major_match.group(2).strip()
        
        # 解析院校代码和名称 (第2列: "A027北京师范大学")
        school_full = str(row[2]).strip()
        school_match = re.match(r'^([A-Z]\d+)\s*(.+)$', school_full)
        if not school_match:
            continue
        school_code = school_match.group(1)
        school_name = school_match.group(2).strip()
        
        # 计划数: 5列表从第3列读，4列表无计划数
        plan = 0
        plan_col = 3
        score_col = 3 if ncols <= 4 else 4
        
        if ncols >= 5 and not pd.isna(row[plan_col]):
            plan_match = re.search(r'(\d+)', str(row[plan_col]))
            if plan_match:
                plan = int(plan_match.group(1))
        
        # 最低分
        line = 0.0
        if not pd.isna(row[score_col]):
            line_match = re.search(r'([\d.]+)', str(row[score_col]))
            if line_match:
                line = float(line_match.group(1))
        
        direction = guess_direction(major_name)
        province, nature = guess_meta(school_code, school_name)
        
        level = "专科" if is_vocational else "本科"
        
        row_id = f"{school_code}_{major_code}_{batch_label}_2025"
        
        rows_list.append({
            "id": row_id,
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


def build_data_json():
    print("\n" + "=" * 60)
    print("  🏫 构建 data.json (投档录取数据)")
    print("=" * 60)
    
    admission_files = [
        (os.path.join(BASE, "山东省2025年艺术类本科批音乐类第1次志愿投档情况表(公布).xls"), "本科批第1次投档"),
        (os.path.join(BASE, "山东省2025年艺术类本科批音乐类第1次志愿投档情况表(公布)（补充）.xls"), "本科批第1次投档"),
        (os.path.join(BASE, "山东省2025年艺术类本科批音乐类第1次志愿录取情况表.xls"), "本科批第1次录取"),
        (os.path.join(BASE, "山东省2025年艺术类本科批音乐类第2次志愿投档情况表.xls"), "本科批第2次投档"),
        (os.path.join(BASE, "山东省2025年艺术类专科批音乐类第1次志愿投档情况表.xls"), "专科批第1次投档"),
        (os.path.join(BASE, "山东省2025年艺术类专科批音乐类第2次志愿投档情况表.xls"), "专科批第2次投档"),
    ]
    
    all_records = []
    seen = set()
    
    for path, batch in admission_files:
        is_voc = "专科" in batch
        records = parse_admission_xls(path, batch, is_vocational=is_voc)
        
        # 去重：按 code + major_code + batch 保留最高分
        for rec in records:
            key = f"{rec['code']}_{rec['major_code']}_{rec['batch']}"
            if key in seen:
                continue
            seen.add(key)
            all_records.append(rec)
        
        print(f"  {batch}: {len(records)} 条记录")
    
    # 构建 data.json
    metadata = {
        "version": "3.0",
        "update_time": "2026-06-25",
        "source": "山东省教育招生考试院",
        "year": 2025,
        "category": "艺术统考音乐类",
        "description": "2025年山东省艺术类本科/专科批音乐类投档录取数据"
    }
    
    schools = sorted(all_records, key=lambda x: (x['code'], x['major_code']))
    
    # 统计
    directions = {"vocal": 0, "instrumental": 0, "education": 0}
    for s in schools:
        if s['direction'] in directions:
            directions[s['direction']] += 1
    
    data = {
        "metadata": metadata,
        "schools": schools,
        "statistics": {
            "total_schools": len(set(s['code'] for s in schools)),
            "total_records": len(schools),
            "direction_distribution": directions
        }
    }
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    size = os.path.getsize("data.json") / 1024
    print(f"\n✅ data.json 已保存 ({size:.1f} KB)")
    print(f"   总记录: {len(schools)} 条")
    print(f"   院校数: {len(set(s['code'] for s in schools))} 所")
    print(f"   声乐: {directions.get('vocal', 0)} | 器乐: {directions.get('instrumental', 0)} | 音教: {directions.get('education', 0)}")
    
    return data


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  山东省2026年音乐类统考志愿填报 — 数据管道 v3.0")
    print("=" * 60)
    
    # Step 1: 生成 compressed_ranks.json
    build_compressed_ranks()
    
    # Step 2: 生成 data.json
    build_data_json()
    
    print("\n" + "=" * 60)
    print("  🎉 所有数据更新完成！")
    print("=" * 60)
