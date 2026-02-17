# Lead Quality Analysis - Executive Summary

## Baseline & Methodology

**Lead Quality主指标定义：**
- **GoodQualityRate** (Primary): (Closed + EP Sent + EP Received + EP Confirmed) / All Leads
- **CloseRate**: Closed / All Leads  
- **BadRate**: (Unable to Contact + Invalid Profile + Doesn't Qualify) / All Leads

**数据规模：** 2,786 leads

---

## Q1: Lead质量趋势

**结论：** Lead质量**改善**

- **趋势方向：** 改善
- **统计显著性：** p = 0.0000, **显著** (α=0.05)
- **前1/2 vs 后1/2对比：**
  - 前1/2 GoodQualityRate: 0.0481 (4.81%)
  - 后1/2 GoodQualityRate: 0.0653 (6.53%)
  - 变化幅度: 0.0172 (35.82%相对变化)

**可能原因：**
- 需要结合驱动因素分析进一步解释（见Q2）

---

## Q2: 驱动因素与分群

### Top 3 高质量段（建议加码）

| Segment | Dimension | GoodQualityRate | Lift | Sample Size |
|---------|-----------|----------------|------|-------------|
| 5 | phone_score_bin | 0.0830 (8.30%) | 1.46x | 566 |
| 5 | address_score_bin | 0.0706 (7.06%) | 1.25x | 807 |
| True | is_branded | 0.0600 (6.00%) | 1.06x | 1116 |

### Top 3 低质量段（建议砍掉）

| Segment | Dimension | GoodQualityRate | Lift | Sample Size |
|---------|-----------|----------------|------|-------------|
| Top Right-300x250 | publisher_zone | 0.0299 (2.99%) | 0.53x | 234 |
| missing | phone_score_bin | 0.0491 (4.91%) | 0.87x | 1487 |
| missing | address_score_bin | 0.0502 (5.02%) | 0.88x | 1694 |

**关键驱动因素：**
1. 详见 `03_driver_analysis.ipynb` 中的模型重要性分析

**建议动作：**
- **加码：** 高质量段（见上表）
- **砍掉：** 低质量段（见上表）

---

## Q3: 能否达到9.6%目标？

**当前Baseline GoodQualityRate：** 0.0567 (5.67%)  
**目标GoodQualityRate：** 9.6%  
**需要提升：** 3.93个百分点 (69.28%相对提升)

### 情景模拟结果

**Scenario A: 砍掉最差5%流量**
- 新质量: 0.0597 (5.97%)
- Volume影响: 下降 5.0%
- ✗ 未达到目标

**Scenario A: 砍掉最差10%流量**
- 新质量: 0.0630 (6.30%)
- Volume影响: 下降 10.0%
- ✗ 未达到目标

**Scenario A: 砍掉最差15%流量**
- 新质量: 0.0667 (6.67%)
- Volume影响: 下降 15.0%
- ✗ 未达到目标

### 最终结论

**能否达到9.6%：** ✗ **不能**

**上限：** 0.0567 (5.67%)
**瓶颈原因：** 
  - 高质量段供给不足
  - 可扩量有限
  - 需要进一步优化投放策略
**下一步数据需求：** 需要更多高质量流量来源的数据

---

## Appendix: 详细分析结果

详细的分群表、模型输出和情景模拟表请参考：
- `01_load_and_clean.ipynb` - 数据清洗与特征工程
- `02_trend_analysis.ipynb` - 趋势分析细节
- `03_driver_analysis.ipynb` - 驱动因素分析细节
- `04_uplift_scenarios.ipynb` - 情景模拟细节

---

*报告生成日期: 2026-02-16 14:24:20*
