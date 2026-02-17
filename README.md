# Lead Quality Analysis Project

## 项目结构

```
.
├── 01_load_and_clean.ipynb          # 数据读取、清洗、特征工程
├── 02_trend_analysis.ipynb          # 问题1：趋势分析
├── 03_driver_analysis.ipynb          # 问题2：驱动因素分析
├── 04_uplift_scenarios.ipynb        # 问题3：9.6%目标情景模拟
├── report.md                         # Executive Summary报告
├── requirements.txt                  # Python依赖
└── README.md                         # 本文件
```

## 使用说明

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 执行顺序

**必须按顺序执行notebooks：**

1. **01_load_and_clean.ipynb**
   - 读取Excel数据
   - 数据质量检查
   - CallStatus映射
   - 特征工程
   - 保存清洗后的数据到 `df_cleaned.pkl`

2. **02_trend_analysis.ipynb**
   - 加载 `df_cleaned.pkl`
   - 按天/周聚合分析
   - 趋势图绘制
   - 显著性检验（z-test, logistic regression）

3. **03_driver_analysis.ipynb**
   - 加载 `df_cleaned.pkl`
   - 单变量分群分析
   - 多变量模型（Logistic Regression + Random Forest）
   - 驱动因素总结

4. **04_uplift_scenarios.ipynb**
   - 加载 `df_cleaned.pkl`
   - 3套情景模拟
   - 9.6%目标可达性分析

5. **生成报告**
   - 运行完所有notebooks后，执行：`python3 generate_report.py`
   - 会自动生成 `report.md` 和 `report.html` 两种格式
   - HTML报告更美观，可在浏览器中打开查看

## 关键指标定义

### Lead Quality主指标

1. **GoodQualityRate** (Primary)
   - 定义: (Closed + EP Sent + EP Received + EP Confirmed) / All
   - 这是主要的质量指标

2. **CloseRate**
   - 定义: Closed / All

3. **BadRate**
   - 定义: (Unable to Contact + Invalid Profile + Doesn't Qualify) / All

### CallStatus分组

- **Closed（成交）**
- **Good quality：** EP Sent / EP Received / EP Confirmed
- **Bad quality：** Unable to Contact / Invalid Profile / Doesn't Qualify
- **Unknown：** 既不算好也不算坏

## 注意事项

1. **数据文件路径：** 确保 `Analyst_case_study_dataset_1_(1) (1).xls` 在当前目录
2. **列名映射：** 代码会自动查找列名，但如果列名不匹配，需要手动调整
3. **缺失值处理：** AddressScore和PhoneScore的missing值会被单独分析
4. **WidgetName解析：** 300250和302252会被合并为同一类

## 输出文件

- `df_cleaned.pkl` - 清洗后的数据（供后续notebooks使用）
- `trend_daily.png` - 趋势图（如果生成）
- `report.md` - Markdown格式的Executive Summary
- `report.html` - **HTML格式的Executive Summary**（美观，可在浏览器中打开）✨

## 生成报告

运行完所有notebooks后：

```bash
python3 generate_report.py
```

这会自动生成：
- ✅ `report.md` - Markdown格式报告
- ✅ `report.html` - **HTML格式报告**（美观，可在浏览器中打开）

**打开HTML报告：**
```bash
open report.html  # Mac
# 或直接双击 report.html 文件
```

HTML报告特点：
- 📱 响应式设计（适配手机/平板/电脑）
- 🎨 现代化UI，彩色指标卡片
- 📊 清晰的表格和情景展示
- ✅ 适合分享和演示

详细说明请参考：`如何生成HTML报告.md`

## 问题反馈

如果遇到问题，请检查：
1. 数据文件是否存在且可读
2. 所有依赖是否已安装（包括xlrd）
3. Notebooks是否按顺序执行
4. 列名是否匹配实际数据
