# 07 — 修改强制规则

> 触发条件：修改任何代码前必读。这是"法律"级文档。

---

## 7.1 八条强制规则

| # | 规则 | 严重级别 |
|---|------|----------|
| 1 | **禁止删除或修改 `compressed_ranks.json` 和 `data.json` 的顶级键名结构** | 🔴 致命 |
| 2 | **禁止修改 `index.html` 中的 4 步等位分算法** | 🔴 致命 |
| 3 | **禁止修改梯度三档阈值（>15, ≥0, ≥-5）而不更新 `03-ALGORITHM.md`** | 🔴 致命 |
| 4 | **禁止在 `index.html` 中硬编码数据**，所有数据必须从 JSON 加载 | 🟠 严重 |
| 5 | **禁止删除 Python 清洗脚本**，它们是数据再生的唯一途径 | 🟠 严重 |
| 6 | **所有筛选/渲染函数必须 try-catch 包裹** | 🟡 重要 |
| 7 | **新增 `state.rankData` 键名必须遵循 `{方向}_{类型}_{年份}` 命名规则** | 🟡 重要 |
| 8 | **修改 `data.json` 结构后必须同步更新 `index.html` 中的渲染和导出代码** | 🟡 重要 |

---

## 7.2 修改前的标准流程

```
1. 查看 gao.md 文档索引 → 确定需要读哪些领域文档
2. 读取对应的领域文档 → 理解约束和规范
3. 修改代码
4. 运行测试（至少：node serve.js → 浏览器验证）
5. 如有架构变化 → 更新对应的领域文档
6. 在 08-CHANGELOG.md 中记录变更
```

---

## 7.3 运行清单

### 首次部署

```bash
# 1. 安装 Python 依赖
pip install pandas openpyxl xlrd

# 2. 生成数据（如已修改数据源）
python build_real_data.py

# 3. 启动服务
node serve.js

# 4. 访问
# http://localhost:8080
```

### 日常启动

```bash
node serve.js
```

### 数据更新后

```bash
python build_real_data.py   # 重新生成 JSON
# 然后重启 serve.js
```

---

## 7.4 禁止的操作清单

- ❌ 手动编辑 `data.json` 中的学校数据
- ❌ 手动编辑 `compressed_ranks.json` 中的位次数据
- ❌ 在 `index.html` 中写死学校列表
- ❌ 直接修改 `serve.js` 端口而不更新文档
- ❌ 删除 `downloads/` 目录中的原始 XLS 文件
- ❌ 跳过 try-catch 直接操作 DOM
- ❌ 在无 `state.calcResult` 时调用 `renderSchoolList()`
