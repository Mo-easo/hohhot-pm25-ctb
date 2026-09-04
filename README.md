# 青城清气 —— 呼和浩特市 PM2.5 智能监测、预测与污染干预决策系统

面向 **CTB（China Thinks Big）环境健康方向** 的研究型 Web 平台，目标是构建：

**监测 → 分析 → 预测 → 干预 → 评估** 闭环系统。

> 当前版本：**Phase 1**（项目架构 + Flask + 首页 + 数据库 + DEMO 数据）  
> 演示数据已明确标注为 **DEMO DATA**，**不是实时监测数据**。

---

## 项目背景

呼和浩特（青城）冬季供暖与气象条件可能加剧颗粒物污染。本项目不满足于“查一下 AQI”，而是围绕可检验的研究问题，用数据科学 + WebGIS + 可解释预测支持低成本干预讨论。

## 研究问题（RQ1–RQ7）

1. PM2.5 是否存在季节 / 月 / 星期 / 小时规律？
2. 与温度、湿度、风速、降水及其他污染物的关系？
3. 监测站点间是否存在空间差异？
4. 能否用历史 PM2.5 + 气象预测未来 24 小时？
5. 能否提前识别高风险时段？
6. 能否识别污染风险较高区域？
7. 可给出怎样的低成本、可执行干预建议？

## 项目创新（相对普通查询站）

- 数据溯源与 **REAL / SIMULATED / DEMO** 三分法，禁止伪实时
- 完整清洗与质量报告（Phase 2）
- 时空可视化 + 风险估计地图（Phase 4）
- 时序正确的 ML 预测与可解释性（Phase 5–6）
- 干预情景模拟器（Phase 8）与实地评估（Phase 9）
- CTB 展示模式（Phase 10）

## 技术架构

| 层 | 技术 |
|----|------|
| 后端 | Python, Flask, SQLite |
| 数据 | Pandas / NumPy（后续阶段） |
| ML | Scikit-learn（Linear / RF / GBM；可选 XGBoost） |
| 前端 | HTML5, CSS3, JavaScript |
| 可视化 | ECharts, Leaflet |

## 数据来源

**Phase 1：** `scripts/generate_demo_data.py` 生成的 **DEMO DATA**（多站点小时序列）。

**后续优先：**

1. 中国环境监测总站公开数据  
2. 内蒙古自治区生态环境厅公开数据  
3. 公开科研数据集  

单位：PM 类 µg/m³；CO mg/m³；温湿度、风速、气压、降水见数据来源页。

## 数据处理 / 机器学习 / 评价

- **Phase 1：** 仅入库与 API，不做清洗结论或模型训练。  
- **Phase 2+：** 清洗流水线 → `data_quality_report.json`  
- **Phase 5：** TimeSeriesSplit，报告 MAE / RMSE / R²；禁止把预测包装为绝对准确。  
- **相关 ≠ 因果：** 页面固定提示 *Correlation does not imply causation.*

## 实验结果

Phase 1 **无正式实验结果**。实地评估未完成时显示「尚未完成实地评估」。

## 局限性

- 当前为演示数据，不可用于真实决策  
- 站点坐标为近似公开位置，用于联调  
- 风险曲线为占位算法，非训练模型  

## 未来工作

按 Phase 2→10 推进：真实数据接口、EDA、WebGIS、ML、SHAP、事件识别、干预模拟、调查评估、CTB 演示模式。

---

## 安装方法

```bash
cd hohhot_pm25_ctb
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

可选：复制 `.env.example` 为环境变量来源（密钥勿写入代码）。

## 运行方法

```bash
# 1) 生成 DEMO 数据并写入 SQLite
python scripts/generate_demo_data.py

# 2) 启动 Flask
python app.py
```

浏览器访问：<http://127.0.0.1:5000>

运行测试：

```bash
pytest -q
```

## 项目结构

```
hohhot_pm25_ctb/
├── app.py                 # Flask 入口与 API
├── config.py              # 配置与环境变量
├── database.py            # SQLite schema / 查询
├── requirements.txt
├── README.md
├── data/                  # raw / cleaned / processed
├── models/                # 模型产物（后续阶段）
├── analysis/              # 分析模块（占位 → 分阶段实现）
├── scripts/               # 演示数据生成等
├── templates/             # 页面
├── static/                # CSS / JS
└── tests/
```

## API（Phase 1）

| 路径 | 说明 |
|------|------|
| `GET /api/health` | 健康检查 |
| `GET /api/meta` | 数据模式与时间范围 |
| `GET /api/stations` | 监测站点 |
| `GET /api/latest` | 城市/站点最新值（含 DEMO 横幅） |
| `GET /api/trend?hours=24\|48\|72\|168` | 城市趋势 |
| `GET /api/risk/forecast-placeholder` | 占位风险（非 ML） |

错误响应统一为：

```json
{"ok": false, "error": {"code": "...", "message": "..."}}
```

---

**青城清气** · CTB 环境健康 · Phase 1
