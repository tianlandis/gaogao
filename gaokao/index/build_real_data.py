#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从6张官方XLS提取真实数据 -> data.json，0虚假数据"""
import sys, io, os, json, re
if sys.platform == 'win32': sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd

UNI_DB = {
    "A027":("北京","公办"),"A028":("北京","公办"),"A031":("北京","公办"),
    "A033":("北京","公办"),"A047":("北京","公办"),"A048":("北京","公办"),
    "A064":("上海","公办"),"A065":("上海","公办"),
    "E437":("山东","公办"),"E438":("山东","公办"),"E439":("山东","公办"),
    "E440":("山东","公办"),"E442":("山东","公办"),"E447":("山东","公办"),
    "E448":("山东","公办"),"E452":("山东","公办"),"E453":("山东","公办"),
    "E454":("山东","公办"),"E456":("山东","公办"),"E457":("山东","公办"),
    "E458":("山东","公办"),"E459":("山东","公办"),"E460":("山东","公办"),
    "E463":("山东","公办"),"E464":("山东","公办"),"E465":("山东","公办"),
    "A220":("黑龙江","公办"),"A514":("湖北","公办"),"A635":("重庆","公办"),
    "A647":("重庆","公办"),"A656":("四川","公办"),"A742":("甘肃","公办"),
    "B407":("宁夏","公办"),"B959":("黑龙江","公办"),
    "A110":("山西","公办"),"A694":("西藏","公办"),
    "D678":("陕西","民办"),"E462":("山西","公办"),
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
    "四川":["四川","成都","绵阳","内江","西华","南充","攀枝花","西南民族"],
    "湖北":["湖北","武汉","黄石","荆州","三峡","江汉","长江大学",
             "武昌","汉口","华中","中南民族","黄冈"],
    "湖南":["湖南","长沙","张家界","邵阳","怀化","湘南","中南大学","吉首","衡阳"],
    "河南":["河南","郑州","安阳","平顶山","南阳","商丘","周口","洛阳","开封"],
    "河北":["河北","石家庄","保定","邯郸","唐山","衡水","廊坊","沧州","邢台"],
    "辽宁":["辽宁","沈阳","大连","鞍山","渤海","锦州","朝阳"],
    "吉林":["吉林","长春","延边","北华","白城","通化","东北师范","吉林艺术"],
    "黑龙江":["黑龙江","哈尔滨","齐齐哈尔","伊春","牡丹江","大庆","佳木斯",
               "黑河","鸡西","绥化","东北石油","鹤岗"],
    "陕西":["陕西","西安","延安","宝鸡","渭南","商洛","咸阳"],
    "福建":["福建","福州","厦门","华侨","集美","泉州"],
    "江西":["江西","南昌","九江","上饶","宜春","景德镇","赣南","吉安"],
    "安徽":["安徽","合肥","淮北","滁州","芜湖","黄山","安庆"],
    "广西":["广西","桂林","南宁","贺州"],
    "海南":["海南","海口","琼台","三亚"],
    "新疆":["新疆","乌鲁木齐","巴音郭楞","和田","喀什","伊犁","石河子","阿勒泰","铁门关"],
    "云南":["云南","昆明","楚雄","玉溪","红河","大理","滇池"],
    "贵州":["贵州","贵阳","遵义","凯里","兴义","六盘水"],
    "重庆":["重庆","西南大学","长江师范"],
    "甘肃":["甘肃","兰州","天水","西北民族"],
    "青海":["青海","西宁"],
    "宁夏":["宁夏","银川","北方民族"],
    "内蒙古":["内蒙古","呼和浩特","包头","赤峰","呼伦贝尔"],
    "山西":["山西","太原","吕梁","忻州","长治","大同"],
}

DIR_KW = {
    "vocal":["声乐","流行演唱","演唱","音乐剧","美声","民族唱法"],
    "instrumental":["器乐","钢琴","管弦","中国乐器","键盘","电吉他",
                    "弦乐","管乐","打击乐","民乐","西洋乐","音乐表演","流行"],
    "education":["音乐教育","师范","作曲","录音艺术","音乐学","音乐治疗","艺术管理"],
}

def guess_direction(major):
    for d,kws in DIR_KW.items():
        for kw in kws:
            if kw in major: return d
    return "education"

def guess_meta(code, name):
    if code in UNI_DB: return UNI_DB[code]
    for p,kws in PROVINCE_KW.items():
        for kw in kws:
            if kw in name:
                nat = "民办" if any(x in name for x in ["民办","独立学院","城市学院","职业技术","职业学院"]) else "公办"
                return (p,nat)
    return ("未知","公办")

def parse(fp, batch, level):
    if not os.path.exists(fp): return []
    df = pd.read_excel(fp, engine='xlrd', header=None)
    rows = df.values.tolist()
    schools, header = [], False
    for row in rows:
        cells = [str(c).strip() for c in row if str(c).strip() and str(c).strip()!='nan']
        if not cells: continue
        if any(w in ''.join(cells) for w in ['专业代号','院校代号','投档计划','投档最低','录取最低']):
            header = True; continue
        if not header or len(cells)<3: continue
        try:
            mt=re.sub(r'^[A-Za-z0-9]+','',cells[0]).strip()
            sc=re.match(r'^([A-Z][0-9]+)',cells[1])
            if not sc or not mt: continue
            code=sc.group(1); name=cells[1][len(code):].strip()
            mc=re.match(r'^([A-Za-z0-9]+)',cells[0])
            mc=mc.group(1) if mc else ""
            line=float(re.sub(r'[^\d.]','',cells[-1]))
            plan=0
            if len(cells)>=4:
                nums=re.findall(r'(\d+)',str(cells[2]))
                if nums: plan=int(nums[0])
            direction=guess_direction(mt)
            province,nature=guess_meta(code,name)
            uid=f"{code}_{mc}_{batch}_2025"
            schools.append({"id":uid,"code":code,"name":name,"major_code":mc,
                "major":mt,"direction":direction,"province":province,"level":level,
                "nature":nature,"batch":batch,"line":line,"plan":plan})
        except: continue
    return schools

BATCHES=[("downloads/山东省2025年艺术类本科批音乐类第1次志愿投档情况表(公布).xls","本科批第1次投档","本科"),
         ("downloads/山东省2025年艺术类本科批音乐类第1次志愿投档情况表(公布)（补充）.xls","本科批第1次投档","本科"),
         ("downloads/山东省2025年艺术类本科批音乐类第1次志愿录取情况表.xls","本科批第1次录取","本科"),
         ("downloads/山东省2025年艺术类本科批音乐类第2次志愿投档情况表.xls","本科批第2次投档","本科"),
         ("downloads/山东省2025年艺术类专科批音乐类第1次志愿投档情况表.xls","专科批第1次投档","专科"),
         ("downloads/山东省2025年艺术类专科批音乐类第2次志愿投档情况表.xls","专科批第2次投档","专科")]

all_s=[]; seen=set()
for fp,batch,level in BATCHES:
    recs=parse(fp,batch,level)
    print(f"[{batch}] {fp.split('/')[-1][:30]}... -> {len(recs)} records")
    for s in recs:
        if s["id"] not in seen: seen.add(s["id"]);all_s.append(s)

# 统计
unknown=[s for s in all_s if s["province"]=="未知"]
print(f"\nTotal: {len(all_s)} unique, unknown province: {len(unknown)}")
if unknown:
    codes=set((s["code"],s["name"]) for s in unknown)
    print("Unknown codes:",codes)

batches={};provinces={};directions={}
for s in all_s:
    batches[s["batch"]]=batches.get(s["batch"],0)+1
    provinces[s["province"]]=provinces.get(s["province"],0)+1
    directions[s["direction"]]=directions.get(s["direction"],0)+1
print(f"\nBy batch: {batches}")
print(f"By province ({len(provinces)}): {dict(sorted(provinces.items(),key=lambda x:-x[1]))}")
print(f"By direction: {directions}")

with open("data.json",'w',encoding='utf-8') as f:
    json.dump({"schools":all_s},f,ensure_ascii=False,indent=2)
print(f"\nSAVED: {os.path.getsize('data.json')/1024:.1f}KB, {len(all_s)} schools")
