#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
山东省艺术统考音乐类数据自动化清洗脚本

功能：
1. 读取2025年艺术统考双达线考生文化/专业成绩一分一段表
2. 读取2025年艺术类本科批音乐类投档情况表
3. 清洗并转换为标准JSON格式
4. 生成 compressed_ranks.json 和 data.json

数据来源：
- 山东招生考试院：https://www.sdzk.cn/NewsList.aspx?BCID=1198&CID=49

使用方法：
    python clean_art_music_data.py

输出文件：
    - compressed_ranks.json (位次数据)
    - data.json (学校投档数据)
"""

import csv
import json
import os
import re
from typing import List, Dict, Optional


class ArtMusicDataCleaner:
    """艺术音乐类数据清洗器"""
    
    def __init__(self):
        # 方向关键词映射规则
        self.direction_mapping = {
            'vocal': ['声乐', '流行演唱', '音乐剧', '美声', '民族唱法'],
            'instrumental': ['器乐', '钢琴', '管弦', '中国乐器', '键盘', '西洋管弦'],
            'education': ['音乐教育', '师范类', '作曲', '录音艺术', '音乐学', '音乐治疗']
        }
        
    def read_csv_file(self, filepath: str, encoding: str = 'utf-8-sig') -> List[List[str]]:
        """
        读取CSV文件，自动尝试多种编码
        
        Args:
            filepath: 文件路径
            encoding: 首选编码
            
        Returns:
            二维列表，每行是一个字符串列表
        """
        encodings = [encoding, 'gbk', 'utf-8', 'gb2312']
        
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc, errors='ignore') as f:
                    reader = csv.reader(f)
                    rows = [row for row in reader]
                print(f"✅ 成功读取文件（编码: {enc}）: {os.path.basename(filepath)}")
                return rows
            except Exception as e:
                continue
        
        raise Exception(f"❌ 无法读取文件: {filepath}")
    
    def parse_rank_table(self, rows: List[List[str]], direction: str) -> Dict[str, int]:
        """
        解析一分一段表，提取分数和累计人数
        
        Args:
            rows: CSV行数据
            direction: 方向标识（vocal/instrumental/education/culture）
            
        Returns:
            字典 {分数: 累计人数}
        """
        result = {}
        header_found = False
        
        for i, row in enumerate(rows):
            if not row or len(row) < 2:
                continue
            
            # 跳过标题行和表头
            text = ''.join(row).strip()
            
            # 检测表头行（包含"成绩"、"分数段"、"累计"等关键词）
            if any(keyword in text for keyword in ['成绩', '分数段', '本段人数', '累计人数', '合计']):
                header_found = True
                continue
            
            # 跳过表头前的内容
            if not header_found:
                continue
            
            try:
                # 尝试提取分数和累计人数
                # 常见格式：["750", "1", "1"] 或 ["750-749", "1", "1"]
                score_str = row[0].strip()
                
                # 提取分数（取第一个数字）
                score_match = re.search(r'(\d+)', score_str)
                if not score_match:
                    continue
                
                score = int(score_match.group(1))
                
                # 提取累计人数（通常是第3列）
                if len(row) >= 3:
                    cumulative_str = row[2].strip()
                    cumulative_match = re.search(r'(\d+)', cumulative_str)
                    if cumulative_match:
                        cumulative_count = int(cumulative_match.group(1))
                        result[score] = cumulative_count
                elif len(row) >= 2:
                    # 如果只有两列，第二列可能是累计人数
                    cumulative_str = row[1].strip()
                    cumulative_match = re.search(r'(\d+)', cumulative_str)
                    if cumulative_match:
                        cumulative_count = int(cumulative_match.group(1))
                        result[score] = cumulative_count
                        
            except (ValueError, IndexError) as e:
                # 跳过无法解析的行（如合计行、空行等）
                continue
        
        print(f"   📊 {direction}: 提取到 {len(result)} 个分数点")
        return result
    
    def compress_rank_data(self, rank_dict: Dict[int, int], interval: int = 5) -> Dict[str, int]:
        """
        压缩位次数据，按间隔采样
        
        Args:
            rank_dict: 原始位数字典 {分数: 累计人数}
            interval: 采样间隔（文化课5分，专业课2分）
            
        Returns:
            压缩后的位数字典 {分数(字符串): 累计人数}
        """
        if not rank_dict:
            return {}
        
        # 按分数降序排序
        sorted_scores = sorted(rank_dict.keys(), reverse=True)
        
        compressed = {}
        last_score = None
        
        for score in sorted_scores:
            # 如果是第一个点，或者与上一个采样点差距达到interval
            if last_score is None or (last_score - score) >= interval:
                compressed[str(score)] = rank_dict[score]
                last_score = score
        
        print(f"   🗜️  压缩后: {len(compressed)} 个采样点（间隔: {interval}分）")
        return compressed
    
    def extract_culture_ranks(self) -> Dict[str, int]:
        """
        提取艺术类文化课双达线考生位次数据
        合并三个方向的文化课数据
        
        Returns:
            压缩后的位数字典
        """
        print("\n📚 正在提取文化课双达线数据...")
        
        culture_files = [
            ('2025 音乐教育 双达线考生文化成绩一分一段表.csv', 'education'),
            ('2025音乐表演-声乐 双达线考生文化成绩一分一段表.csv', 'vocal'),
            ('2025音乐表演-器乐 双达线考生文化成绩一分一段表.csv', 'instrumental')
        ]
        
        all_culture_data = {}
        
        for filepath, direction in culture_files:
            if not os.path.exists(filepath):
                print(f"   ⚠️  文件不存在: {filepath}")
                continue
            
            try:
                rows = self.read_csv_file(filepath, encoding='gbk')
                rank_dict = self.parse_rank_table(rows, f"{direction}_culture")
                
                # 合并数据（相同分数取最大累计人数）
                for score, count in rank_dict.items():
                    if score not in all_culture_data or count > all_culture_data[score]:
                        all_culture_data[score] = count
                        
            except Exception as e:
                print(f"   ❌ 处理失败: {filepath} - {str(e)}")
        
        # 压缩数据（文化课每隔5分采样）
        compressed = self.compress_rank_data(all_culture_data, interval=5)
        return compressed
    
    def extract_professional_ranks(self) -> Dict[str, Dict[str, int]]:
        """
        提取各专业方向的专业成绩位次数据
        
        Returns:
            字典 {方向: 压缩后的位数字典}
        """
        print("\n🎵 正在提取专业成绩位次数据...")
        
        professional_files = {
            'vocal': '2026_vocal.csv',
            'instrumental': '2026_instrumental.csv',
            'education': '2026_education.csv'
        }
        
        result = {}
        
        for direction, filepath in professional_files.items():
            if not os.path.exists(filepath):
                print(f"   ⚠️  文件不存在: {filepath}")
                continue
            
            try:
                rows = self.read_csv_file(filepath, encoding='utf-8-sig')
                rank_dict = self.parse_rank_table(rows, direction)
                
                # 压缩数据（专业课每隔2分采样）
                compressed = self.compress_rank_data(rank_dict, interval=2)
                result[f"{direction}_2025"] = compressed
                
            except Exception as e:
                print(f"   ❌ 处理失败: {filepath} - {str(e)}")
        
        return result
    
    def determine_direction(self, major_name: str) -> str:
        """
        根据专业名称智能判断方向
        
        Args:
            major_name: 专业名称
            
        Returns:
            方向标识 (vocal/instrumental/education)
        """
        major_lower = major_name.lower()
        
        # 按优先级检查
        for direction, keywords in self.direction_mapping.items():
            for keyword in keywords:
                if keyword in major_name:
                    return direction
        
        # 默认归为education
        return 'education'
    
    def parse_admission_table(self, filepath: str) -> List[Dict]:
        """
        解析投档情况表，提取学校和专业信息
        
        Args:
            filepath: 投档情况表文件路径
            
        Returns:
            学校专业列表
        """
        print(f"\n🏫 正在解析投档情况表: {os.path.basename(filepath)}")
        
        if not os.path.exists(filepath):
            print(f"   ⚠️  文件不存在: {filepath}")
            return []
        
        rows = self.read_csv_file(filepath, encoding='gbk')
        schools = []
        header_found = False
        
        for i, row in enumerate(rows):
            if not row or len(row) < 5:
                continue
            
            # 跳过标题和表头
            text = ''.join(row).strip()
            if any(keyword in text for keyword in ['院校', '专业', '计划', '投档', '合计']):
                header_found = True
                continue
            
            if not header_found:
                continue
            
            try:
                # 解析院校代号及名称（如 "A027北京师范大学"）
                school_full = row[0].strip() if len(row) > 0 else ""
                school_match = re.match(r'^([A-Z]\d+)(.+)$', school_full)
                
                if not school_match:
                    continue
                
                school_code = school_match.group(1)
                school_name = school_match.group(2)
                
                # 解析专业代号及名称（如 "1D音乐学(声乐)"）
                major_full = row[1].strip() if len(row) > 1 else ""
                major_match = re.match(r'^(\d+[A-Z]?)(.+)$', major_full)
                
                if not major_match:
                    continue
                
                major_code = major_match.group(1)
                major_name = major_match.group(2)
                
                # 提取计划数
                plan_str = row[2].strip() if len(row) > 2 else "0"
                plan_match = re.search(r'(\d+)', plan_str)
                plan = int(plan_match.group(1)) if plan_match else 0
                
                # 提取投档最低分（综合分）
                line_str = row[3].strip() if len(row) > 3 else "0"
                line_match = re.search(r'([\d.]+)', line_str)
                line = float(line_match.group(1)) if line_match else 0.0
                
                # 智能判断方向
                direction = self.determine_direction(major_name)
                
                # 构建学校记录
                school_record = {
                    "code": school_code,
                    "name": school_name,
                    "major_code": major_code,
                    "major": major_name,
                    "direction": direction,
                    "plan": plan,
                    "line": line,
                    "province": "",  # 需要从其他数据源补充
                    "type": ""  # 需要从其他数据源补充
                }
                
                schools.append(school_record)
                
            except Exception as e:
                # 跳过无法解析的行
                continue
        
        print(f"   ✅ 成功提取 {len(schools)} 条投档记录")
        return schools
    
    def generate_compressed_ranks(self) -> Dict:
        """
        生成 compressed_ranks.json 数据
        
        Returns:
            完整的位数字典
        """
        print("\n" + "="*70)
        print("  开始生成 compressed_ranks.json")
        print("="*70)
        
        # 提取文化课数据
        art_culture_2025 = self.extract_culture_ranks()
        
        # 提取专业数据
        professional_ranks = self.extract_professional_ranks()
        
        # 组装最终数据
        result = {
            "art_culture_2025": art_culture_2025
        }
        result.update(professional_ranks)
        
        print(f"\n📦 最终数据结构:")
        for key, value in result.items():
            print(f"   - {key}: {len(value)} 个采样点")
        
        return result
    
    def generate_school_data(self) -> Dict:
        """
        生成 data.json 数据
        
        Returns:
            包含metadata、schools、statistics的完整字典
        """
        print("\n" + "="*70)
        print("  开始生成 data.json")
        print("="*70)
        
        # 查找投档情况表文件
        admission_files = [
            '山东省2025年艺术类本科批音乐类第1次志愿投档情况表.csv',
            '2025艺术类本科批音乐类投档.csv',
            '2025艺术投档.csv'
        ]
        
        all_schools = []
        
        for filepath in admission_files:
            if os.path.exists(filepath):
                schools = self.parse_admission_table(filepath)
                all_schools.extend(schools)
                break
        
        if not all_schools:
            print("   ⚠️  未找到投档情况表文件，使用空数据")
        
        # 按方向分组统计
        direction_stats = {}
        for school in all_schools:
            direction = school['direction']
            if direction not in direction_stats:
                direction_stats[direction] = {'count': 0, 'total_plan': 0}
            direction_stats[direction]['count'] += 1
            direction_stats[direction]['total_plan'] += school['plan']
        
        # 构建元数据
        metadata = {
            "version": "2.0",
            "update_time": "2026-05-20",
            "source": "山东省教育招生考试院",
            "year": 2025,
            "category": "艺术统考音乐类",
            "description": "2025年山东省艺术类本科批音乐类投档数据"
        }
        
        # 构建统计数据
        statistics = {
            "total_schools": len(set(s['code'] for s in all_schools)),
            "total_records": len(all_schools),
            "direction_distribution": direction_stats
        }
        
        result = {
            "metadata": metadata,
            "schools": all_schools,
            "statistics": statistics
        }
        
        print(f"\n📦 数据统计:")
        print(f"   - 总学校数: {statistics['total_schools']}")
        print(f"   - 总记录数: {statistics['total_records']}")
        for direction, stats in direction_stats.items():
            print(f"   - {direction}: {stats['count']} 条记录, 计划 {stats['total_plan']} 人")
        
        return result
    
    def run(self):
        """执行完整的数据清洗流程"""
        print("\n" + "="*70)
        print("  山东省艺术统考音乐类数据清洗工具")
        print("  数据来源: https://www.sdzk.cn/NewsList.aspx?BCID=1198&CID=49")
        print("="*70)
        
        try:
            # 生成 compressed_ranks.json
            ranks_data = self.generate_compressed_ranks()
            with open('compressed_ranks.json', 'w', encoding='utf-8') as f:
                json.dump(ranks_data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ compressed_ranks.json 已生成 ({os.path.getsize('compressed_ranks.json') / 1024:.2f} KB)")
            
            # 生成 data.json
            school_data = self.generate_school_data()
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(school_data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ data.json 已生成 ({os.path.getsize('data.json') / 1024:.2f} KB)")
            
            print("\n" + "="*70)
            print("  🎉 数据清洗完成！")
            print("="*70)
            
        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    cleaner = ArtMusicDataCleaner()
    cleaner.run()
