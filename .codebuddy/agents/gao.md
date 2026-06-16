---
name: gao
description: 2026山东音乐类统考志愿填报 — 数据清洗、标签富化、前端交互
model: deepseek-v4-pro
tools: list_dir, search_file, search_content, read_file, read_lints, replace_in_file, write_to_file, execute_command, delete_file, preview_url, web_fetch, use_skill, web_search
agentMode: agentic
enabled: true
enabledAutoRun: true
---

# 山东音乐类志愿填报系统 · 宪法入口 V0.1

> ⚠️ 本文档是项目"宪法"。所有改动必须遵守以下原则。
> 详细规范见 `docs/` 目录下各领域文档——**按任务类型按需读取，不要全部加载**。

---

## 五条核心原则（不可违反）

1. **数据只读** — `data.json` 和 `compressed_ranks.json` 只能由 Python 脚本生成，禁止手动编辑或代码内硬编码
2. **算法不变** — 等位分 4 步换算流程（见 `docs/03-ALGORITHM.md`）不可修改其数学逻辑
3. **防御编程** — 所有 DOM 操作前必须 null 检查；所有渲染函数必须 try-catch
4. **状态驱动** — 筛选必须在 `state.calcResult` 存在后才生效，无结果时 `applyFilters()` 直接 return
5. **版本隔离** — 2025 数据为 V0.1 基准，2026 数据为 V0.2 增量，不覆盖历史数据

---

## 文档索引（按需读取）

| 任务类型 | 必读文档 | 选读文档 |
|---------|---------|---------|
| 修改前端 UI/交互 | `05-FRONTEND_RULES.md` | `01-ARCHITECTURE.md` |
| 修改计算逻辑/算法 | `03-ALGORITHM.md` → `02-DATA_MODEL.md` | `05-FRONTEND_RULES.md` |
| 修改数据模型/JSON结构 | `02-DATA_MODEL.md` → `04-DATA_INGEST.md` | `07-CODING_RULES.md` |
| 处理原始数据/运行脚本 | `04-DATA_INGEST.md` | `02-DATA_MODEL.md` |
| 规划新功能/版本升级 | `06-VERSION_PLAN.md` | `01-ARCHITECTURE.md` |
| 首次接触项目 | `01-ARCHITECTURE.md` → `02-DATA_MODEL.md` → `03-ALGORITHM.md` | — |
| 修 Bug | `05-FRONTEND_RULES.md` | `08-CHANGELOG.md` |
| 不确定该读什么 | **先读本文件**，再根据任务匹配上表 | — |

---

## 文档目录结构

```
.codebuddy/agents/
├── gao.md                    # 🔴 本文件 — 宪法入口
└── docs/
    ├── 01-ARCHITECTURE.md    # 项目定位、文件架构、部署方式
    ├── 02-DATA_MODEL.md      # data.json / compressed_ranks.json / state 结构
    ├── 03-ALGORITHM.md       # 等位分4步、插值、梯度、文化超越率
    ├── 04-DATA_INGEST.md     # Python脚本、XLS解析规则、标签富化
    ├── 05-FRONTEND_RULES.md  # 状态机、筛选渲染防御、响应式、代码预留点
    ├── 06-VERSION_PLAN.md    # V0.2 数据需求、架构扩展、功能规划
    ├── 07-CODING_RULES.md    # 8条强制规则 + 运行清单
    └── 08-CHANGELOG.md       # 变更历史、已知BUG、待办事项
```

---

## 快速参考

| 项目 | 值 |
|------|-----|
| 启动命令 | `node serve.js` |
| 访问地址 | `http://localhost:8080` |
| 生成数据 | `python build_real_data.py` |
| 目标用户 | 2026年山东音乐类统考考生 |
| 综合分公式 | 文化×0.5 + 专业×2.5×0.5 |
| 梯度阈值 | 保>15 / 稳≥0 / 冲≥-5 |
