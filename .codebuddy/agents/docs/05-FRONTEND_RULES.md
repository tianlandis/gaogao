# 05 — 前端交互规范

> 触发条件：修改 index.html 中任何 UI/交互/渲染代码时必读。
> ⚠️ 违反本规范是 V0.1 已修复 BUG 的主要来源。

---

## 5.1 状态机

```
┌──────────┐   点击"开始预测"   ┌──────────────┐   操作筛选    ┌──────────────┐
│  初始态   │ ─────────────────→ │  计算展示态   │ ────────────→ │  筛选展示态   │
│ (无结果)  │                    │ (有结果)      │              │ (过滤结果)   │
└──────────┘                    └──────────────┘              └──────────────┘
                                       │                            │
                                       │    再次点击"开始预测"        │
                                       │    (重置筛选，重新计算)      │
                                       └────────────────────────────┘
```

**关键约束**：
- 初始态：`state.calcResult === null`，筛选栏隐藏，筛选操作不触发渲染
- 计算展示态：`state.calcResult` 有值，筛选操作可触发渲染
- 进入计算态时：**必须重置所有筛选条件为默认值**

---

## 5.2 筛选防御规则

### applyFilters() 入口守卫（必须）

```javascript
function applyFilters() {
    if (!state.calcResult) return;  // ← 这行不可删除！无结果时不渲染
    // ... 后续逻辑
}
```

### handleCalculate() 中重置筛选

```javascript
// 每次新查询必须重置：
state.filters = { provinces: [], nature: '', level: '', batch: '', gradient: '' };
if (E.natureSelect) E.natureSelect.value = '';
if (E.levelSelect) E.levelSelect.value = '';
if (E.batchSelect) E.batchSelect.value = '';
updateProvinceCheckboxes();  // 重置省份复选框
```

### 省份筛选逻辑

- `state.filters.provinces` 是**排除列表**（空数组 = 全选）
- 取消勾选某省份 → 将该省加入 `provinces`（排除）
- 重新勾选 → 从 `provinces` 移除
- `getFilteredSchools()` 中：`if(exp.size>0) f = f.filter(s=>!exp.has(s.province))`

---

## 5.3 渲染防御规则

### 所有渲染函数必须 try-catch

```javascript
function renderSchoolList(result) {
    try {
        // ... 渲染逻辑
    } catch(e) {
        console.error('❌ 渲染失败:', e);
    }
}
```

### 所有 DOM 操作前 null 检查

```javascript
if (E.schoolCount) E.schoolCount.textContent = display.length + ' 所';
if (E.exportBar) E.exportBar.classList.add('visible');
if (E.schoolList) E.schoolList.innerHTML = html;
```

### E 对象（元素引用）

所有 DOM 元素通过 `gid(id)` 函数获取，存储在 `E` 对象中。
`gid()` 等于 `document.getElementById()`，可能返回 `null`。

---

## 5.4 响应式布局规则

| 场景 | 条件 | 布局 |
|------|------|------|
| 默认（横屏） | width > 768px 且 height > width | 左右分栏：380px 输入 + flex 结果 |
| 竖屏/移动端 | width ≤ 768px 或 height > width | 上下布局：输入在上，结果在下 |
| 竖屏学校卡片 | 同上 | 横向滑动（overflow-x: auto） |

### 竖屏计算后自动滚动

```javascript
if (window.innerWidth <= 768 || window.innerHeight > window.innerWidth) {
    setTimeout(() => {
        const a = gid('resultPanelAnchor');
        if (a) a.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 150);
}
```

---

## 5.5 导出按钮

- 初始隐藏（`display: none`），第一次计算后显示（`classList.add('visible')`）
- 点击导出 → `exportCSV()` → 下载 `志愿推荐.csv`
- 导出数据来源：`state.currentDisplay`（当前筛选后显示的结果）

---

## 5.6 按钮规范

- 所有 `<button>` 必须加 `type="button"`，防止触发表单提交刷新页面
- 计算按钮 id：`btnCalculate`

---

## 5.7 V0.2 代码预留点（不要破坏）

```
1. handleCalculate() 中的年份键名拼接
   当前: rankData[dir + '_art_' + year]  ← year 硬编码
   升级: 让 year 成为变量，支持双年切换

2. renderSchoolList() 中的梯度计算
   当前: diff = result.comprehensive - school.line
   升级: diff = result.comprehensive - predictLine(school)

3. data.json school 对象
   V0.2 可能新增: remark(string), line_2026(number), 录取最低分(number)
```
