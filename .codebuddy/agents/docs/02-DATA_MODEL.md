# 02 — 数据模型定义

> 触发条件：修改 JSON 结构、新增字段、修改数据处理脚本、调试数据问题时必读。
> ⚠️ 这是"数据库 schema"级文档，所有数据操作以此为唯一标准。

---

## 2.1 data.json — 院校投档数据

```json
{
  "schools": [
    {
      "id": "A027_1D_本科批第1次投档_2025",
      "code": "A027",           // 院校代码（必须非空，4位字母数字）
      "name": "北京师范大学",    // 院校名称（必须非空）
      "major_code": "1D",        // 专业代码（必须非空）
      "major": "音乐学(声乐)",   // 专业名称（必须非空）
      "direction": "vocal",      // 方向：vocal|instrumental|education
      "province": "北京",        // 省份（必须非空）
      "level": "本科",           // 层次：本科|专科
      "nature": "公办",          // 性质：公办|民办
      "batch": "本科批第1次投档",// 批次
      "line": 620.13,            // 投档最低分（必须为number）
      "plan": 2                  // 招生计划数（必须为number）
    }
  ]
}
```

### 字段约束

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `id` | string | ✅ | `{code}_{major_code}_{batch}_{year}` |
| `code` | string | ✅ | 4位字母数字 |
| `name` | string | ✅ | 非空 |
| `major_code` | string | ✅ | 非空 |
| `major` | string | ✅ | 非空 |
| `direction` | string | ✅ | 枚举：`vocal` / `instrumental` / `education` |
| `province` | string | ✅ | 非空 |
| `level` | string | ✅ | 枚举：`本科` / `专科` |
| `nature` | string | ✅ | 枚举：`公办` / `民办` |
| `batch` | string | ✅ | 见批次列表 |
| `line` | number | ✅ | 数字，可为浮点数 |
| `plan` | number | ✅ | 整数 |

### 批次枚举（排序顺序）

```
本科批第1次投档 > 本科批第1次录取 > 本科批第2次投档 > 专科批第1次投档 > 专科批第2次投档
```

---

## 2.2 compressed_ranks.json — 位次字典

```json
{
  "vocal_art_2026":       { "178": 8358, "180": 8297, ... },
  "vocal_art_2025":       { "190": 5000, "188": 5200, ... },
  "vocal_2025":           { "620.50": 1, "615.00": 5, ... },
  "vocal_culture_2025":   { "604": 1, "589": 2, ... },
  "instrumental_art_2026": { ... },
  "instrumental_art_2025": { ... },
  "instrumental_2025":     { ... },
  "instrumental_culture_2025": { ... },
  "education_art_2026":   { ... },
  "education_art_2025":   { ... },
  "education_2025":       { ... },
  "education_culture_2025": { ... }
}
```

### 键名命名规则（严格）

```
{方向}_{数据类}_{年份}
```

| 部分 | 可选值 | 说明 |
|------|--------|------|
| 方向 | `vocal` / `instrumental` / `education` | 音乐类三个方向 |
| 数据类 | `art`（专业分） / `culture`（文化分） / 无后缀（综合分） | |
| 年份 | `2025` / `2026` | 当前 V0.1 只有 2025 + art_2026 |

### 键值约束

- 键：分数（string），按分数**降序**排列
- 值：累计人数（integer），同分累计
- 专业分：每 2 分采样（压缩）
- 文化分：每 5 分采样（压缩）
- 综合分：全部保留（不压缩）

---

## 2.3 前端 state 对象（index.html）

```javascript
state = {
    schools: [],       // data.json 全量学校 → init() 时 fetch 加载
    rankData: {},      // compressed_ranks.json → init() 时 fetch 加载
    calcResult: null,  // 计算结果 → handleCalculate() 后赋值
    filters: {         // 筛选条件
        provinces: [], // 排除的省份列表（空数组 = 全选）
        nature: '',    // ''|'公办'|'民办'
        level: '',     // ''|'本科'|'专科'
        batch: '',     // ''|具体批次名
        gradient: ''   // ''|'bao'|'wen'|'chong'
    },
    allProvinces: [],  // 全部省份列表（去重，从 schools 派生）
    currentDisplay: [] // 当前显示的学校列表 → 导出功能使用
}
```

### calcResult 对象结构

```javascript
{
    rawComp: number,           // 原始综合分
    comprehensive: number,     // 等位综合分（核心）
    comprehensiveRank: number, // 综合位次
    musicScore: number,        // 原始专业分
    equivalentProf2025: number,// 等位专业分（2025刻度）
    pureArtRank: number,       // 2026专业位次
    culturePct: number,        // 文化超越率（百分比）
    cultureRank: number,       // 文化位次
    cultureTotal: number,      // 文化总人数
    direction: string          // vocal|instrumental|education
}
```
