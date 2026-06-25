# 项目记忆 - 2026山东音乐类统考志愿填报

## 项目结构（清理后）
- `index.html`: 前端志愿填报界面
- `compressed_ranks.json`: 12个一分一段数据集
- `data.json`: 投档录取数据（1693条记录，347所院校）
- `plan_2026.json`: 2026招生计划（450条，242院校），由 `build_plan_from_excel.py` 生成
- `rebuild_all_data.py`: 统一生成 data.json + compressed_ranks.json
- `build_plan_from_excel.py`: 从Excel生成 plan_2026.json
- `downloads/`: 原始数据源（XLS一分一段+录取表，CSV专业成绩，Excel招生计划，PDF参考）

## 数据来源
- 9个2025年一分一段表XLS（downloads/子目录）
- 3个2026年专业成绩CSV
- 6个投档/录取XLS（downloads/根目录）
- **plan_2026.json**: 由 `build_plan_from_excel.py` 从 `downloads/2026音乐生院校招生计划表（不完整）.xlsx` 生成（784条→过滤非钢琴器乐后450条）
  - vocal: 114条, instrumental(仅钢琴): 71条, education: 265条
  - 总计划数: 3553人, 242所院校
  - 注意：PDF OCR提取的数据已废弃，改用人工整理的Excel

## 关键数据验证点（2025）
- 专业成绩最高: 声乐279, 器乐281, 音教276
- 综合成绩最高: 声乐629.59, 器乐644.96, 音教624.14（三者不同才是对的）
- 文化成绩最高: 均为604

## 前端关键逻辑
- **等位换算算法（专业分百分位映射 — 仅用真实数据）**：
  1. 计算 rawComp = culture×0.5 + pro×1.25（仅供对比参考）
  2. 在 `*_art_2026` 专业分段表中找到专业分排名 → 百分位
  3. 百分位映射到 `*_art_2025` 专业分段表同百分位 → 等位2025专业分 equivPro
  4. equivComp = culture×0.5 + equivPro×1.25
  5. 在 `*_2025` 综合分段表查等位综合分排名
  6. **注意**：暂无2026综合分段表（等真实数据），已删除卷积生成的假表
  7. `score_from_rank` 插值条件：`c1 <= rank <= c2`（累积从低到高方向）
- 冲稳保: 等位综合分-2025投档线 >15保、0~15稳、-5~0冲
- 按钮文字: "💫 心想事成"
- 三年数据对比: 2024/2025/2026 均已加载，但2024暂未接入等位换算链路
