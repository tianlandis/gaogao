#!/usr/bin/env python3
"""
蒙特卡洛回测验证：用 2025 年真实数据检验"专业分与文化分独立分布"假设

验证结论 (2026-06-26):
  平均绝对差 4.1 分 (声乐 2.4 / 器乐 5.5 / 音教 4.3)
  KS 距离 15.4 分
  系统性偏差: 高分端偏低，低分端偏高 (说明专业分与文化分正相关)
  结论: 蒙特卡洛路径不可用于生产，保持当前专业分百分位映射算法，
        等 2026 综合分段表来了直接切过去。

方法：
1. 展开 2025 年专业分段表、文化分段表 → 各自 5524 个分值
2. 随机打乱后配对 → 计算模拟综合分 → 构建模拟综合分段表
3. 与真实 2025 综合分段表对比（逐百分点 + KS 距离）
4. 跑 5 个随机种子看稳定性

如果模拟表与真实表接近 → 独立分布假设成立，蒙特卡洛可用于 2026
如果模拟表与真实表差距大 → 独立分布不成立，蒙特卡洛路径不可行
"""

import json
import random
import sys
import io
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ========== 1. 加载数据 ==========
with open('e:/gaogao/compressed_ranks.json', 'r', encoding='utf-8') as f:
    ranks = json.load(f)

DIRECTIONS = [
    ('vocal', '声乐'),
    ('instrumental', '器乐'),
    ('education', '音乐教育'),
]


def expand_ranks(table: dict) -> list:
    """
    展开分段表为个体分值列表。
    table 格式: {score_str: cumulative_count}
    cumulative_count = 达到此分及以上的人数（高分→1，低分→总人数）
    某分数段的人数 = 该分累积 - 下一个更高分的累积
    """
    # 按分数升序排列
    sorted_items = sorted(table.items(), key=lambda x: float(x[0]))
    expanded = []

    for i, (score_str, cum) in enumerate(sorted_items):
        score = float(score_str)
        # 下一个更高分数的累积人数
        next_cum = sorted_items[i + 1][1] if i + 1 < len(sorted_items) else 0
        count_at_this_score = cum - next_cum
        if count_at_this_score > 0:
            expanded.extend([score] * count_at_this_score)

    return expanded


def build_cumulative_table(scores: list) -> dict:
    """从个体分值列表构建分段表（高分→1，低分→总人数）"""
    scores_sorted = sorted(scores, reverse=True)
    table = {}
    for i, s in enumerate(scores_sorted):
        # 用字符串做键，和 compressed_ranks.json 一致
        key = f"{s:.2f}"  # 综合分用两位小数
        if key not in table:
            table[key] = i + 1
    return table


def percentile_from_table(table: dict, pct: float) -> float:
    """
    从分段表取第 pct 百分位的分数。
    table: {score_str: cumulative_count}, 累积=从高分往下数的人数
    累积大 ← 低分低累积 ← 中 → 高累积低分 → 累积小
    所以从高分→低分遍历，cum 从小变大
    pct=50 时取中位数：找到 cum >= 50%总人数 的最低分（或说是最高分的边界）
    """
    total = max(table.values())
    target_rank = max(1, min(total, int(total * pct / 100.0 + 0.5)))
    # 按分数从高到低排：最高分(cum=1) → 最低分(cum=total)
    items = sorted(table.items(), key=lambda x: float(x[0]), reverse=True)
    for score_str, cum in items:
        if cum >= target_rank:
            return float(score_str)
    return float(items[-1][0])


def compare_tables(real: dict, sim: dict, name: str) -> dict:
    """对比真实表和模拟表，返回各项指标"""
    total = max(real.values())
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    diffs = []

    print(f"\n  {'百分位':<8} {'真实分':>10} {'模拟分':>10} {'差值':>10}")
    print(f"  {'-'*8} {'-'*10} {'-'*10} {'-'*10}")

    for p in percentiles:
        r = percentile_from_table(real, p)
        s = percentile_from_table(sim, p)
        d = s - r
        diffs.append(d)
        print(f"  P{p:<7} {r:>10.2f} {s:>10.2f} {d:>+10.2f}")

    # KS 距离：取所有百分位的最大绝对差值
    ks = max(abs(d) for d in diffs)

    # 平均绝对差值
    mad = sum(abs(d) for d in diffs) / len(diffs)

    return {
        'name': name,
        'total': total,
        'diffs': diffs,
        'ks': ks,
        'mad': mad,
        'percentile_diffs': dict(zip(percentiles, diffs)),
    }


def run_simulation(direction: str, name_cn: str, seed: int) -> dict:
    """运行一次蒙特卡洛模拟"""
    art_2025 = ranks[f'{direction}_art_2025']
    culture_2025 = ranks[f'{direction}_culture_2025']
    real_2025 = ranks[f'{direction}_2025']

    # 展开为个体分值列表
    art_scores = expand_ranks(art_2025)
    culture_scores = expand_ranks(culture_2025)

    assert len(art_scores) == len(culture_scores), \
        f"{name_cn}: 专业{len(art_scores)}人 ≠ 文化{len(culture_scores)}人"

    n = len(art_scores)

    # 随机打乱两个列表（模拟独立分布）
    rng = random.Random(seed)
    rng.shuffle(art_scores)
    rng.shuffle(culture_scores)

    # 计算模拟综合分
    sim_comp = [
        c * 0.5 + a * 1.25
        for a, c in zip(art_scores, culture_scores)
    ]

    # 构建模拟综合分段表
    sim_table = build_cumulative_table(sim_comp)

    # 对比
    result = compare_tables(real_2025, sim_table, f"{name_cn} (seed={seed})")
    result['direction'] = direction
    result['n_people'] = n
    result['seed'] = seed
    return result


# ========== 2. 主验证流程 ==========
print("=" * 70)
print("蒙特卡洛回测验证：独立分布假设检验")
print("=" * 70)
print()
print("原理：如果专业分和文化分真的独立，随机配对后算出的")
print("综合分分布应该接近真实综合分分布。")
print()

SEEDS = [42, 123, 456, 789, 2025]
all_results = []

for direction, name_cn in DIRECTIONS:
    print(f"\n{'#'*70}")
    print(f"# {name_cn}方向")
    print(f"{'#'*70}")

    dir_results = []
    for seed in SEEDS:
        print(f"\n  --- seed={seed} ---")
        r = run_simulation(direction, name_cn, seed)
        dir_results.append(r)
        print(f"  KS距离={r['ks']:.4f}  平均绝对差值={r['mad']:.4f}")

    # 汇总该方向的多次运行
    ks_values = [r['ks'] for r in dir_results]
    mad_values = [r['mad'] for r in dir_results]
    print(f"\n  ▶ {name_cn} 汇总 (5次运行):")
    print(f"    KS距离: 最小={min(ks_values):.4f}  最大={max(ks_values):.4f}  平均={sum(ks_values)/len(ks_values):.4f}")
    print(f"    平均绝对差值: 最小={min(mad_values):.4f}  最大={max(mad_values):.4f}  平均={sum(mad_values)/len(mad_values):.4f}")

    all_results.extend(dir_results)


# ========== 3. 综合判断 ==========
print("\n" + "=" * 70)
print("总结")
print("=" * 70)

for direction, name_cn in DIRECTIONS:
    dir_ks = [r['ks'] for r in all_results if r['direction'] == direction]
    dir_mad = [r['mad'] for r in all_results if r['direction'] == direction]
    avg_ks = sum(dir_ks) / len(dir_ks)
    avg_mad = sum(dir_mad) / len(dir_mad)
    print(f"  {name_cn}: 平均KS={avg_ks:.4f}, 平均绝对差={avg_mad:.4f}")

overall_ks = sum(r['ks'] for r in all_results) / len(all_results)
overall_mad = sum(r['mad'] for r in all_results) / len(all_results)
print(f"\n  总平均 KS距离 = {overall_ks:.4f}")
print(f"  总平均 绝对差值 = {overall_mad:.4f}")

print()
if overall_mad < 3:
    print("  ✅ 结论：独立分布假设基本成立，蒙特卡洛方法可用于 2026")
elif overall_mad < 8:
    print("  ⚠️  结论：独立分布有偏差但可接受，蒙特卡洛方法需谨慎使用")
else:
    print("  ❌ 结论：独立分布假设不成立，蒙特卡洛路径不可行")
    print("     专业分和文化分存在显著相关性，不能简单随机配对")


# ========== 4. 额外：算一下真实专业分和文化分的相关系数 ==========
print("\n" + "=" * 70)
print("补充：真实数据中专业分与文化分的相关性 (按分数段配对)")
print("=" * 70)
print("(注：我们不知道个体的真实配对，只能按相同百分位配对作为近似)")

for direction, name_cn in DIRECTIONS:
    art_2025 = ranks[f'{direction}_art_2025']
    culture_2025 = ranks[f'{direction}_culture_2025']
    art_scores = expand_ranks(art_2025)
    culture_scores = expand_ranks(culture_2025)
    
    n = len(art_scores)
    # 按百分位配对（假设两者排位相同的人就是同一个人——最理想的情况）
    art_sorted = sorted(art_scores)
    culture_sorted = sorted(culture_scores)
    
    # 皮尔逊相关系数
    mean_a = sum(art_sorted) / n
    mean_c = sum(culture_sorted) / n
    cov = sum((a - mean_a) * (c - mean_c) for a, c in zip(art_sorted, culture_sorted)) / n
    std_a = (sum((a - mean_a)**2 for a in art_sorted) / n) ** 0.5
    std_c = (sum((c - mean_c)**2 for c in culture_sorted) / n) ** 0.5
    r = cov / (std_a * std_c) if std_a > 0 and std_c > 0 else 0
    
    print(f"  {name_cn}: 如果按同百分位配对，相关系数 r = {r:.4f}")
    print(f"    专业均分={mean_a:.1f}±{std_a:.1f}, 文化均分={mean_c:.1f}±{std_c:.1f}")

print()
print("(说明：真实的个体配对是未知的，这个r只是按百分位匹配的近似)")
