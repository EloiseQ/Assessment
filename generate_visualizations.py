#!/usr/bin/env python3
"""
生成可视化图表
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

print("生成可视化图表...")

# 加载数据
df = pd.read_pickle('df_cleaned.pkl')
print(f"数据形状: {df.shape}")

# 确保date是datetime类型
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'])

# 1. 趋势图
print("\n1. 生成趋势图...")
daily_stats = df.groupby('date').agg({
    'is_good': ['sum', 'count'],
    'is_closed': 'sum',
    'is_bad': 'sum'
}).reset_index()

daily_stats.columns = ['date', 'good_count', 'total_count', 'closed_count', 'bad_count']
daily_stats['GoodQualityRate'] = daily_stats['good_count'] / daily_stats['total_count']
daily_stats['CloseRate'] = daily_stats['closed_count'] / daily_stats['total_count']
daily_stats['BadRate'] = daily_stats['bad_count'] / daily_stats['total_count']

# 7日滚动均值
daily_stats['GoodQualityRate_7d'] = daily_stats['GoodQualityRate'].rolling(window=7, min_periods=1).mean()
daily_stats['CloseRate_7d'] = daily_stats['CloseRate'].rolling(window=7, min_periods=1).mean()
daily_stats['BadRate_7d'] = daily_stats['BadRate'].rolling(window=7, min_periods=1).mean()

# 95% CI
def calc_ci(n, p, alpha=0.05):
    if n == 0:
        return (0, 0)
    se = np.sqrt(p * (1 - p) / n)
    z = stats.norm.ppf(1 - alpha/2)
    ci_lower = max(0, p - z * se)
    ci_upper = min(1, p + z * se)
    return (ci_lower, ci_upper)

daily_stats['GoodQualityRate_ci_lower'] = daily_stats.apply(
    lambda row: calc_ci(row['total_count'], row['GoodQualityRate'])[0], axis=1
)
daily_stats['GoodQualityRate_ci_upper'] = daily_stats.apply(
    lambda row: calc_ci(row['total_count'], row['GoodQualityRate'])[1], axis=1
)

# 画图
fig, axes = plt.subplots(3, 1, figsize=(14, 12))

# GoodQualityRate
ax1 = axes[0]
ax1.plot(daily_stats['date'], daily_stats['GoodQualityRate'], 'o-', alpha=0.6, label='Daily Rate', markersize=4)
ax1.plot(daily_stats['date'], daily_stats['GoodQualityRate_7d'], '-', linewidth=2, label='7-Day Rolling Mean', color='red')
ax1.fill_between(daily_stats['date'], daily_stats['GoodQualityRate_ci_lower'], 
                 daily_stats['GoodQualityRate_ci_upper'], alpha=0.2, label='95% CI', color='blue')
ax1.set_title('GoodQualityRate Trend (Daily)', fontsize=14, fontweight='bold')
ax1.set_ylabel('Rate', fontsize=12)
ax1.legend()
ax1.grid(True, alpha=0.3)

# CloseRate
ax2 = axes[1]
ax2.plot(daily_stats['date'], daily_stats['CloseRate'], 'o-', alpha=0.6, label='Daily Rate', markersize=4)
ax2.plot(daily_stats['date'], daily_stats['CloseRate_7d'], '-', linewidth=2, label='7-Day Rolling Mean', color='red')
ax2.set_title('CloseRate Trend (Daily)', fontsize=14, fontweight='bold')
ax2.set_ylabel('Rate', fontsize=12)
ax2.legend()
ax2.grid(True, alpha=0.3)

# BadRate
ax3 = axes[2]
ax3.plot(daily_stats['date'], daily_stats['BadRate'], 'o-', alpha=0.6, label='Daily Rate', markersize=4)
ax3.plot(daily_stats['date'], daily_stats['BadRate_7d'], '-', linewidth=2, label='7-Day Rolling Mean', color='red')
ax3.set_title('BadRate Trend (Daily)', fontsize=14, fontweight='bold')
ax3.set_ylabel('Rate', fontsize=12)
ax3.set_xlabel('Date', fontsize=12)
ax3.legend()
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('trend_daily.png', dpi=300, bbox_inches='tight')
print("✓ 趋势图已保存: trend_daily.png")

# 2. 分群对比图（Top高质量和低质量段）
print("\n2. 生成分群对比图...")
baseline_rate = df['is_good'].mean()

# 找出Top高质量和低质量段
def segment_analysis(df, segment_col, baseline_rate):
    results = []
    for segment in df[segment_col].unique():
        if pd.isna(segment):
            segment_df = df[df[segment_col].isna()]
            segment_name = 'missing'
        else:
            segment_df = df[df[segment_col] == segment]
            segment_name = str(segment)
        
        if len(segment_df) == 0:
            continue
        
        n = len(segment_df)
        if n < 50:
            continue
        
        good_rate = segment_df['is_good'].mean()
        lift = good_rate / baseline_rate if baseline_rate > 0 else 0
        
        results.append({
            'dimension': segment_col,
            'segment': segment_name,
            'rate': good_rate,
            'lift': lift,
            'leads': n
        })
    
    return pd.DataFrame(results)

all_segments = []
dimensions = ['dc_pages', 'publisher_zone', 'is_call_center', 'address_score_bin', 
              'phone_score_bin', 'is_branded', 'traffic_type']

for dim in dimensions:
    if dim in df.columns:
        segments = segment_analysis(df, dim, baseline_rate)
        all_segments.extend(segments.to_dict('records'))

segments_df = pd.DataFrame(all_segments)
if len(segments_df) > 0:
    high_quality = segments_df.nlargest(5, 'rate')
    low_quality = segments_df.nsmallest(5, 'rate')
    
    # 创建对比图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Top高质量段
    high_labels = [f"{row['segment']}\n({row['dimension']})" for _, row in high_quality.iterrows()]
    high_rates = high_quality['rate'].values * 100
    
    ax1.barh(range(len(high_quality)), high_rates, color='#2ecc71')
    ax1.set_yticks(range(len(high_quality)))
    ax1.set_yticklabels(high_labels, fontsize=10)
    ax1.set_xlabel('GoodQualityRate (%)', fontsize=12)
    ax1.set_title('Top 5 High-Quality Segments', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='x')
    for i, (rate, lift) in enumerate(zip(high_rates, high_quality['lift'].values)):
        ax1.text(rate + 0.1, i, f'{rate:.2f}% (Lift: {lift:.2f}x)', va='center', fontsize=9)
    
    # Top低质量段
    low_labels = [f"{row['segment']}\n({row['dimension']})" for _, row in low_quality.iterrows()]
    low_rates = low_quality['rate'].values * 100
    
    ax2.barh(range(len(low_quality)), low_rates, color='#e74c3c')
    ax2.set_yticks(range(len(low_quality)))
    ax2.set_yticklabels(low_labels, fontsize=10)
    ax2.set_xlabel('GoodQualityRate (%)', fontsize=12)
    ax2.set_title('Top 5 Low-Quality Segments', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')
    for i, (rate, lift) in enumerate(zip(low_rates, low_quality['lift'].values)):
        ax2.text(rate + 0.1, i, f'{rate:.2f}% (Lift: {lift:.2f}x)', va='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('segments_comparison.png', dpi=300, bbox_inches='tight')
    print("✓ 分群对比图已保存: segments_comparison.png")

# 3. 情景模拟结果图
print("\n3. 生成情景模拟结果图...")
target_rate = 0.096

# Scenario A结果
df_sorted = df.sort_values('is_good').reset_index(drop=True)
scenario_a_results = []
for cut_pct in [5, 10, 15, 20]:
    cut_n = int(len(df_sorted) * cut_pct / 100)
    df_remaining = df_sorted.iloc[cut_n:]
    new_rate = df_remaining['is_good'].mean()
    scenario_a_results.append({
        'cut_pct': cut_pct,
        'new_rate': new_rate * 100,
        'volume_drop': cut_pct
    })

scenario_df = pd.DataFrame(scenario_a_results)

fig, ax = plt.subplots(figsize=(10, 6))
x = scenario_df['cut_pct']
y = scenario_df['new_rate']
colors = ['#e74c3c' if r < target_rate*100 else '#2ecc71' for r in y]

bars = ax.bar(x, y, color=colors, alpha=0.7, width=3)
ax.axhline(y=target_rate*100, color='red', linestyle='--', linewidth=2, label=f'Target: {target_rate*100:.1f}%')
ax.set_xlabel('Volume Cut (%)', fontsize=12)
ax.set_ylabel('New GoodQualityRate (%)', fontsize=12)
ax.set_title('Scenario A: Impact of Cutting Worst Traffic', fontsize=14, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

# 添加数值标签
for bar, rate, drop in zip(bars, y, x):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
            f'{rate:.2f}%\n(-{drop}%)',
            ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('scenario_a_results.png', dpi=300, bbox_inches='tight')
print("✓ 情景模拟图已保存: scenario_a_results.png")

print("\n✓ 所有可视化图表已生成完成！")
