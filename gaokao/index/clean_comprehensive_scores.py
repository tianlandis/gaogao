#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
山东省2025年音乐类综合成绩分段表清洗脚本

功能：
1. 读取三个方向的综合成绩分段表（声乐、器乐、音教）
2. 提取综合分和累计人数
3. 生成 compressed_ranks.json

数据来源：
- 山东招生考试院：https://www.sdzk.cn/NewsInfo.aspx?NewsID=6954

使用方法：
    python clean_comprehensive_scores.py

输出文件：
    - compressed_ranks.json (仅包含综合分位次数据)
"""

import csv
import json
import os
import re
from typing import List, Dict, Optional


class ComprehensiveScoreCleaner:
    """综合成绩分段表清洗器"""
    
    def __init__(self):
        # 方向映射配置
        self.direction_config = {
            'vocal_2025': {
                'keywords': ['声乐', '音乐表演-声乐'],
                'files': [
                    '2025年本科艺术统考音乐类（音乐表演-声乐）综合成绩分段表.xls',
                    '2025年本科艺术统考音乐类（音乐表演-声乐）综合成绩分段表.xlsx',
                    '2025年本科艺术统考音乐类（音乐表演-声乐）综合成绩分段表.csv',
                    'vocal_comprehensive.csv'
                ]
            },
            'instrumental_2025': {
                'keywords': ['器乐', '音乐表演-器乐'],
                'files': [
                    '2025年本科艺术统考音乐类（音乐表演-器乐）综合成绩分段表.xls',
                    '2025年本科艺术统考音乐类（音乐表演-器乐）综合成绩分段表.xlsx',
                    '2025年本科艺术统考音乐类（音乐表演-器乐）综合成绩分段表.csv',
                    'instrumental_comprehensive.csv'
                ]
            },
            'education_2025': {
                'keywords': ['音乐教育', '音教'],
                'files': [
                    '2025年本科艺术统考音乐类（音乐教育）综合成绩分段表.xls',
                    '2025年本科艺术统考音乐类（音乐教育）综合成绩分段表.xlsx',
                    '2025年本科艺术统考音乐类（音乐教育）综合成绩分段表.csv',
                    'education_comprehensive.csv'
                ]
            }
        }
    
    def read_csv_file(self, filepath: str) -> List[List[str]]:
        """
        读取CSV文件，自动尝试多种编码
        
        Args:
            filepath: 文件路径
            
        Returns:
            二维列表，每行是一个字符串列表
        """
        encodings = ['utf-8-sig', 'gbk', 'utf-8', 'gb2312']
        
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc, errors='ignore') as f:
                    reader = csv.reader(f)
                    rows = [row for row in reader]
                print(f"✅ 成功读取CSV文件（编码: {enc}）: {os.path.basename(filepath)}")
                return rows
            except Exception as e:
                continue
        
        raise Exception(f"❌ 无法读取CSV文件: {filepath}")
    
    def try_read_excel(self, filepath: str) -> Optional[List[List[str]]]:
        """
        尝试读取Excel文件（需要pandas和openpyxl/xlrd）
        
        Args:
            filepath: 文件路径
            
        Returns:
            二维列表，如果失败返回None
        """
        try:
            import pandas as pd
            
            # 根据文件扩展名选择引擎
            if filepath.endswith('.xlsx'):
                df = pd.read_excel(filepath, engine='openpyxl', header=None)
            else:  # .xls
                df = pd.read_excel(filepath, engine='xlrd', header=None)
            
            # 转换为二维列表
            rows = df.values.tolist()
            # 将NaN转换为空字符串
            rows = [[str(cell) if pd.notna(cell) else '' for cell in row] for row in rows]
            
            print(f"✅ 成功读取Excel文件: {os.path.basename(filepath)}")
            return rows
            
        except ImportError:
            print(f"⚠️  缺少pandas库，无法读取Excel文件: {os.path.basename(filepath)}")
            print(f"💡 请安装: pip install pandas openpyxl xlrd")
            return None
        except Exception as e:
            print(f"❌ 读取Excel失败: {os.path.basename(filepath)} - {str(e)}")
            return None
    
    def read_file(self, filepath: str) -> Optional[List[List[str]]]:
        """
        智能读取文件（支持CSV和Excel）
        
        Args:
            filepath: 文件路径
            
        Returns:
            二维列表，如果失败返回None
        """
        if not os.path.exists(filepath):
            return None
        
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.csv':
            return self.read_csv_file(filepath)
        elif ext in ['.xls', '.xlsx']:
            return self.try_read_excel(filepath)
        else:
            print(f"⚠️  不支持的文件格式: {ext}")
            return None
    
    def parse_score_table(self, rows: List[List[str]], direction: str) -> Dict[str, int]:
        """
        解析综合成绩分段表，提取综合分和累计人数
        
        Args:
            rows: CSV/Excel行数据
            direction: 方向标识（vocal_2025/instrumental_2025/education_2025）
            
        Returns:
            字典 {综合分(字符串): 累计人数}
        """
        result = {}
        header_found = False
        
        print(f"\n📊 正在解析 {direction} 数据...")
        
        for i, row in enumerate(rows):
            if not row or len(row) < 2:
                continue
            
            # 跳过标题行和表头
            text = ''.join(str(cell).strip() for cell in row)
            
            # 检测表头行（包含"综合成绩"、"分数段"、"累计"等关键词）
            if any(keyword in text for keyword in ['综合成绩', '成绩分数段', '本段人数', '累计人数', '合计']):
                header_found = True
                continue
            
            # 跳过表头前的内容
            if not header_found:
                continue
            
            try:
                # 提取综合分（第一列）
                score_str = str(row[0]).strip()
                
                # 验证是否为有效的数字（支持小数）
                if not re.match(r'^\d+\.?\d*$', score_str):
                    continue
                
                # 保持原始精度（不四舍五入）
                score_key = score_str
                
                # 提取累计人数（通常是第三列，索引为2）
                if len(row) >= 3:
                    cumulative_str = str(row[2]).strip()
                    
                    # 提取数字
                    cumulative_match = re.search(r'(\d+)', cumulative_str)
                    if cumulative_match:
                        cumulative_count = int(cumulative_match.group(1))
                        result[score_key] = cumulative_count
                elif len(row) >= 2:
                    # 如果只有两列，第二列可能是累计人数
                    cumulative_str = str(row[1]).strip()
                    cumulative_match = re.search(r'(\d+)', cumulative_str)
                    if cumulative_match:
                        cumulative_count = int(cumulative_match.group(1))
                        result[score_key] = cumulative_count
                        
            except (ValueError, IndexError) as e:
                # 跳过无法解析的行（如合计行、空行等）
                continue
        
        print(f"   ✅ {direction}: 提取到 {len(result)} 个分数点")
        return result
    
    def find_and_process_direction(self, direction_key: str, config: Dict) -> Optional[Dict[str, int]]:
        """
        查找并处理指定方向的数据
        
        Args:
            direction_key: 方向键名（如 vocal_2025）
            config: 方向配置
            
        Returns:
            位数字典，如果失败返回None
        """
        # 尝试所有可能的文件名
        for filename in config['files']:
            if os.path.exists(filename):
                rows = self.read_file(filename)
                if rows:
                    return self.parse_score_table(rows, direction_key)
        
        print(f"⚠️  未找到 {direction_key} 的数据文件")
        print(f"   期望的文件名:")
        for filename in config['files']:
            print(f"     - {filename}")
        return None
    
    def generate_compressed_ranks(self) -> Dict:
        """
        生成 compressed_ranks.json 数据
        
        Returns:
            完整的位数字典
        """
        print("\n" + "="*70)
        print("  开始生成 compressed_ranks.json")
        print("="*70)
        
        result = {}
        
        # 处理每个方向
        for direction_key, config in self.direction_config.items():
            rank_dict = self.find_and_process_direction(direction_key, config)
            
            if rank_dict:
                # 按分数降序排序（高分在前）
                sorted_dict = dict(
                    sorted(rank_dict.items(), key=lambda x: float(x[0]), reverse=True)
                )
                result[direction_key] = sorted_dict
        
        print(f"\n📦 最终数据结构:")
        for key, value in result.items():
            if value:
                scores = list(value.keys())
                print(f"   - {key}: {len(value)} 个分数点")
                print(f"     最高分: {scores[0]}")
                print(f"     最低分: {scores[-1]}")
            else:
                print(f"   - {key}: ❌ 无数据")
        
        return result
    
    def run(self):
        """执行完整的数据清洗流程"""
        print("\n" + "="*70)
        print("  山东省2025年音乐类综合成绩分段表清洗工具")
        print("  数据来源: https://www.sdzk.cn/NewsInfo.aspx?NewsID=6954")
        print("="*70)
        
        try:
            # 生成 compressed_ranks.json
            ranks_data = self.generate_compressed_ranks()
            
            if not ranks_data:
                print("\n❌ 错误: 没有成功提取任何数据！")
                print("💡 请确保已将Excel/CSV文件下载到当前目录")
                return
            
            # 保存到文件
            output_file = 'compressed_ranks.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(ranks_data, f, ensure_ascii=False, indent=2)
            
            file_size = os.path.getsize(output_file) / 1024
            print(f"\n✅ {output_file} 已生成 ({file_size:.2f} KB)")
            
            # 验证数据完整性
            missing_dirs = [key for key in self.direction_config.keys() if key not in ranks_data or not ranks_data[key]]
            if missing_dirs:
                print(f"\n⚠️  警告: 以下方向缺少数据:")
                for direction in missing_dirs:
                    print(f"   - {direction}")
                print(f"\n💡 请下载缺失的Excel/CSV文件后重新运行脚本")
            else:
                print(f"\n🎉 所有方向数据提取成功！")
            
            print("\n" + "="*70)
            print("  🎊 数据清洗完成！")
            print("="*70)
            
        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    cleaner = ComprehensiveScoreCleaner()
    cleaner.run()
