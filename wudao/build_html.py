#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从音乐类 index.html 适配生成舞蹈类 wudao/index.html"""
import os, sys
if sys.platform == 'win32':
    import io; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'index.html')
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')

with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()

print(f'Source: {len(html)} chars from {SRC}')

# ====== 替换列表 ======
replacements = [
    # 标题
    ('2026年山东省音乐类智能志愿填报专家系统', '2026年山东省舞蹈类智能志愿填报专家系统'),
    # 面板标题
    ('🎵 音乐类智能志愿填报', '💃 舞蹈类智能志愿填报'),
    # 面板描述
    ('基于2026年最新投档计划数据 / 等位换算算法', '基于2026年最新投档计划数据 / 等位换算算法 | 舞蹈类'),
    # 输入标签
    ('🎹 音乐专业统考分数', '💃 舞蹈专业统考分数'),
    # 数据路径
    ('{ url: \'data.json\',', '{ url: \'./data.json\','),
    ('{ url: \'compressed_ranks.json\',', '{ url: \'./compressed_ranks.json\','),
    
    # 移除方向选择组
    ('<div class="input-group"><label for="directionSelect">🎯 专业方向</label>\n        <select id="directionSelect">\n            <option value="vocal">🎤 声乐</option>\n            <option value="instrumental">🎸 器乐</option>\n            <option value="education" selected>🏫 音乐教育</option>\n        </select>\n    </div>', ''),
    
    # 方向选择器引用
    ('directionSelect: gid(\'directionSelect\'), ', ''),
    ('const dir = E.directionSelect.value;', 'const dir = \'dance\';'),
    
    # 键盘事件中的方向选择
    ('E.directionSelect.value', "'dance'"),
    
    # direction 字段在 calcResult 中
    ('direction:dir', "direction:'dance'"),
    
    # getFilteredSchools 中 direction 过滤 (保持不变因为都是 'dance')
    
    # 导出文本
    ('2026年山东省音乐类志愿填报方案', '2026年山东省舞蹈类志愿填报方案'),
    ("const m={vocal:'声乐',instrumental:'器乐',education:'音乐教育'}", "const m={dance:'舞蹈类'}"),
    ("return m[state.calcResult.direction]||state.calcResult.direction", "return '舞蹈类'"),
    ("m[r.direction]||r.direction", "'舞蹈类'"),
    
    # 算法注释
    ('// STEP 3: 专业排名（保留，仅用于展示参考）', '// STEP 3: 专业排名（保留，仅用于展示参考）'),
    
    # 文化课分段表可能缺失，添加防护（已存在if(cult2025)检查）
    
    # ===== 添加导航链接 =====
    # 在 panel-header 后面添加导航
    ('<div class="panel-header">',
     '<div class="panel-header">\n        <div style="margin-bottom:12px;display:flex;gap:8px;justify-content:center">'
     '<a href="../index.html" style="font-size:0.85rem;color:#6B7280;text-decoration:none;padding:4px 12px;border:1px solid #E5E7EB;border-radius:20px;transition:all 0.2s">🎵 音乐类</a>'
     '<span style="font-size:0.85rem;color:#fff;background:linear-gradient(135deg,#EC4899,#F43F5E);padding:4px 16px;border-radius:20px;font-weight:700">💃 舞蹈类</span>'
     '</div>'),
]

for old, new in replacements:
    if old in html:
        html = html.replace(old, new)
        print(f'  ✅ replaced: {old[:50]}...')
    else:
        print(f'  ⚠️ NOT FOUND: {old[:50]}...')

# ===== 额外替换: 移除 input-group 后的空行 =====
import re
html = re.sub(r'<div class="input-group">(\s*)</div>', '', html)

with open(DST, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\nSaved: {DST} ({len(html)} chars)')
print('DONE!')
