#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
山东省2025年艺术类音乐类全批次投档录取表智能清洗合并脚本

功能：
1. 读取6个官方投档/录取表格
2. 自动补齐省份、公办/民办、本科/专科等元数据
3. 智能拆分音乐方向（vocal/instrumental/education）
4. 去重合并输出到 data.json

数据来源：
- NewsID=6986: 本科批第1次志愿投档情况表(公布) + 补充表
- NewsID=6989: 本科批第1次志愿录取情况表
- NewsID=7001: 本科批第2次志愿投档情况表
- NewsID=7009: 专科批第1次志愿投档情况表
- NewsID=7018: 专科批第2次志愿投档情况表

使用方法：
    python merge_all_admission_data.py

输出文件：
    - data.json (全量合并后的学校投档数据)
"""

import csv
import json
import os
import re
from typing import List, Dict, Optional


class SmartAdmissionMerger:
    """智能投档数据合并器"""
    
    def __init__(self):
        # ==================== 1. 顶端内置高精度院校权威字典表 ====================
        self.UNIVERSITY_DB = {
            # 北京地区
            "A027": {"province": "北京", "nature": "公办", "level": "本科"},
            "A028": {"province": "北京", "nature": "公办", "level": "本科"},
            "A031": {"province": "北京", "nature": "公办", "level": "本科"},
            "A033": {"province": "北京", "nature": "公办", "level": "本科"},
            "A045": {"province": "山东", "nature": "公办", "level": "本科"},
            
            # 山东本地高校（重点）
            "E437": {"province": "山东", "nature": "公办", "level": "本科"},  # 山东师范大学
            "E438": {"province": "山东", "nature": "公办", "level": "本科"},  # 山东管理学院
            "E439": {"province": "山东", "nature": "公办", "level": "本科"},  # 山东女子学院
            "E440": {"province": "山东", "nature": "公办", "level": "本科"},  # 山东青年政治学院
            "E441": {"province": "山东", "nature": "公办", "level": "本科"},  # 山东政法学院
            "E442": {"province": "山东", "nature": "公办", "level": "本科"},  # 齐鲁师范学院
            "E443": {"province": "山东", "nature": "公办", "level": "本科"},  # 山东农业工程学院
            "E444": {"province": "山东", "nature": "公办", "level": "本科"},  # 山东第一医科大学
            "E445": {"province": "山东", "nature": "公办", "level": "本科"},  # 齐鲁工业大学
            "E446": {"province": "山东", "nature": "公办", "level": "本科"},  # 山东中医药大学
            "E447": {"province": "山东", "nature": "公办", "level": "本科"},  # 曲阜师范大学
            "E448": {"province": "山东", "nature": "公办", "level": "本科"},  # 聊城大学
            "E449": {"province": "山东", "nature": "公办", "level": "本科"},  # 德州学院
            "E450": {"province": "山东", "nature": "公办", "level": "本科"},  # 滨州学院
            "E451": {"province": "山东", "nature": "公办", "level": "本科"},  # 济宁学院
            "E452": {"province": "山东", "nature": "公办", "level": "本科"},  # 临沂大学
            "E453": {"province": "山东", "nature": "公办", "level": "本科"},  # 泰山学院
            "E454": {"province": "山东", "nature": "公办", "level": "本科"},  # 潍坊学院
            "E455": {"province": "山东", "nature": "公办", "level": "本科"},  # 菏泽学院
            "E456": {"province": "山东", "nature": "公办", "level": "本科"},  # 枣庄学院
            "E457": {"province": "山东", "nature": "公办", "level": "本科"},  # 山东交通学院
            "E458": {"province": "山东", "nature": "公办", "level": "本科"},  # 山东工商学院
            "E459": {"province": "山东", "nature": "公办", "level": "本科"},  # 烟台大学
            "E460": {"province": "山东", "nature": "公办", "level": "本科"},  # 青岛大学
            "E461": {"province": "山东", "nature": "公办", "level": "本科"},  # 青岛科技大学
            "E462": {"province": "山东", "nature": "公办", "level": "本科"},  # 青岛理工大学
            "E463": {"province": "山东", "nature": "公办", "level": "本科"},  # 青岛农业大学
            "E464": {"province": "山东", "nature": "公办", "level": "本科"},  # 鲁东大学
            "E465": {"province": "山东", "nature": "公办", "level": "本科"},  # 济南大学
            
            # 艺术类专业院校
            "C001": {"province": "北京", "nature": "公办", "level": "本科"},  # 中国音乐学院
            "C002": {"province": "北京", "nature": "公办", "level": "本科"},  # 中央音乐学院
            "C003": {"province": "上海", "nature": "公办", "level": "本科"},  # 上海音乐学院
            "C004": {"province": "四川", "nature": "公办", "level": "本科"},  # 四川音乐学院
            "C005": {"province": "天津", "nature": "公办", "level": "本科"},  # 天津音乐学院
            "C006": {"province": "沈阳", "nature": "公办", "level": "本科"},  # 沈阳音乐学院
            "C007": {"province": "西安", "nature": "公办", "level": "本科"},  # 西安音乐学院
            "C008": {"province": "武汉", "nature": "公办", "level": "本科"},  # 武汉音乐学院
            "C009": {"province": "浙江", "nature": "公办", "level": "本科"},  # 浙江音乐学院
            "C010": {"province": "哈尔滨", "nature": "公办", "level": "本科"}, # 哈尔滨音乐学院
            
            # 中外合作/特殊性质
            "F401": {"province": "广东", "nature": "中外合作", "level": "本科"},
            "F407": {"province": "香港", "nature": "公办", "level": "本科"},
            
            # 更多常见院校代码（根据实际需要扩展）
            "A001": {"province": "北京", "nature": "公办", "level": "本科"},  # 北京大学
            "A002": {"province": "北京", "nature": "公办", "level": "本科"},  # 中国人民大学
            "A003": {"province": "北京", "nature": "公办", "level": "本科"},  # 清华大学
        }
        
        # ==================== 2. 智能启发式规则配置 ====================
        self.PROVINCE_KEYWORDS = {
            "山东": ["山东", "齐鲁", "济南", "青岛", "烟台", "潍坊", "临沂", "泰山", "曲阜", "聊城", "菏泽", "枣庄", "德州", "滨州", "济宁", "日照", "威海", "东营", "莱芜", "淄博"],
            "北京": ["北京", "首都", "北大", "清华", "人大"],
            "上海": ["上海", "复旦", "交大", "同济", "华东"],
            "天津": ["天津", "南开"],
            "江苏": ["南京", "江苏", "苏州", "无锡", "常州", "徐州", "南通", "连云港", "淮安", "盐城", "扬州", "镇江", "泰州", "宿迁"],
            "浙江": ["浙江", "杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴", "金华", "衢州", "舟山", "台州", "丽水"],
            "广东": ["广东", "广州", "深圳", "珠海", "汕头", "佛山", "韶关", "湛江", "肇庆", "江门", "茂名", "惠州", "梅州", "汕尾", "河源", "阳江", "清远", "东莞", "中山", "潮州", "揭阳", "云浮"],
            "四川": ["四川", "成都", "自贡", "攀枝花", "泸州", "德阳", "绵阳", "广元", "遂宁", "内江", "乐山", "南充", "眉山", "宜宾", "广安", "达州", "雅安", "巴中", "资阳"],
            "湖北": ["湖北", "武汉", "黄石", "十堰", "宜昌", "襄阳", "鄂州", "荆门", "孝感", "荆州", "黄冈", "咸宁", "随州", "恩施"],
            "湖南": ["湖南", "长沙", "株洲", "湘潭", "衡阳", "邵阳", "岳阳", "常德", "张家界", "益阳", "郴州", "永州", "怀化", "娄底", "湘西"],
            "河南": ["河南", "郑州", "开封", "洛阳", "平顶山", "安阳", "鹤壁", "新乡", "焦作", "濮阳", "许昌", "漯河", "三门峡", "南阳", "商丘", "信阳", "周口", "驻马店"],
            "河北": ["河北", "石家庄", "唐山", "秦皇岛", "邯郸", "邢台", "保定", "张家口", "承德", "沧州", "廊坊", "衡水"],
            "辽宁": ["辽宁", "沈阳", "大连", "鞍山", "抚顺", "本溪", "丹东", "锦州", "营口", "阜新", "辽阳", "盘锦", "铁岭", "朝阳", "葫芦岛"],
            "吉林": ["吉林", "长春", "吉林", "四平", "辽源", "通化", "白山", "松原", "白城", "延边"],
            "黑龙江": ["黑龙江", "哈尔滨", "齐齐哈尔", "鸡西", "鹤岗", "双鸭山", "大庆", "伊春", "佳木斯", "七台河", "牡丹江", "黑河", "绥化", "大兴安岭"],
            "陕西": ["陕西", "西安", "铜川", "宝鸡", "咸阳", "渭南", "延安", "汉中", "榆林", "安康", "商洛"],
            "甘肃": ["甘肃", "兰州", "嘉峪关", "金昌", "白银", "天水", "武威", "张掖", "平凉", "酒泉", "庆阳", "定西", "陇南", "临夏", "甘南"],
            "福建": ["福建", "福州", "厦门", "莆田", "三明", "泉州", "漳州", "南平", "龙岩", "宁德"],
            "江西": ["江西", "南昌", "景德镇", "萍乡", "九江", "新余", "鹰潭", "赣州", "吉安", "宜春", "抚州", "上饶"],
            "安徽": ["安徽", "合肥", "芜湖", "蚌埠", "淮南", "马鞍山", "淮北", "铜陵", "安庆", "黄山", "滁州", "阜阳", "宿州", "六安", "亳州", "池州", "宣城"],
            "云南": ["云南", "昆明", "曲靖", "玉溪", "保山", "昭通", "丽江", "普洱", "临沧", "楚雄", "红河", "文山", "西双版纳", "大理", "德宏", "怒江", "迪庆"],
            "贵州": ["贵州", "贵阳", "六盘水", "遵义", "安顺", "毕节", "铜仁", "黔西南", "黔东南", "黔南"],
            "广西": ["广西", "南宁", "柳州", "桂林", "梧州", "北海", "防城港", "钦州", "贵港", "玉林", "百色", "贺州", "河池", "来宾", "崇左"],
            "海南": ["海南", "海口", "三亚", "三沙", "儋州"],
            "重庆": ["重庆"],
            "内蒙古": ["内蒙古", "呼和浩特", "包头", "乌海", "赤峰", "通辽", "鄂尔多斯", "呼伦贝尔", "巴彦淖尔", "乌兰察布", "兴安", "锡林郭勒", "阿拉善"],
            "宁夏": ["宁夏", "银川", "石嘴山", "吴忠", "固原", "中卫"],
            "新疆": ["新疆", "乌鲁木齐", "克拉玛依", "吐鲁番", "哈密", "昌吉", "博尔塔拉", "巴音郭楞", "阿克苏", "克孜勒苏", "喀什", "和田", "伊犁", "塔城", "阿勒泰"],
            "西藏": ["西藏", "拉萨", "日喀则", "昌都", "林芝", "山南", "那曲", "阿里"],
            "青海": ["青海", "西宁", "海东", "海北", "黄南", "海南", "果洛", "玉树", "海西"],
        }
        
        self.PRIVATE_KEYWORDS = ["独立学院", "分校", "城市学院", "世纪学院", "民办", "学院(民办)", "职业技术", "职业", "科技", "工商", "财经", "外国语"]
        
        # ==================== 3. 文件来源与批次映射 ====================
        self.FILE_BATCH_MAP = {
            "6986_1": {"batch": "本科批第1次投档", "level": "本科"},
            "6986_2": {"batch": "本科批第1次投档(补充)", "level": "本科"},
            "6989": {"batch": "本科批第1次录取", "level": "本科"},
            "7001": {"batch": "本科批第2次投档", "level": "本科"},
            "7009": {"batch": "专科批第1次投档", "level": "专科"},
            "7018": {"batch": "专科批第2次投档", "level": "专科"},
        }
        
        # ==================== 4. 音乐方向关键词映射 ====================
        self.DIRECTION_KEYWORDS = {
            "vocal": ["声乐", "流行演唱", "音乐剧", "美声", "民族唱法", "演唱"],
            "instrumental": ["器乐", "钢琴", "管弦", "中国乐器", "键盘", "西洋管弦", "器乐方向"],
            "education": ["音乐教育", "师范类", "作曲", "录音艺术", "音乐学", "音乐治疗", "音乐表演"]
        }
    
    def read_excel_file(self, filepath: str) -> Optional[List[List[str]]]:
        """
        读取Excel文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            二维列表，如果失败返回None
        """
        try:
            import pandas as pd
            
            ext = os.path.splitext(filepath)[1].lower()
            if ext == '.xlsx':
                df = pd.read_excel(filepath, engine='openpyxl', header=None)
            else:  # .xls
                df = pd.read_excel(filepath, engine='xlrd', header=None)
            
            rows = df.values.tolist()
            rows = [[str(cell) if pd.notna(cell) else '' for cell in row] for row in rows]
            
            print(f"✅ 成功读取: {os.path.basename(filepath)} ({len(rows)}行)")
            return rows
            
        except ImportError:
            print(f"❌ 缺少pandas库，请安装: pip install pandas openpyxl xlrd")
            return None
        except Exception as e:
            print(f"❌ 读取失败: {os.path.basename(filepath)} - {str(e)}")
            return None
    
    def determine_province(self, school_name: str) -> str:
        """
        智能判定省份
        
        Args:
            school_name: 学校名称
            
        Returns:
            省份名称
        """
        for province, keywords in self.PROVINCE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in school_name:
                    return province
        
        return "其它省份"
    
    def determine_nature(self, school_name: str, school_code: str) -> str:
        """
        智能判定公办/民办性质
        
        Args:
            school_name: 学校名称
            school_code: 学校代码
            
        Returns:
            "公办" 或 "民办" 或 "中外合作"
        """
        # 优先从权威字典查询
        if school_code in self.UNIVERSITY_DB:
            return self.UNIVERSITY_DB[school_code]["nature"]
        
        # 启发式规则
        for keyword in self.PRIVATE_KEYWORDS:
            if keyword in school_name:
                return "民办"
        
        return "公办"
    
    def determine_level_from_batch(self, batch_info: Dict) -> str:
        """
        从批次信息中提取层次
        
        Args:
            batch_info: 批次信息字典
            
        Returns:
            "本科" 或 "专科"
        """
        return batch_info.get("level", "本科")
    
    def determine_direction(self, major_name: str) -> str:
        """
        智能判定音乐方向
        
        Args:
            major_name: 专业名称
            
        Returns:
            "vocal" / "instrumental" / "education"
        """
        for direction, keywords in self.DIRECTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in major_name:
                    return direction
        
        return "education"  # 默认归为education
    
    def parse_admission_table(self, rows: List[List[str]], file_key: str) -> List[Dict]:
        """
        解析单个投档表
        
        Args:
            rows: Excel行数据
            file_key: 文件标识（如 "6986_1"）
            
        Returns:
            学校记录列表
        """
        batch_info = self.FILE_BATCH_MAP.get(file_key, {"batch": "未知批次", "level": "本科"})
        schools = []
        header_found = False
        
        print(f"\n📊 正在解析 {file_key} ({batch_info['batch']})...")
        
        for i, row in enumerate(rows):
            if not row or len(row) < 4:
                continue
            
            # 跳过标题和表头
            text = ''.join(str(cell).strip() for cell in row)
            if any(keyword in text for keyword in ['院校', '专业', '计划', '投档', '合计', '录取']):
                header_found = True
                continue
            
            if not header_found:
                continue
            
            try:
                # 解析院校代号及名称（如 "A027北京师范大学"）
                school_full = str(row[0]).strip()
                school_match = re.match(r'^([A-Z]\d+)(.+)$', school_full)
                
                if not school_match:
                    continue
                
                school_code = school_match.group(1)
                school_name = school_match.group(2)
                
                # 解析专业代号及名称（如 "1D音乐学(声乐)"）
                major_full = str(row[1]).strip() if len(row) > 1 else ""
                major_match = re.match(r'^(\d+[A-Z]?)(.+)$', major_full)
                
                if not major_match:
                    continue
                
                major_code = major_match.group(1)
                major_name = major_match.group(2)
                
                # 提取计划数
                plan_str = str(row[2]).strip() if len(row) > 2 else "0"
                plan_match = re.search(r'(\d+)', plan_str)
                plan = int(plan_match.group(1)) if plan_match else 0
                
                # 提取投档最低分（综合分）
                line_str = str(row[3]).strip() if len(row) > 3 else "0"
                line_match = re.search(r'([\d.]+)', line_str)
                line = float(line_match.group(1)) if line_match else 0.0
                
                # ==================== 智能补齐元数据 ====================
                # 1. 省份判定
                if school_code in self.UNIVERSITY_DB:
                    province = self.UNIVERSITY_DB[school_code]["province"]
                else:
                    province = self.determine_province(school_name)
                
                # 2. 公办/民办判定
                nature = self.determine_nature(school_name, school_code)
                
                # 3. 层次判定（从批次信息获取）
                level = self.determine_level_from_batch(batch_info)
                
                # 4. 音乐方向判定
                direction = self.determine_direction(major_name)
                
                # 5. 生成唯一ID
                unique_id = f"{school_code}_{major_code}_{file_key}_2025"
                
                # 构建学校记录
                school_record = {
                    "id": unique_id,
                    "code": school_code,
                    "name": school_name,
                    "major_code": major_code,
                    "major": major_name,
                    "direction": direction,
                    "province": province,
                    "level": level,
                    "nature": nature,
                    "batch": batch_info["batch"],
                    "line": line,
                    "plan": plan
                }
                
                schools.append(school_record)
                
            except Exception as e:
                # 跳过无法解析的行
                continue
        
        print(f"   ✅ 成功提取 {len(schools)} 条记录")
        return schools
    
    def deduplicate_schools(self, schools: List[Dict]) -> List[Dict]:
        """
        去重合并（保留最高分）
        
        Args:
            schools: 学校记录列表
            
        Returns:
            去重后的学校记录列表
        """
        print(f"\n🔄 开始去重合并...")
        print(f"   原始记录数: {len(schools)}")
        
        # 使用字典去重，key为 "code_major_batch"
        unique_dict = {}
        
        for school in schools:
            key = f"{school['code']}_{school['major_code']}_{school['batch']}"
            
            if key not in unique_dict:
                unique_dict[key] = school
            else:
                # 如果已存在，保留投档线更高的记录
                existing = unique_dict[key]
                if school['line'] > existing['line']:
                    unique_dict[key] = school
        
        deduplicated = list(unique_dict.values())
        print(f"   去重后记录数: {len(deduplicated)}")
        print(f"   删除重复记录: {len(schools) - len(deduplicated)}")
        
        return deduplicated
    
    def run(self):
        """执行完整的数据清洗合并流程"""
        print("\n" + "="*70)
        print("  山东省2025年艺术类音乐类全批次投档数据智能合并工具")
        print("="*70)
        
        # 定义6个文件及其标识
        files_to_process = [
            ("6986_1", "山东省2025年艺术类本科批音乐类第1次志愿投档情况表(公布).xls"),
            ("6986_2", "山东省2025年艺术类本科批音乐类第1次志愿投档情况表(公布)（补充）.xls"),
            ("6989", "山东省2025年艺术类本科批音乐类第1次志愿录取情况表.xls"),
            ("7001", "山东省2025年艺术类本科批音乐类第2次志愿投档情况表.xls"),
            ("7009", "山东省2025年艺术类专科批音乐类第1次志愿投档情况表.xls"),
            ("7018", "山东省2025年艺术类专科批音乐类第2次志愿投档情况表.xls"),
        ]
        
        all_schools = []
        
        # 循环读取所有文件
        for file_key, filename in files_to_process:
            if os.path.exists(filename):
                rows = self.read_excel_file(filename)
                if rows:
                    schools = self.parse_admission_table(rows, file_key)
                    all_schools.extend(schools)
            else:
                print(f"⚠️  文件不存在: {filename}")
        
        if not all_schools:
            print("\n❌ 错误: 没有成功提取任何数据！")
            print("💡 请确保已将6个Excel文件下载到当前目录")
            return
        
        # 去重合并
        deduplicated_schools = self.deduplicate_schools(all_schools)
        
        # 构建最终数据结构
        result = {
            "schools": deduplicated_schools
        }
        
        # 保存到文件
        output_file = 'data.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        file_size = os.path.getsize(output_file) / 1024
        print(f"\n✅ {output_file} 已生成 ({file_size:.2f} KB)")
        
        # 统计信息
        print(f"\n📦 数据统计:")
        print(f"   总记录数: {len(deduplicated_schools)}")
        
        # 按方向统计
        direction_stats = {}
        for school in deduplicated_schools:
            direction = school['direction']
            direction_stats[direction] = direction_stats.get(direction, 0) + 1
        
        print(f"   方向分布:")
        for direction, count in sorted(direction_stats.items()):
            print(f"     - {direction}: {count} 条")
        
        # 按批次统计
        batch_stats = {}
        for school in deduplicated_schools:
            batch = school['batch']
            batch_stats[batch] = batch_stats.get(batch, 0) + 1
        
        print(f"   批次分布:")
        for batch, count in sorted(batch_stats.items()):
            print(f"     - {batch}: {count} 条")
        
        # 按省份统计
        province_stats = {}
        for school in deduplicated_schools:
            province = school['province']
            province_stats[province] = province_stats.get(province, 0) + 1
        
        print(f"   省份分布（前10）:")
        for province, count in sorted(province_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"     - {province}: {count} 条")
        
        # 按性质统计
        nature_stats = {}
        for school in deduplicated_schools:
            nature = school['nature']
            nature_stats[nature] = nature_stats.get(nature, 0) + 1
        
        print(f"   性质分布:")
        for nature, count in sorted(nature_stats.items()):
            print(f"     - {nature}: {count} 条")
        
        print("\n" + "="*70)
        print("  🎊 数据清洗合并完成！")
        print("="*70)


if __name__ == '__main__':
    merger = SmartAdmissionMerger()
    merger.run()
