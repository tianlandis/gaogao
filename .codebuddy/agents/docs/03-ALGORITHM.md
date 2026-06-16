# 03 — 核心算法

> 触发条件：修改计算逻辑、调试分数结果、调整梯度阈值时必读。
> ⚠️ 这是"数学公式"级文档，算法的数学逻辑不可修改。

---

## 3.1 等位分标准化（4步流程）⭐ 核心

```
输入：文化分(culture) + 专业分(pro) + 方向(dir)

STEP 1 — 原始综合分
  rawComp = culture × 0.5 + pro × 2.5 × 0.5
  （满分750，综合分公式假定不变）

STEP 2 — 2026专业位次
  从 rankData[dir + '_art_2026'] 查2026专业一分一段表
  artRank = rankFromDict(art2026, pro)
  → 得到该专业分对应的2026全省累计位次

STEP 3 — 等位专业分换算（位次→2025分数）
  从 rankData[dir + '_art_2025'] 查2025专业一分一段表
  equivPro = scoreFromRank(art2025, artRank)
  → 用2026的位次反查2025年该位次对应的分数

STEP 4 — 等位综合分 & 综合位次
  equivComp = culture × 0.5 + equivPro × 2.5 × 0.5
  从 rankData[dir + '_2025'] 查2025综合分一分一段表
  compRank = rankFromDict(comp2025, equivComp)
```

### 设计原理

每年考题难度不同，直接比原始分无意义。
通过"**位次**"这个跨年不变量，将2026专业分映射到2025分数刻度上，
使考生的等位综合分可以直接与2025投档线公平比较。

### 降级策略

如果缺少 `dir + '_art_2026'` 数据：
→ 直接使用 `dir + '_art_2025'` 查位次（跳过等位换算）

如果缺少 `dir + '_art_2025'` 数据：
→ equivPro = pro（跳过等位换算，直接使用原始分）

---

## 3.2 插值算法

### rankFromDict(dict, score) — 分数→位次

```
1. 将 dict 按 score 降序排列
2. 二分查找 score 所处区间
3. 线性插值：rank = dict[s1] + (dict[s2]-dict[s1]) × (score-s1)/(s2-s1)
   （s1 ≤ score < s2, s1和s2为相邻分数）
```

### scoreFromRank(dict, rank) — 位次→分数

```
1. 将 dict 按 score 降序排列
2. 二分查找 rank 所处区间
3. 线性插值：score = s1 + (s2-s1) × (rank-dict[s1])/(dict[s2]-dict[s1])
```

---

## 3.3 梯度计算（冲/稳/保）

```
输入：等位综合分(comprehensive) + 学校投档线(school.line)
diff = comprehensive - school.line

if diff > 15:  → "保" (bao) — 超过投档线15分以上
if diff >= 0:  → "稳" (wen) — 达线，差距在0~15分
if diff >= -5: → "冲" (chong) — 低于线但差距≤5分
otherwise:     → 不显示（差距超过5分，不建议报考）
```

### 对应 CSS 类名

| 梯度 | CSS类 | 标签 |
|------|-------|------|
| 保 | `tag-bao` | 绿色 `保` |
| 稳 | `tag-wen` | 蓝色 `稳` |
| 冲 | `tag-chong` | 橙色 `冲` |

---

## 3.4 文化课超越率

```
cultureRank = rankFromDict(cultureDict, culture分)
  → 从 dir + '_culture_2025' 字典查位次

cultureTotal = max(所有累计人数)
  → 双达线考生总数

culturePct = (1 - cultureRank / cultureTotal) × 100
  → 百分比，含义：文化分超过了百分之多少的双达线考生
```

### 无数据降级

如果 `dir + '_culture_2025'` 不存在：
→ culturePct = 0, cultureRank = null, cultureTotal = 0
→ 前端显示 "0.0%" 和 "--"

---

## 3.5 算法在 index.html 中的位置

所有算法实现在 `index.html` 的 `<script>` 标签内：

| 函数 | 对应算法 | 行范围（参考） |
|------|----------|---------------|
| `handleCalculate()` | 4步流程入口 | ~第440行 |
| `rankFromDict()` | 分数→位次插值 | ~第380行 |
| `scoreFromRank()` | 位次→分数插值 | 同上区域 |
| `getFilteredSchools()` | 筛选+梯度计算 | ~第470行 |
| `renderSchoolList()` | 梯度分类展示 | ~第490行 |
