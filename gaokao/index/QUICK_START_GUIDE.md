# 🚀 智能爬虫合并脚本 - 快速启动指南

## ✅ 已完成文件

1. **smart_crawler_and_merger.py** (729行) - 核心脚本
2. **SMART_CRAWLER_MERGER_README.md** (466行) - 详细使用说明
3. **test_smart_crawler.py** (155行) - 功能测试脚本

---

## 📋 三步快速开始

### 第一步：安装依赖（仅第一次）

```bash
pip install pandas openpyxl xlrd requests
```

或使用批处理文件：
```bash
install_dependencies.bat
```

---

### 第二步：准备数据文件

#### **方式A：自动下载（推荐）**
```bash
python smart_crawler_and_merger.py --download
```

脚本会自动从官网下载所有6个Excel文件到 `downloads` 目录。

#### **方式B：手动下载**
1. 访问以下5个官方链接，下载对应的Excel文件：
   - https://www.sdzk.cn/NewsInfo.aspx?NewsID=6986 (2个文件)
   - https://www.sdzk.cn/NewsInfo.aspx?NewsID=6989
   - https://www.sdzk.cn/NewsInfo.aspx?NewsID=7001
   - https://www.sdzk.cn/NewsInfo.aspx?NewsID=7009
   - https://www.sdzk.cn/NewsInfo.aspx?NewsID=7018

2. 将下载的Excel文件放入当前目录或 `downloads` 子目录

3. 运行脚本：
```bash
python smart_crawler_and_merger.py
```

---

### 第三步：查看结果

脚本执行完成后会生成：
- **data.json** - 包含所有学校投档数据的JSON文件

控制台会显示详细的统计报告：
```
📊 数据处理完成！共收集 XXX 条记录
🔄 去重后: XXX 条

📋 各批次记录数:
   • 本科批第1次投档: XXX 条
   • ...

🎵 各方向记录数:
   • 声乐: XXX 条
   • 器乐: XXX 条
   • 音教: XXX 条

📊 投档线范围:
   • 最高分: XXX.XX
   • 最低分: XXX.XX
   • 平均分: XXX.XX
```

---

## 🧪 测试核心功能

运行测试脚本验证各项功能是否正常：

```bash
python test_smart_crawler.py
```

测试内容包括：
- ✅ 院校字典匹配
- ✅ 省份智能推断
- ✅ 公办/民办性质推断
- ✅ 音乐方向自动分类
- ✅ 院校代码提取

---

## 📖 核心功能说明

### 1. 高精度院校字典（150+所高校）

```python
UNIVERSITY_DB = {
    "A027": {"province": "北京", "nature": "公办", "level": "本科"},  # 北京师范大学
    "E438": {"province": "山东", "nature": "公办", "level": "本科"},  # 山东管理学院
    "A047": {"province": "北京", "nature": "公办", "level": "本科"},  # 中央音乐学院
    # ... 更多高校
}
```

### 2. 智能启发式规则（Fallback）

如果字典未命中，通过校名关键词自动判断：

**省份判定**：
- "山东师范大学" → 匹配"山东" → `province: "山东"`
- "青岛大学" → 匹配"青岛" → `province: "山东"`
- "未知学院" → 无匹配 → `province: "其它省份"`

**性质判定**：
- "山东协和学院" → 匹配"协和" → `nature: "民办"`
- "山东师范大学" → 无匹配 → `nature: "公办"`（默认）

### 3. 音乐方向自动分类

```python
"音乐学(声乐)" → direction: "vocal"
"音乐表演(钢琴)" → direction: "instrumental"
"音乐教育" → direction: "education"
```

### 4. 批次标签自动灌入

| 文件来源 | batch | level |
|---------|-------|-------|
| NewsID=6986 | 本科批第1次投档 | 本科 |
| NewsID=6989 | 本科批第1次录取 | 本科 |
| NewsID=7001 | 本科批第2次投档 | 本科 |
| NewsID=7009 | 专科批第1次投档 | 专科 |
| NewsID=7018 | 专科批第2次投档 | 专科 |

---

## 📊 输出数据结构

```json
{
  "schools": [
    {
      "id": "A027_1D_本科批第1次投档_2025",
      "code": "A027",
      "name": "北京师范大学",
      "major_code": "1D",
      "major": "音乐学(声乐)",
      "direction": "vocal",
      "province": "北京",
      "level": "本科",
      "nature": "公办",
      "batch": "本科批第1次投档",
      "line": 620.13,
      "plan": 2
    }
  ]
}
```

---

## ⚠️ 常见问题

### Q1: 提示"未安装 requests/pandas 库"
```bash
pip install pandas openpyxl xlrd requests
```

### Q2: 下载文件失败
手动从官网下载Excel文件，放入当前目录或 `downloads` 目录，然后运行：
```bash
python smart_crawler_and_merger.py
```

### Q3: 某些学校信息不准确
打开 `smart_crawler_and_merger.py`，在 `UNIVERSITY_DB` 字典中添加该校的准确信息。

---

## 🎯 下一步

1. ✅ 运行脚本生成 `data.json`
2. ✅ 在前端 `index.html` 中加载该数据
3. ✅ 测试志愿填报推荐功能
4. ✅ 根据实际数据调整前端展示逻辑

---

## 📞 技术支持

如有问题，请查看：
- **详细文档**: `SMART_CRAWLER_MERGER_README.md`
- **测试脚本**: `test_smart_crawler.py`

祝使用愉快！🎉
