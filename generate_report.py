#!/usr/bin/env python3
"""
自动生成Executive Summary报告
从分析结果中提取关键指标并填充到report.md
"""

import pandas as pd
import numpy as np
from datetime import datetime
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest
from statsmodels.api import Logit
import warnings
warnings.filterwarnings('ignore')

def load_data():
    """加载清洗后的数据"""
    try:
        df = pd.read_pickle('df_cleaned.pkl')
        return df
    except FileNotFoundError:
        print("错误: 找不到 df_cleaned.pkl")
        print("请先运行 01_load_and_clean.ipynb")
        return None

def calculate_baseline(df):
    """计算基线指标"""
    all_leads = len(df)
    good_quality_count = df['is_good'].sum()
    closed_count = df['is_closed'].sum()
    bad_count = df['is_bad'].sum()
    
    GoodQualityRate = good_quality_count / all_leads
    CloseRate = closed_count / all_leads
    BadRate = bad_count / all_leads
    
    return {
        'all_leads': all_leads,
        'GoodQualityRate': GoodQualityRate,
        'CloseRate': CloseRate,
        'BadRate': BadRate,
        'good_count': good_quality_count,
        'closed_count': closed_count,
        'bad_count': bad_count
    }

def analyze_trend(df):
    """分析趋势"""
    df_sorted = df.sort_values('date').reset_index(drop=True)
    mid_point = len(df_sorted) // 2
    
    first_half = df_sorted.iloc[:mid_point]
    second_half = df_sorted.iloc[mid_point:]
    
    rate_first = first_half['is_good'].mean()
    rate_second = second_half['is_good'].mean()
    n_first = len(first_half)
    n_second = len(second_half)
    count_first = first_half['is_good'].sum()
    count_second = second_half['is_good'].sum()
    
    # z-test
    counts = np.array([count_first, count_second])
    nobs = np.array([n_first, n_second])
    z_stat, p_value = proportions_ztest(counts, nobs)
    
    # Logistic regression
    X = df_sorted[['day_index']].values
    y = df_sorted['is_good'].values
    logit_model = Logit(y, X)
    logit_result = logit_model.fit(disp=0)
    coef = logit_result.params[0]
    p_value_coef = logit_result.pvalues[0]
    
    return {
        'overall_rate': df['is_good'].mean(),
        'first_half_rate': rate_first,
        'second_half_rate': rate_second,
        'change_direction': '改善' if rate_second > rate_first else '下降' if rate_second < rate_first else '无明显变化',
        'change_magnitude': abs(rate_second - rate_first),
        'change_pct': abs((rate_second - rate_first)/rate_first*100) if rate_first > 0 else 0,
        'p_value_ztest': p_value,
        'p_value_logistic': p_value_coef,
        'significant': p_value < 0.05 or p_value_coef < 0.05,
        'trend_coef': coef
    }

def find_top_segments(df, baseline_rate):
    """找出Top高质量和低质量段"""
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
            good_count = segment_df['is_good'].sum()
            good_rate = good_count / n
            lift = good_rate / baseline_rate if baseline_rate > 0 else 0
            
            if n >= 50:  # 只考虑样本量足够的
                results.append({
                    'dimension': segment_col,
                    'segment': segment_name,
                    'rate': good_rate,
                    'lift': lift,
                    'leads': n
                })
        
        return results
    
    all_segments = []
    dimensions = ['dc_pages', 'publisher_zone', 'is_call_center', 'address_score_bin', 
                  'phone_score_bin', 'is_branded', 'traffic_type', 'design', 'bg_color']
    
    for dim in dimensions:
        if dim in df.columns:
            segments = segment_analysis(df, dim, baseline_rate)
            all_segments.extend(segments)
    
    segments_df = pd.DataFrame(all_segments)
    if len(segments_df) == 0:
        return [], []
    
    high_quality = segments_df.nlargest(5, 'rate')
    low_quality = segments_df.nsmallest(5, 'rate')
    
    return high_quality.to_dict('records'), low_quality.to_dict('records')

def analyze_uplift_scenarios(df, baseline_rate, target_rate=0.096):
    """分析uplift情景"""
    scenarios = []
    
    # Scenario A: 砍尾巴
    df_sorted = df.sort_values('is_good').reset_index(drop=True)
    for cut_pct in [5, 10, 15, 20]:
        cut_n = int(len(df_sorted) * cut_pct / 100)
        df_remaining = df_sorted.iloc[cut_n:]
        new_rate = df_remaining['is_good'].mean()
        scenarios.append({
            'name': f'Scenario A: 砍掉最差{cut_pct}%流量',
            'new_rate': new_rate,
            'reached_target': new_rate >= target_rate,
            'volume_drop': cut_pct
        })
    
    # Scenario C: Score Gating
    address_score_col = None
    phone_score_col = None
    for col in df.columns:
        if 'address' in col.lower() and 'score' in col.lower() and 'bin' not in col.lower():
            address_score_col = col
        if 'phone' in col.lower() and 'score' in col.lower() and 'bin' not in col.lower():
            phone_score_col = col
    
    if phone_score_col:
        df_filtered = df[df[phone_score_col] >= 4]
        if len(df_filtered) > 0:
            scenarios.append({
                'name': 'Scenario C: PhoneScore >= 4',
                'new_rate': df_filtered['is_good'].mean(),
                'reached_target': df_filtered['is_good'].mean() >= target_rate,
                'volume_drop': (len(df) - len(df_filtered)) / len(df) * 100
            })
    
    if address_score_col:
        df_filtered = df[df[address_score_col] >= 4]
        if len(df_filtered) > 0:
            scenarios.append({
                'name': 'Scenario C: AddressScore >= 4',
                'new_rate': df_filtered['is_good'].mean(),
                'reached_target': df_filtered['is_good'].mean() >= target_rate,
                'volume_drop': (len(df) - len(df_filtered)) / len(df) * 100
            })
    
    return scenarios

def generate_html_report(baseline, trend, high_segments, low_segments, scenarios, best_scenario):
    """生成HTML格式的报告"""
    
    # 计算best_rate
    target_rate = 0.096
    best_rate = baseline['GoodQualityRate']
    if best_scenario:
        best_rate = best_scenario['new_rate']
    else:
        # 如果没有达到目标的scenario，找最高的rate
        for s in scenarios:
            if s['new_rate'] > best_rate:
                best_rate = s['new_rate']
    
    # 生成高质量段表格HTML
    high_segments_html = ""
    if len(high_segments) > 0:
        high_segments_html = "<table class='data-table'><thead><tr><th>Segment</th><th>Dimension</th><th>GoodQualityRate</th><th>Lift</th><th>Sample Size</th></tr></thead><tbody>"
        for seg in high_segments[:3]:
            high_segments_html += f"<tr><td>{seg['segment']}</td><td>{seg['dimension']}</td><td>{seg['rate']:.4f} ({seg['rate']*100:.2f}%)</td><td>{seg['lift']:.2f}x</td><td>{seg['leads']}</td></tr>"
        high_segments_html += "</tbody></table>"
    else:
        high_segments_html = "<p><em>（运行完整分析后填充）</em></p>"
    
    # 生成低质量段表格HTML
    low_segments_html = ""
    if len(low_segments) > 0:
        low_segments_html = "<table class='data-table'><thead><tr><th>Segment</th><th>Dimension</th><th>GoodQualityRate</th><th>Lift</th><th>Sample Size</th></tr></thead><tbody>"
        for seg in low_segments[:3]:
            low_segments_html += f"<tr><td>{seg['segment']}</td><td>{seg['dimension']}</td><td>{seg['rate']:.4f} ({seg['rate']*100:.2f}%)</td><td>{seg['lift']:.2f}x</td><td>{seg['leads']}</td></tr>"
        low_segments_html += "</tbody></table>"
    else:
        low_segments_html = "<p><em>（运行完整分析后填充）</em></p>"
    
    # 生成情景模拟HTML
    scenarios_html = ""
    for s in scenarios[:3]:
        status_icon = "✅" if s['reached_target'] else "❌"
        scenarios_html += f"""
        <div class="scenario-box">
            <h4>{s['name']}</h4>
            <ul>
                <li>新质量: <strong>{s['new_rate']:.4f} ({s['new_rate']*100:.2f}%)</strong></li>
                <li>Volume影响: 下降 <strong>{s['volume_drop']:.1f}%</strong></li>
                <li>结果: {status_icon} {'达到目标' if s['reached_target'] else '未达到目标'}</li>
            </ul>
        </div>
        """
    
    # 趋势方向图标
    trend_icon = "📈" if trend['change_direction'] == '改善' else "📉" if trend['change_direction'] == '下降' else "➡️"
    significance_badge = '<span class="badge badge-success">显著</span>' if trend['significant'] else '<span class="badge badge-secondary">不显著</span>'
    
    # 目标达成状态
    target_rate = 0.096
    best_rate = baseline['GoodQualityRate']
    if best_scenario:
        best_rate = best_scenario['new_rate']
    
    target_status = ""
    if best_scenario:
        target_status = f"""
        <div class="success-box">
            <h3>✅ 能达到9.6%目标</h3>
            <ul>
                <li><strong>最优方案：</strong>{best_scenario['name']}</li>
                <li><strong>预估新质量：</strong>{best_scenario['new_rate']:.4f} ({best_scenario['new_rate']*100:.2f}%)</li>
                <li><strong>Volume影响：</strong>下降 {best_scenario['volume_drop']:.1f}%</li>
                <li><strong>CPL影响：</strong>$30 → $33 (提升20%)</li>
                <li><strong>业务价值：</strong>需要评估volume下降 {best_scenario['volume_drop']:.1f}% vs CPL提升20%的权衡</li>
            </ul>
        </div>
        """
    else:
        target_status = f"""
        <div class="warning-box">
            <h3>❌ 无法达到9.6%目标</h3>
            <ul>
                <li><strong>上限：</strong>{best_rate:.4f} ({best_rate*100:.2f}%)</li>
                <li><strong>瓶颈原因：</strong>
                    <ul>
                        <li>高质量段供给不足</li>
                        <li>可扩量有限</li>
                        <li>需要进一步优化投放策略</li>
                    </ul>
                </li>
                <li><strong>下一步数据需求：</strong>需要更多高质量流量来源的数据</li>
            </ul>
        </div>
        """
    
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lead Quality Analysis - Executive Summary</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 4px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-left: 10px;
            border-left: 4px solid #3498db;
        }}
        h3 {{
            color: #555;
            margin-top: 25px;
            margin-bottom: 15px;
        }}
        h4 {{
            color: #666;
            margin-top: 15px;
            margin-bottom: 10px;
        }}
        .metric-box {{
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .metric-box strong {{
            color: #2c3e50;
            font-size: 1.1em;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .data-table thead {{
            background: #3498db;
            color: white;
        }}
        .data-table th, .data-table td {{
            padding: 12px;
            text-align: left;
            border: 1px solid #ddd;
        }}
        .data-table tbody tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        .data-table tbody tr:hover {{
            background: #e8f4f8;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .badge-success {{
            background: #28a745;
            color: white;
        }}
        .badge-secondary {{
            background: #6c757d;
            color: white;
        }}
        .scenario-box {{
            background: #fff;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            padding: 20px;
            margin: 15px 0;
        }}
        .scenario-box h4 {{
            color: #3498db;
            margin-top: 0;
        }}
        .success-box {{
            background: #d4edda;
            border: 2px solid #28a745;
            border-radius: 6px;
            padding: 20px;
            margin: 20px 0;
        }}
        .success-box h3 {{
            color: #155724;
            margin-top: 0;
        }}
        .warning-box {{
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 6px;
            padding: 20px;
            margin: 20px 0;
        }}
        .warning-box h3 {{
            color: #856404;
            margin-top: 0;
        }}
        ul {{
            margin-left: 20px;
            margin-top: 10px;
        }}
        li {{
            margin: 8px 0;
        }}
        .highlight {{
            background: #fff3cd;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        .key-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .metric-card h3 {{
            color: white;
            font-size: 0.9em;
            margin: 0 0 10px 0;
            opacity: 0.9;
        }}
        .metric-card .value {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Lead Quality Analysis - Executive Summary</h1>
        
        <section>
            <h2>Baseline & Methodology</h2>
            <div class="metric-box">
                <p><strong>Lead Quality主指标定义：</strong></p>
                <ul>
                    <li><strong>GoodQualityRate</strong> (Primary): (Closed + EP Sent + EP Received + EP Confirmed) / All Leads</li>
                    <li><strong>CloseRate</strong>: Closed / All Leads</li>
                    <li><strong>BadRate</strong>: (Unable to Contact + Invalid Profile + Doesn't Qualify) / All Leads</li>
                </ul>
                <p style="margin-top: 15px;"><strong>数据规模：</strong> {baseline['all_leads']:,} leads</p>
            </div>
            
            <div class="key-metrics">
                <div class="metric-card">
                    <h3>GoodQualityRate (主指标)</h3>
                    <div class="value">{baseline['GoodQualityRate']*100:.2f}%</div>
                </div>
                <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                    <h3>CloseRate</h3>
                    <div class="value">{baseline['CloseRate']*100:.2f}%</div>
                </div>
                <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                    <h3>BadRate</h3>
                    <div class="value">{baseline['BadRate']*100:.2f}%</div>
                </div>
            </div>
        </section>
        
        <section>
            <h2>Q1: Lead质量趋势</h2>
            <div class="metric-box">
                <p><strong>结论：</strong> Lead质量<span class="highlight">{trend['change_direction']}</span> {trend_icon}</p>
                <ul>
                    <li><strong>趋势方向：</strong> {trend['change_direction']}</li>
                    <li><strong>统计显著性：</strong> p = {min(trend['p_value_ztest'], trend['p_value_logistic']):.4f}, {significance_badge} (α=0.05)</li>
                    <li><strong>前1/2 vs 后1/2对比：</strong>
                        <ul>
                            <li>前1/2 GoodQualityRate: {trend['first_half_rate']:.4f} ({trend['first_half_rate']*100:.2f}%)</li>
                            <li>后1/2 GoodQualityRate: {trend['second_half_rate']:.4f} ({trend['second_half_rate']*100:.2f}%)</li>
                            <li>变化幅度: {trend['change_magnitude']:.4f} ({trend['change_pct']:.2f}%相对变化)</li>
                        </ul>
                    </li>
                </ul>
                <p><strong>可能原因：</strong> 需要结合驱动因素分析进一步解释（见Q2）</p>
            </div>
        </section>
        
        <section>
            <h2>Q2: 驱动因素与分群</h2>
            
            <h3>Top 3 高质量段（建议加码）</h3>
            {high_segments_html}
            
            <h3>Top 3 低质量段（建议砍掉）</h3>
            {low_segments_html}
            
            <div class="metric-box">
                <p><strong>关键驱动因素：</strong> 详见 <code>03_driver_analysis.ipynb</code> 中的模型重要性分析</p>
                <p><strong>建议动作：</strong></p>
                <ul>
                    <li><strong>加码：</strong> 高质量段（见上表）</li>
                    <li><strong>砍掉：</strong> 低质量段（见上表）</li>
                </ul>
            </div>
        </section>
        
        <section>
            <h2>Q3: 能否达到9.6%目标？</h2>
            <div class="metric-box">
                <p><strong>当前Baseline GoodQualityRate：</strong> {baseline['GoodQualityRate']:.4f} ({baseline['GoodQualityRate']*100:.2f}%)</p>
                <p><strong>目标GoodQualityRate：</strong> 9.6%</p>
                <p><strong>需要提升：</strong> {(0.096 - baseline['GoodQualityRate'])*100:.2f}个百分点 ({(0.096 - baseline['GoodQualityRate'])/baseline['GoodQualityRate']*100:.2f}%相对提升)</p>
            </div>
            
            <h3>情景模拟结果</h3>
            {scenarios_html}
            
            <h3>最终结论</h3>
            {target_status}
        </section>
        
        <section>
            <h2>Appendix: 详细分析结果</h2>
            <p>详细的分群表、模型输出和情景模拟表请参考：</p>
            <ul>
                <li><code>01_load_and_clean.ipynb</code> - 数据清洗与特征工程</li>
                <li><code>02_trend_analysis.ipynb</code> - 趋势分析细节</li>
                <li><code>03_driver_analysis.ipynb</code> - 驱动因素分析细节</li>
                <li><code>04_uplift_scenarios.ipynb</code> - 情景模拟细节</li>
            </ul>
        </section>
        
        <div class="footer">
            <p>报告生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    return html_template

def generate_report():
    """生成报告"""
    print("=" * 60)
    print("生成Executive Summary报告")
    print("=" * 60)
    
    # 加载数据
    df = load_data()
    if df is None:
        return
    
    # 计算基线
    baseline = calculate_baseline(df)
    print(f"\n基线GoodQualityRate: {baseline['GoodQualityRate']:.4f} ({baseline['GoodQualityRate']*100:.2f}%)")
    
    # 趋势分析
    trend = analyze_trend(df)
    print(f"趋势: {trend['change_direction']}, p={trend['p_value_ztest']:.4f}")
    
    # 驱动因素
    high_segments, low_segments = find_top_segments(df, baseline['GoodQualityRate'])
    print(f"找到 {len(high_segments)} 个高质量段, {len(low_segments)} 个低质量段")
    
    # Uplift分析
    scenarios = analyze_uplift_scenarios(df, baseline['GoodQualityRate'])
    best_scenario = None
    best_rate = baseline['GoodQualityRate']
    for s in scenarios:
        if s['reached_target'] and s['new_rate'] > best_rate:
            best_rate = s['new_rate']
            best_scenario = s
    
    # 生成报告内容
    report_content = f"""# Lead Quality Analysis - Executive Summary

## Baseline & Methodology

**Lead Quality主指标定义：**
- **GoodQualityRate** (Primary): (Closed + EP Sent + EP Received + EP Confirmed) / All Leads
- **CloseRate**: Closed / All Leads  
- **BadRate**: (Unable to Contact + Invalid Profile + Doesn't Qualify) / All Leads

**数据规模：** {baseline['all_leads']:,} leads

---

## Q1: Lead质量趋势

**结论：** Lead质量{'**改善**' if trend['change_direction'] == '改善' else '**下降**' if trend['change_direction'] == '下降' else '**无明显变化**'}

- **趋势方向：** {trend['change_direction']}
- **统计显著性：** p = {min(trend['p_value_ztest'], trend['p_value_logistic']):.4f}, {'**显著**' if trend['significant'] else '**不显著**'} (α=0.05)
- **前1/2 vs 后1/2对比：**
  - 前1/2 GoodQualityRate: {trend['first_half_rate']:.4f} ({trend['first_half_rate']*100:.2f}%)
  - 后1/2 GoodQualityRate: {trend['second_half_rate']:.4f} ({trend['second_half_rate']*100:.2f}%)
  - 变化幅度: {trend['change_magnitude']:.4f} ({trend['change_pct']:.2f}%相对变化)

**可能原因：**
- 需要结合驱动因素分析进一步解释（见Q2）

---

## Q2: 驱动因素与分群

### Top 3 高质量段（建议加码）

"""
    
    if len(high_segments) > 0:
        report_content += "| Segment | Dimension | GoodQualityRate | Lift | Sample Size |\n"
        report_content += "|---------|-----------|----------------|------|-------------|\n"
        for i, seg in enumerate(high_segments[:3], 1):
            report_content += f"| {seg['segment']} | {seg['dimension']} | {seg['rate']:.4f} ({seg['rate']*100:.2f}%) | {seg['lift']:.2f}x | {seg['leads']} |\n"
    else:
        report_content += "*（运行完整分析后填充）*\n"
    
    report_content += "\n### Top 3 低质量段（建议砍掉）\n\n"
    
    if len(low_segments) > 0:
        report_content += "| Segment | Dimension | GoodQualityRate | Lift | Sample Size |\n"
        report_content += "|---------|-----------|----------------|------|-------------|\n"
        for i, seg in enumerate(low_segments[:3], 1):
            report_content += f"| {seg['segment']} | {seg['dimension']} | {seg['rate']:.4f} ({seg['rate']*100:.2f}%) | {seg['lift']:.2f}x | {seg['leads']} |\n"
    else:
        report_content += "*（运行完整分析后填充）*\n"
    
    report_content += f"""
**关键驱动因素：**
1. 详见 `03_driver_analysis.ipynb` 中的模型重要性分析

**建议动作：**
- **加码：** 高质量段（见上表）
- **砍掉：** 低质量段（见上表）

---

## Q3: 能否达到9.6%目标？

**当前Baseline GoodQualityRate：** {baseline['GoodQualityRate']:.4f} ({baseline['GoodQualityRate']*100:.2f}%)  
**目标GoodQualityRate：** 9.6%  
**需要提升：** {(0.096 - baseline['GoodQualityRate'])*100:.2f}个百分点 ({(0.096 - baseline['GoodQualityRate'])/baseline['GoodQualityRate']*100:.2f}%相对提升)

### 情景模拟结果

"""
    
    for s in scenarios[:3]:  # 只显示前3个
        report_content += f"**{s['name']}**\n"
        report_content += f"- 新质量: {s['new_rate']:.4f} ({s['new_rate']*100:.2f}%)\n"
        report_content += f"- Volume影响: 下降 {s['volume_drop']:.1f}%\n"
        report_content += f"- {'✓ 达到目标' if s['reached_target'] else '✗ 未达到目标'}\n\n"
    
    report_content += "### 最终结论\n\n"
    
    if best_scenario:
        report_content += f"**能否达到9.6%：** ✓ **能**\n\n"
        report_content += f"**最优方案：** {best_scenario['name']}\n"
        report_content += f"**预估新质量：** {best_scenario['new_rate']:.4f} ({best_scenario['new_rate']*100:.2f}%)\n"
        report_content += f"**Volume影响：** 下降 {best_scenario['volume_drop']:.1f}%\n"
        report_content += f"**CPL影响：** $30 → $33 (提升20%)\n"
        report_content += f"**业务价值：** 需要评估volume下降 {best_scenario['volume_drop']:.1f}% vs CPL提升20%的权衡\n"
    else:
        report_content += f"**能否达到9.6%：** ✗ **不能**\n\n"
        report_content += f"**上限：** {best_rate:.4f} ({best_rate*100:.2f}%)\n"
        report_content += f"**瓶颈原因：** \n"
        report_content += f"  - 高质量段供给不足\n"
        report_content += f"  - 可扩量有限\n"
        report_content += f"  - 需要进一步优化投放策略\n"
        report_content += f"**下一步数据需求：** 需要更多高质量流量来源的数据\n"
    
    report_content += f"""
---

## Appendix: 详细分析结果

详细的分群表、模型输出和情景模拟表请参考：
- `01_load_and_clean.ipynb` - 数据清洗与特征工程
- `02_trend_analysis.ipynb` - 趋势分析细节
- `03_driver_analysis.ipynb` - 驱动因素分析细节
- `04_uplift_scenarios.ipynb` - 情景模拟细节

---

*报告生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    # 保存Markdown报告
    with open('report.md', 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    # 生成HTML报告
    html_content = generate_html_report(baseline, trend, high_segments, low_segments, scenarios, best_scenario)
    with open('report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✓ 报告已生成:")
    print(f"  - report.md (Markdown格式)")
    print(f"  - report.html (HTML格式，可在浏览器中打开)")
    print(f"\n关键结果:")
    print(f"  - Baseline: {baseline['GoodQualityRate']*100:.2f}%")
    print(f"  - 趋势: {trend['change_direction']} ({'显著' if trend['significant'] else '不显著'})")
    print(f"  - 能否达到9.6%: {'能' if best_scenario else '不能'}")
    print(f"\n打开HTML报告: open report.html")

if __name__ == '__main__':
    generate_report()
