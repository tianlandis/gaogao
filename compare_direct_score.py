#!/usr/bin/env python3
"""对比"百分位映射"和"直接用原始综合分"两种方案"""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('e:/gaogao/compressed_ranks.json', 'r', encoding='utf-8') as f:
    ranks = json.load(f)

culture = 430
pro = 232
raw_comp = culture * 0.5 + pro * 1.25  # = 505

print('=' * 60)
print(f'用户: 专业={pro}  文化={culture}  -> 原始综合分 = {raw_comp}')
print('=' * 60)

def rank_from_score(table, score):
    total = max(table.values())
    items = sorted(table.items(), key=lambda x: float(x[0]), reverse=True)
    for s, cum in items:
        if float(s) <= score:
            return cum, total
    return 1, total

def score_from_rank(table, target_rank):
    """从高分往低分找，cum从小变大，返回第一个 cum >= target_rank 的分数"""
    items = sorted(table.items(), key=lambda x: float(x[0]), reverse=True)
    for s, cum in items:
        if cum >= target_rank:
            return float(s)
    return float(items[-1][0])

for dir_key, name in [('vocal', '声乐'), ('instrumental', '器乐'), ('education', '音乐教育')]:
    print()
    print('--- ' + name + '方向 ---')
    
    art_2026 = ranks[dir_key + '_art_2026']
    art_2025 = ranks[dir_key + '_art_2025']
    comp_2025 = ranks[dir_key + '_2025']
    
    art_total_2026 = max(art_2026.values())
    art_total_2025 = max(art_2025.values())
    comp_total_2025 = max(comp_2025.values())
    
    # ===== 方案A: 百分位映射 =====
    art_rank_2026, _ = rank_from_score(art_2026, pro)
    pct = art_rank_2026 / art_total_2026
    target_rank_2025 = max(1, min(art_total_2025, round(pct * art_total_2025)))
    equiv_pro = score_from_rank(art_2025, target_rank_2025)
    equiv_comp = culture * 0.5 + equiv_pro * 1.25
    equiv_rank, _ = rank_from_score(comp_2025, equiv_comp)
    
    pct_a = equiv_rank / comp_total_2025 * 100
    
    # ===== 方案B: 直接用原始分 =====
    direct_rank, direct_total = rank_from_score(comp_2025, raw_comp)
    pct_b = direct_rank / direct_total * 100
    
    print('  方案A (百分位映射):')
    print(f'    2026专业排名: 第{art_rank_2026}/{art_total_2026}名 (top {pct*100:.1f}%)')
    print(f'    等位2025专业分: {equiv_pro:.2f}')
    print(f'    等位综合分: {equiv_comp:.2f}  -> 2025综合排名 第{equiv_rank}/{comp_total_2025}名 (top {pct_a:.1f}%)')
    
    print('  方案B (直接用505分):')
    print(f'    原始综合分: {raw_comp}  -> 2025综合排名 第{direct_rank}/{direct_total}名 (top {pct_b:.1f}%)')
    
    diff = equiv_rank - direct_rank
    print(f'  差异: 方案B比方案A 排名差 {diff:+d} 名 ({(diff/comp_total_2025*100):+.2f}%)')

# ========== 跨年稳定性 ==========
print()
print('=' * 60)
print('跨年稳定性: 同一个综合分 2024 vs 2025 排名差多少')
print('=' * 60)

for dir_key, name in [('vocal', '声乐'), ('instrumental', '器乐'), ('education', '音乐教育')]:
    comp_2024 = ranks.get(dir_key + '_2024')
    comp_2025 = ranks[dir_key + '_2025']
    if not comp_2024:
        continue
    
    t24 = max(comp_2024.values())
    t25 = max(comp_2025.values())
    
    print()
    print('--- ' + name + ' (2024共' + str(t24) + '人 / 2025共' + str(t25) + '人) ---')
    print('  {:>8}  {:>10}  {:>10}  {:>8}'.format('分数', '2024排名', '2025排名', '百分位差'))
    print('  ' + '-' * 44)
    
    diffs = []
    for comp_score in [420, 440, 460, 470, 480, 490, 500, 505, 510, 520, 540, 560, 580]:
        r24, _ = rank_from_score(comp_2024, comp_score)
        r25, _ = rank_from_score(comp_2025, comp_score)
        p24 = r24 / t24 * 100
        p25 = r25 / t25 * 100
        d = p25 - p24
        diffs.append(abs(d))
        marker = '  *** 你的分数 ***' if comp_score == 505 else ''
        print('  {:>8}  {:>10}  {:>10}  {:>+7.2f}% {}'.format(
            comp_score, r24, r25, d, marker))

    avg_diff = sum(diffs) / len(diffs)
    print('  平均绝对百分位差: {:.2f}% (约 {:.0f} 人)'.format(avg_diff, avg_diff/100*t25))

# ========== 你的505分在三年的位置 ==========
print()
print('=' * 60)
print('你的 505 分在 2024/2025 综合表中的位置')
print('=' * 60)
for dir_key, name in [('vocal', '声乐'), ('instrumental', '器乐'), ('education', '音乐教育')]:
    comp_2025 = ranks[dir_key + '_2025']
    comp_2024 = ranks.get(dir_key + '_2024')
    total5 = max(comp_2025.values())
    r5, _ = rank_from_score(comp_2025, 505)
    p5 = r5 / total5 * 100
    
    if comp_2024:
        total4 = max(comp_2024.values())
        r4, _ = rank_from_score(comp_2024, 505)
        p4 = r4 / total4 * 100
        print('  {}: 2024年第{}/{}名 (top{:.1f}%)  |  2025年第{}/{}名 (top{:.1f}%)'.format(
            name, r4, total4, p4, r5, total5, p5))
    else:
        print('  {}: 2025年第{}/{}名 (top{:.1f}%)'.format(name, r5, total5, p5))
