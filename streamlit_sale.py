import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import requests
import io

# ==========================================
# 0. 页面基础配置及炫酷科技感 CSS 注入 (必须作为首句)
# ==========================================
st.set_page_config(page_title="通信销售与复式财务全能云工作台", layout="wide")

# 注入赛博极客/黑客科技感全局视觉样式
st.markdown("""
<style>
    /* 全局深色科技感背景与字体平衡 */
    .stApp {
        background-color: #0E1117;
        color: #E2E8F0;
    }
    /* 侧边栏暗色调调和 */
    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    /* 标题与副标题极光渐变字 */
    h1 {
        font-family: 'Courier New', Courier, monospace;
        background: linear-gradient(45deg, #00f2fe, #4facfe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        letter-spacing: 1px;
    }
    h2, h3, h4 {
        color: #58A6FF !important;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    /* 表单与输入框极客框美化 */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #21262D !important;
        color: #C9D1D9 !important;
        border: 1px solid #30363D !important;
        border-radius: 6px !important;
    }
    .stTextInput>div>div>input:focus {
        border-color: #58A6FF !important;
        box-shadow: 0 0 8px rgba(88, 166, 255, 0.3) !important;
    }
    /* Tab 选项卡高亮 */
    button[data-baseweb="tab"] {
        color: #8B949E !important;
        font-weight: 600;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #58A6FF !important;
        border-bottom-color: #58A6FF !important;
    }
    /* 数据表格现代科技风微调 */
    .stDataFrame div {
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

PROJECT_STAGES = ["线索", "机会点", "招投标", "已中标"]

# ==========================================
# 🗄️ 永久冷数据存储：往年离线归档数据集
# ==========================================
HISTORY_ARCHIVE = {
    "2024": {"revenue": 4200000.0, "collection": 3900000.0}, 
    "2025": {"revenue": 4800000.0, "collection": 4600000.0},
}

BASE_ACCOUNTS = [
    "Assets:WeChat", "Assets:Alipay", "Assets:Card:ICBC", "Assets:Cash", "Assets:Reimbursement",
    "Expenses:Food", "Expenses:Child", "Expenses:Decoration", "Expenses:Travel", "Expenses:Daily",
    "Liabilities:CreditCard", "Income:Salary", "Income:SalesBonus"
]

# ==========================================
# 1. 🚀 官方 API 高速安全驱动引擎
# ==========================================
try:
    SB_URL = st.secrets["secrets"]["SUPABASE_URL"]
    SB_KEY = st.secrets["secrets"]["SUPABASE_KEY"]
    HEADERS = {
        "apikey": SB_KEY,
        "Authorization": f"Bearer {SB_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
except Exception as e:
    st.error("⚠️ 获取凭证失败！请检查 Streamlit 后台 Secrets 是否正确填入 SUPABASE_URL 和 SUPABASE_KEY。")
    st.stop()

@st.cache_data(ttl=1)
def load_db_data():
    """实时读取 Supabase 云数据库数据"""
    try:
        res_p = requests.get(f"{SB_URL}/rest/v1/projects?select=*", headers=HEADERS, timeout=5).json()
        res_o = requests.get(f"{SB_URL}/rest/v1/orders?select=*", headers=HEADERS, timeout=5).json()
        res_c = requests.get(f"{SB_URL}/rest/v1/collections?select=*", headers=HEADERS, timeout=5).json()
        res_r = requests.get(f"{SB_URL}/rest/v1/revenues?select=*", headers=HEADERS, timeout=5).json() 
        res_l = requests.get(f"{SB_URL}/rest/v1/ledger_entries?select=*", headers=HEADERS, timeout=5).json()
    except Exception as e:
        st.error(f"📡 连不上云数据库，网络握手超时！详情: {e}")
        return {}, {}, [], [], []

    projects_dict = {}
    if isinstance(res_p, list):
        for row in res_p:
            projects_dict[row['id']] = {
                "id": row['id'], "name": row['name'], "client": row['client'],
                "target": float(row['target']), "stage": row['stage'], "bid_date": str(row['bid_date']),
                "amt_with_tax_total": 0.0, "collect_total": 0.0
            }
        
    orders_dict = {}
    if isinstance(res_o, list):
        for row in res_o:
            orders_dict[row['id']] = {
                "id": row['id'], "date": str(row['order_date']), "province": row['province'],
                "client": row['client'], "product": row['product'], "price_no_tax": float(row['price_no_tax']),
                "tax_rate": float(row['tax_rate']), "quantity": int(row['quantity']),
                "amt_no_tax": float(row['amt_no_tax']), "amt_with_tax": float(row['amt_with_tax']),
                "p_ref": row.get('project_ref'), "order_p_name": row['order_p_name'], 
                "collect_total": 0.0, "revenue_total": 0.0, "is_history": row.get('project_ref') is None 
            }
        
    collections_list = []
    if isinstance(res_c, list):
        for row in res_c:
            collections_list.append({
                "o_ref": row['order_ref'], "amount": float(row['amount']), 
                "date": str(row['collection_date']), "invoice_no": row.get('invoice_no', '-')
            })

    revenues_list = [] 
    if isinstance(res_r, list):
        for row in res_r:
            revenues_list.append({
                "o_ref": row['order_ref'], "amount": float(row['amount']), "date": str(row['revenue_date'])
            })

    ledger_list = []
    if isinstance(res_l, list):
        for row in res_l:
            ledger_list.append({
                "id": row["id"], "date": str(row["tx_date"]), "code": row.get("code", "-"),
                "description": row["description"], "account_from": row["account_from"],
                "account_to": row["account_to"], "amount": float(row["amount"]),
                "tags": row.get("tags", ""), "comment": row.get("comment", "")
            })
        
    for oid, o in orders_dict.items():
        if o["p_ref"] and o["p_ref"] in projects_dict:
            projects_dict[o["p_ref"]]["amt_with_tax_total"] += o["amt_with_tax"]
            
    for c in collections_list:
        if c["o_ref"] in orders_dict:
            orders_dict[c["o_ref"]]["collect_total"] += c["amount"]
            p_ref = orders_dict[c["o_ref"]]["p_ref"]
            if p_ref and p_ref in projects_dict:
                projects_dict[p_ref]["collect_total"] += c["amount"]

    for r in revenues_list:
        if r["o_ref"] in orders_dict:
            orders_dict[r["o_ref"]]["revenue_total"] += r["amount"]

    return projects_dict, orders_dict, collections_list, revenues_list, ledger_list

st.cache_data.clear()
projects, orders, collections, revenues, ledgers = load_db_data()

def get_quarter(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.year, f"Q{(dt.month - 1) // 3 + 1}"
    except: return None, None

def make_csv_buffer(df):
    if df.empty: return None
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, encoding='utf-8-sig')
    return buffer.getvalue()

existing_accounts = set(BASE_ACCOUNTS)
for l in ledgers:
    if l["account_from"]: existing_accounts.add(l["account_from"])
    if l["account_to"]: existing_accounts.add(l["account_to"])
DYNAMIC_ACCOUNT_LIST = sorted(list(existing_accounts))

# ==========================================
# 2. 侧边栏导航控制及 KPI 目标动态配置中心
# ==========================================
st.sidebar.title("⚡ 战术数字座舱")
st.sidebar.markdown("💡 **核心内核**：`🟢 Supabase REST 高速安全通道`")

system_current_year = datetime.now().year

with st.sidebar.expander("⚙️ 运营大屏 KPI 智能目标拦截线"):
    st.markdown(f"控制核心 **{system_current_year}** 年的硬性考核红线：")
    cfg_rev = st.number_input("年度确收目标(元)", min_value=0.0, value=5000000.0, step=50000.0)
    cfg_col = st.number_input("年度回款目标(元)", min_value=0.0, value=4500000.0, step=50000.0)

menu = st.sidebar.radio("核心系统导航", ["📊 业绩与KPI大屏", "📝 综合业务台账", "➕ 业务数据维护中心", "🏦 复式财务管理中心", "💾 往年库容释放与数据导出"])

# ==========================================
# 3. 页面 1: 业绩与KPI大屏
# ==========================================
if menu == "📊 业绩与KPI大屏":
    st.title("📡 销售战绩与年/季双轨 KPI 战略大屏")
    current_year = system_current_year 
    
    annual_revenue_done = sum(r["amount"] for r in revenues if datetime.strptime(r["date"], "%Y-%m-%d").year == current_year)
    annual_collection_done = sum(c["amount"] for c in collections if datetime.strptime(c["date"], "%Y-%m-%d").year == current_year)
    
    rev_annual_rate = (annual_revenue_done / cfg_rev) if cfg_rev > 0 else 0.0
    col_annual_rate = (annual_collection_done / cfg_col) if cfg_col > 0 else 0.0

    st.markdown(f"### 📊 {current_year}年度数字雷达 KPI 观测站")
    
    # 科技感霓虹毛玻璃卡片渲染逻辑
    def render_tech_metric(title, value, sub_text="", border_color="#30363D", text_color="#58A6FF"):
        return f"""
        <div style="background: rgba(22, 27, 34, 0.8); padding:16px; border-radius:8px; border:1px solid {border_color}; box-shadow: 0 0 10px rgba(0,0,0,0.5); text-align:center; min-height:110px;">
            <p style="margin:0; font-size:13px; color:#8B949E; font-weight:600; letter-spacing:0.5px;">{title}</p>
            <h3 style="margin:8px 0; font-size:20px; color:{text_color}; font-family:'Courier New', monospace; font-weight:bold; white-space:nowrap;">{value}</h3>
            <p style="margin:0; font-size:12px; color:#58A6FF; font-weight:bold; font-family:sans-serif;">{sub_text}</p>
        </div>
        """
        
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.markdown(render_tech_metric(f"{current_year}年度确收指标", f"¥{cfg_rev:,.2f}", "", "#388BFD"), unsafe_allow_html=True)
    m_col2.markdown(render_tech_metric("大盘当前已确收", f"¥{annual_revenue_done:,.2f}", f"🎯 达成进度 {rev_annual_rate*100:.1f}%", "#238636", "#39D353"), unsafe_allow_html=True)
    m_col3.markdown(render_tech_metric(f"{current_year}年度到账目标", f"¥{cfg_col:,.2f}", "", "#8957E5"), unsafe_allow_html=True)
    m_col4.markdown(render_tech_metric("大盘累计资金进账", f"¥{annual_collection_done:,.2f}", f"⚡ 达成进度 {col_annual_rate*100:.1f}%", "#A371F7", "#D2A8FF"), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"**🟢 {current_year}年度确认收入 KPI 深度推进链:**")
    st.progress(min(1.0, rev_annual_rate))
    st.markdown(f"**⚡ {current_year}年度实际回款 KPI 资金链脉搏:**")
    st.progress(min(1.0, col_annual_rate))
    
    st.markdown("---")
    st.markdown("### 🗂️ 跨断代全景历史业绩演进脉络")
    
    history_list = []
    for yr, data in HISTORY_ARCHIVE.items():
        history_list.append({"年份": f"{yr}年", "确认收入": float(data["revenue"]), "到账回款": float(data["collection"])})
    history_list.append({"年份": f"{current_year}年(实时)", "确认收入": float(annual_revenue_done), "到账回款": float(annual_collection_done)})
    
    df_history_chart = pd.DataFrame(history_list)
    df_history_chart["确认收入"] = pd.to_numeric(df_history_chart["确认收入"]).fillna(0.0)
    df_history_chart["到账回款"] = pd.to_numeric(df_history_chart["到账回款"]).fillna(0.0)
    
    try:
        fig_history = px.bar(
            df_history_chart, x="年份", y=["确认收入", "到账回款"],
            barmode="group", text_auto='.2s',
            title="📊 多跨度年度营收/进账全景历史推演（自动并入本地冷数据区）",
            template="plotly_dark"
        )
        fig_history.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color="#C9D1D9")
        st.plotly_chart(fig_history, use_container_width=True)
    except: st.info("📊 演进图深度加载中...")
    
    st.markdown("---")
    st.markdown("### ⏱️ 战术季度 KPI 穿透分析仪")
    selected_q = st.selectbox("请锚定需要复盘审查的特定精细季度：", [f"{current_year}年 Q1 (1-3月)", f"{current_year}年 Q2 (4-6月)", f"{current_year}年 Q3 (7-9月)", f"{current_year}年 Q4 (10-12月)"], index=2)
    target_q_code = selected_q.split(" ")[1]

    q_revenue_done = 0.0
    q_collection_done = 0.0
    for r in revenues:
        y, q = get_quarter(r["date"])
        if y == current_year and q == target_q_code: q_revenue_done += r["amount"]
    for c in collections:
        y, q = get_quarter(c["date"])
        if y == current_year and q == target_q_code: q_collection_done += c["amount"]

    q_box1, q_box2, q_box3 = st.columns(3)
    q_box1.markdown(f"<div style='background: #161B22; padding:15px; border-left:4px solid #58A6FF; border-radius:4px;'><h4>📌 考察周期</h4><h2 style='color:#58A6FF; font-size:18px; margin:0;'>{selected_q}</h2></div>", unsafe_allow_html=True)
    q_box2.markdown(f"<div style='background: #161B22; padding:15px; border-left:4px solid #39D353; border-radius:4px;'><h4>📈 季度确认收入</h4><h2 style='color:#39D353; font-size:18px; margin:0;'>¥{q_revenue_done:,.2f}</h2></div>", unsafe_allow_html=True)
    q_box3.markdown(f"<div style='background: #161B22; padding:15px; border-left:4px solid #D2A8FF; border-radius:4px;'><h4>🏦 季度到账回款</h4><h2 style='color:#D2A8FF; font-size:18px; margin:0;'>¥{q_collection_done:,.2f}</h2></div>", unsafe_allow_html=True)

    if q_revenue_done > 0 or q_collection_done > 0:
        fig_q = px.bar(x=["季度确收数据", "季度回款进账"], y=[q_revenue_done, q_collection_done], color=["确收", "回款"], text_auto='.2f', template="plotly_dark", title=f"📡 {selected_q} 确收/回款对称雷达")
        fig_q.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_q, use_container_width=True)

# ==========================================
# 4. 页面 2: 综合业务台账
# ==========================================
elif menu == "📝 综合业务台账":
    st.title("🖥️ 综合业务拉通一体化控制台明细")
    st.markdown("### 🎛️ 过滤与宏观拦截条件")
    f_col1, f_col2, f_col3 = st.columns(3)
    
    unique_projects = ["全部项目"] + sorted(list(set(p["name"] for p in projects.values())))
    unique_provinces = ["全部省份"] + sorted(list(set(o["province"] for o in orders.values())))
    
    selected_project = f_col1.selectbox("🎯 关联框架项目狙击：", unique_projects)
    selected_province = f_col2.selectbox("📍 订单所属省份雷达：", unique_provinces)
    
    today = date.today()
    start_of_year = date(today.year, 1, 1)
    date_range = f_col3.date_input("📅 锁定业务周期范围：", value=(start_of_year, today))
    st.markdown("---")

    st.subheader("📡 前期售前 / 项目框架水位安全预警")
    project_rows = []
    for pid, p in projects.items():
        if selected_project != "全部项目" and p["name"] != selected_project: continue
        ratio = (p["amt_with_tax_total"] / p["target"]) if p["target"] > 0 else 0.0
        warning_status = "✅ 安全范围"
        if ratio >= 1.0: warning_status = "🚨 爆仓！订单已突破框架极限"
        elif ratio >= 0.8: warning_status = "⚠️ 告急！消耗度超80%"
        project_rows.append({"项目ID": p["id"], "项目/框架名称": p["name"], "客户简称": p["client"], "框架标的总额": p["target"], "已下正式订单含税总额": p["amt_with_tax_total"], "框架额度消耗比例": f"{ratio*100:.1f}%", "框架安全水位预警": warning_status, "开标/创建日期": p["bid_date"], "当前状态": p["stage"]})
    if project_rows:
        df_p_view = pd.DataFrame(project_rows)
        # 在黑客暗调下，让超标高亮更显眼
        st.dataframe(df_p_view.style.map(lambda v: "background-color: #4A1519; color: #FF6B6B; font-weight: bold;" if "🚨" in str(v) else ("background-color: #3C2B0A; color: #FFD43B; font-weight: bold;" if "⚠️" in str(v) else ""), subset=["框架安全水位预警"]), use_container_width=True, hide_index=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.subheader("🤝 已中标订单及到货【确收/回款】双驱生命周期流水")
    order_rows = []
    for oid, o in orders.items():
        related_p_name = projects[o["p_ref"]]["name"] if o["p_ref"] and o["p_ref"] in projects else "历史老账/无需补录项目"
        if selected_project != "全部项目" and related_p_name != selected_project: continue
        if selected_province != "全部省份" and o["province"] != selected_province: continue
        try:
            o_date_obj = datetime.strptime(o["date"], "%Y-%m-%d").date()
            if isinstance(date_range, tuple) and len(date_range) == 2:
                if not (date_range[0] <= o_date_obj <= date_range[1]): continue
        except: pass
            
        uncollected = max(0.0, o["amt_with_tax"] - o["collect_total"])
        unrevenue = max(0.0, o["amt_with_tax"] - o["revenue_total"]) 
        order_rows.append({"订单编号": o["id"], "订单下发日期": o["date"], "区域省份": o["province"], "客户简称": o["client"], "订购产品明细": o["product"], "接单含税金额": o["amt_with_tax"], "订单项目名称": o["order_p_name"], "💡 累计已确认收入": o["revenue_total"], "⏳ 尚未收货未确收": unrevenue, "累计已回款": o["collect_total"], "待追收尾款": uncollected, "关联源头框架项目": related_p_name})
        
    if order_rows:
        df_o_view = pd.DataFrame(order_rows)
        column_order = ["订单编号", "订单下发日期", "区域省份", "客户简称", "订购产品明细", "接单含税金额", "💡 累计已确认收入", "⏳ 尚未收货未确收", "累计已回款", "待追收尾款", "关联源头框架项目"]
        df_o_view = df_o_view.reindex(columns=column_order)
        s1, s2, s3 = st.columns(3)
        s1.metric("筛选接单核心总规模", f"¥{df_o_view['接单含税金额'].sum():,.2f}")
        s2.metric("开网收货已交付确收", f"¥{df_o_view['💡 累计已确认收入'].sum():,.2f}")
        s3.metric("整个大盘待追踪尾款", f"¥{df_o_view['待追收尾款'].sum():,.2f}")
        st.dataframe(df_o_view, use_container_width=True, hide_index=True)

# ==========================================
# 5. 页面 3: 业务数据维护中心
# ==========================================
elif menu == "➕ 业务数据维护中心":
    st.title("🔧 核心业务数据全生命周期维护基地")
    op_type = st.radio("请选择核心维护指令类型：", ["🆕 录入全新数据", "⚙️ 修改已有信息 (数据回显覆写)"], horizontal=True)
    st.markdown("---")

    if op_type == "🆕 录入全新数据":
        sub_step = st.radio("请选择录入的业务阶段：", ["🎯 项目前期录入", "🤝 中标订单录入", "📈 确认收入到货登记", "🏦 回款销账登记"], horizontal=True) 
        st.markdown("---")

        if sub_step == "🎯 项目前期录入":
            with st.form("p_form", clear_on_submit=True):
                p_name = st.text_input("1. 项目框架/名称 *")
                p_client = st.text_input("2. 客户简称 *")
                p_target = st.number_input("3. 项目框架标的额 (元) *", min_value=0.0, step=10000.0)
                p_stage = st.selectbox("4. 项目阶段 *", PROJECT_STAGES)
                p_bid_date = st.date_input("5. 开标/签署时间 *", value=datetime.now()).strftime("%Y-%m-%d")
                if st.form_submit_button("⚡ 签署并同步至 Supabase 云集群"):
                    if not p_name or not p_client: st.error("❌ 项目名称和客户简称为必填项！")
                    else:
                        payload = {"id": f"PRJ{int(datetime.now().timestamp())}", "name": p_name, "client": p_client, "target": p_target, "stage": p_stage, "bid_date": p_bid_date}
                        res = requests.post(f"{SB_URL}/rest/v1/projects", headers=HEADERS, json=payload, timeout=5)
                        if res.status_code in [200, 201]: st.success("✔️ 框架项目入库完成！"); st.rerun()

        elif sub_step == "🤝 中标订单录入":
            if not projects: st.warning("⚠️ 暂无前置项目！")
            else:
                p_opts = {f"{p['name']} ({p['client']})": pid for pid, p in projects.items()}
                sel_p = st.selectbox("11. 关联源头框架项目 *", list(p_opts.keys()))
                o_id = st.text_input("1. 客户正式订单号 *")
                o_date = st.date_input("2. 订单下发日期 *", value=datetime.now()).strftime("%Y-%m-%d")
                o_province = st.text_input("3. 区域省份 *")
                o_client = st.text_input("4. 客户简称 *")
                o_product = st.text_input("5. 订购产品明细 *")
                cp, cr, cq = st.columns(3)
                price = cp.number_input("6. 单价(不含税/元) *", min_value=0.0)
                tax_rate = cr.number_input("7. 税率 *", min_value=0.0, max_value=1.0, value=0.13)
                qty = cq.number_input("8. 数量 *", min_value=1, value=1)
                amt_no_tax = price * qty
                amt_with_tax = amt_no_tax * (1 + tax_rate)
                st.info(f"📊 自动核税预览含税额: ¥{amt_with_tax:,.2f}")
                o_p_name = st.text_input("12. 对应订单项目名称 *")

                if st.button("⚡ 锁定订单下发"):
                    if not o_id or not o_province or not o_client or not o_product or not o_p_name: st.error("❌ 请完整填写必填字段！")
                    else:
                        pid_ref = p_opts[sel_p]
                        requests.patch(f"{SB_URL}/rest/v1/projects?id=eq.{pid_ref}", headers=HEADERS, json={"stage": "已中标"}, timeout=5)
                        o_payload = {"id": o_id, "project_ref": pid_ref, "order_date": o_date, "province": o_province, "client": o_client, "product": o_product, "price_no_tax": price, "tax_rate": tax_rate, "quantity": qty, "amt_no_tax": amt_no_tax, "amt_with_tax": amt_with_tax, "order_p_name": o_p_name}
                        res = requests.post(f"{SB_URL}/rest/v1/orders", headers=HEADERS, json=o_payload, timeout=5)
                        if res.status_code in [200, 201]: st.success("✔️ 正式接单入库成功！"); st.rerun()

        elif sub_step == "📈 确认收入到货登记":
            if not orders: st.warning("⚠️ 系统内暂无订单。")
            else:
                with st.form("r_form", clear_on_submit=True):
                    o_opts = {f"订单:{oid} (含税额:¥{o['amt_with_tax']} | 已确收:¥{o['revenue_total']})": oid for oid, o in orders.items()}
                    sel_o = st.selectbox("1. 选择要登记确收的订单号 *", list(o_opts.keys())); oid_final = o_opts[sel_o]
                    r_amt = st.number_input("2. 本次客户签收/确认收入金额 (元) *", min_value=0.0)
                    r_date = st.date_input("3. 实际确认收入到货日期 *", value=datetime.now()).strftime("%Y-%m-%d")
                    if st.form_submit_button("⚡ 拦截签收并确收"):
                        if r_amt <= 0: st.error("❌ 金额需大于0元！")
                        else:
                            res = requests.post(f"{SB_URL}/rest/v1/revenues", headers=HEADERS, json={"order_ref": oid_final, "amount": r_amt, "revenue_date": r_date}, timeout=5)
                            if res.status_code in [200, 201]: st.success("🎉 签收确收流水已记录！"); st.rerun()

        elif sub_step == "🏦 回款销账登记":
            is_legacy_history = st.checkbox("⏳ 本次是核销【多年前的陈年遗留老账/挂账】")
            with st.form("c_form", clear_on_submit=True):
                if not is_legacy_history:
                    if not orders: st.warning("⚠️ 系统内暂无订单。"); st.form_submit_button("不可提交", disabled=True); raw_oid_input = ""
                    else:
                        o_opts = {f"订单:{oid} (尾款:¥{o['amt_with_tax'] - o['collect_total']:.2f})": oid for oid, o in orders.items()}
                        selected_order_labels = st.multiselect("1. 请选择本次合并结算包含的订单号（支持下拉多选）*", list(o_opts.keys()))
                        raw_oid_input = ",".join([o_opts[lbl] for lbl in selected_order_labels])
                else: raw_oid_input = st.text_input("1. 手动精确输入历史客户订单号 *")

                c_amt = st.number_input("2. 本次财务实际到账总回款额 (元) *", min_value=0.0)
                c_date = st.date_input("3. 实际回款进账日期 *", value=datetime.now()).strftime("%Y-%m-%d")
                c_invoice = st.text_input("4. 关联销账发票号 / 财务凭证号 (选填)")

                if st.form_submit_button("⚡ 执行智能销账"):
                    cleaned_input = str(raw_oid_input).strip()
                    if not cleaned_input: st.error("❌ 必须选择或填写至少一个订单号！")
                    elif c_amt <= 0: st.error("❌ 回款金额需大于0元！")
                    else:
                        target_orders = [x.strip() for x in cleaned_input.split(",") if x.strip()]
                        if len(target_orders) == 1:
                            single_oid = target_orders[0]
                            if is_legacy_history and (single_oid not in orders):
                                hedge_payload = {"id": single_oid, "project_ref": None, "order_date": c_date, "province": "历史老账归档区", "client": "历史长账龄客户", "product": "跨年历史账目结转款", "price_no_tax": c_amt, "tax_rate": 0.0, "quantity": 1, "amt_no_tax": c_amt, "amt_with_tax": c_amt, "order_p_name": "多年前老订单挂账"}
                                requests.post(f"{SB_URL}/rest/v1/orders", headers=HEADERS, json=hedge_payload, timeout=5)
                            c_payload = {"order_ref": single_oid, "amount": c_amt, "collection_date": c_date, "invoice_no": c_invoice if c_invoice else "-"}
                            requests.post(f"{SB_URL}/rest/v1/collections", headers=HEADERS, json=c_payload, timeout=5)
                        else:
                            debt_dict = {}
                            total_debt = 0.0
                            for target_id in target_orders:
                                if target_id in orders: current_debt = max(0.0, orders[target_id]["amt_with_tax"] - orders[target_id]["collect_total"])
                                else: current_debt = 0.0
                                debt_dict[target_id] = current_debt; total_debt += current_debt
                            remaining_pool = c_amt
                            for idx, target_id in enumerate(target_orders):
                                if idx == len(target_orders) - 1: split_amt = remaining_pool
                                else:
                                    if total_debt > 0: split_amt = round(c_amt * (debt_dict[target_id] / total_debt), 2)
                                    else: split_amt = round(c_amt / len(target_orders), 2)
                                    remaining_pool -= split_amt
                                if target_id not in orders:
                                    requests.post(f"{SB_URL}/rest/v1/orders", headers=HEADERS, json={"id": target_id, "project_ref": None, "order_date": c_date, "province": "合并结算老账区", "client": "运营商历史长账", "product": "历史批量并单核销款", "price_no_tax": split_amt, "tax_rate": 0.0, "quantity": 1, "amt_no_tax": split_amt, "amt_with_tax": split_amt, "order_p_name": "批量遗留老账合并"}, timeout=5)
                                each_payload = {"order_ref": target_id, "amount": split_amt, "collection_date": c_date, "invoice_no": f"{c_invoice}(合并拆分)" if c_invoice else "合并拆分"}
                                requests.post(f"{SB_URL}/rest/v1/collections", headers=HEADERS, json=each_payload, timeout=5)
                        st.success("🎉 复合长账龄流水平摊拦截分流成功！"); st.rerun()

    elif op_type == "⚙️ 修改已有信息 (数据回显覆写)":
        edit_target = st.radio("请选择需要修改的内容类型：", ["🎯 修改框架项目", "🤝 修改订单明细"], horizontal=True)
        st.markdown("---")
        if edit_target == "🎯 修改框架项目":
            if not projects: st.info("云端暂无数据可修改")
            else:
                p_edit_opts = {f"{p['name']} ({p['client']})": pid for pid, p in projects.items()}
                sel_edit_p = st.selectbox("请选择要修改的框架项目：", list(p_edit_opts.keys())); pid_edit = p_edit_opts[sel_edit_p]; old_p = projects[pid_edit]
                up_p_name = st.text_input("项目框架/名称", value=old_p["name"])
                up_p_client = st.text_input("客户简称", value=old_p["client"])
                up_p_target = st.number_input("框架标的总额(元)", min_value=0.0, value=old_p["target"])
                up_p_stage = st.selectbox("项目进展状态", PROJECT_STAGES, index=PROJECT_STAGES.index(old_p["stage"]))
                try: old_dt = datetime.strptime(old_p["bid_date"], "%Y-%m-%d")
                except: old_dt = datetime.now()
                up_p_date = st.date_input("开标时间", value=old_dt).strftime("%Y-%m-%d")
                p_edit_reason = st.text_area("🔧 请输入本次项目调整/修正的原因备注 * (审计强痕迹)")
                if st.button("💾 强审计回写项目"):
                    if not p_edit_reason.strip(): st.error("❌ 必须填写修改原因！")
                    else:
                        trace_stamp = f" [修改痕迹 {datetime.now().strftime('%Y-%m-%d')}: {p_edit_reason.strip()}]"
                        up_payload = {"name": up_p_name, "client": up_p_client, "target": up_p_target, "stage": up_p_stage + trace_stamp, "bid_date": up_p_date}
                        res = requests.patch(f"{SB_URL}/rest/v1/projects?id=eq.{pid_edit}", headers=HEADERS, json=up_payload, timeout=5)
                        if res.status_code in [200, 204]: st.success("🎉 项目覆写成功！"); st.rerun()

        elif edit_target == "🤝 修改订单明细":
            if not orders: st.info("云端暂无订单数据可修改")
            else:
                o_edit_opts = {f"订单号:{oid} | {o['order_p_name']}": oid for oid, o in orders.items()}
                sel_edit_o = st.selectbox("请选择要更正的正式订单：", list(o_edit_opts.keys())); oid_edit = o_edit_opts[sel_edit_o]; old_o = orders[oid_edit]
                up_o_province = st.text_input("省份", value=old_o["province"])
                up_o_client = st.text_input("客户简称", value=old_o["client"])
                up_o_product = st.text_input("订单产品", value=old_o["product"].split(" [修改痕迹")[0])
                up_o_p_name = st.text_input("订单项目名称", value=old_o["order_p_name"])
                cep, cer, ceq = st.columns(3)
                up_price = cep.number_input("单价(不含税)", min_value=0.0, value=old_o["price_no_tax"])
                up_tax_rate = cer.number_input("税率", min_value=0.0, max_value=1.0, value=old_o["tax_rate"])
                up_qty = ceq.number_input("数量", min_value=1, value=int(old_o["quantity"]))
                new_no_tax = up_price * up_qty
                new_tax_in = new_no_tax * (1 + up_tax_rate)
                try: old_o_dt = datetime.strptime(old_o["date"], "%Y-%m-%d")
                except: old_o_dt = datetime.now()
                up_o_date = st.date_input("订单日期", value=old_o_dt).strftime("%Y-%m-%d")
                o_edit_reason = st.text_area("🔧 请输入本次订单调整/修正的原因备注 * (审计强痕迹)")
                if st.button("💾 强审计回写订单"):
                    if not o_edit_reason.strip(): st.error("❌ 必须填写修改原因！")
                    else:
                        trace_stamp = f" [修改痕迹 {datetime.now().strftime('%Y-%m-%d')}: {o_edit_reason.strip()}]"
                        up_o_payload = {"province": up_o_province, "client": up_o_client, "product": up_o_product + trace_stamp, "order_p_name": up_o_p_name, "price_no_tax": up_price, "tax_rate": up_tax_rate, "quantity": up_qty, "amt_no_tax": new_no_tax, "amt_with_tax": new_tax_in, "order_date": up_o_date}
                        res = requests.patch(f"{SB_URL}/rest/v1/orders?id=eq.{oid_edit}", headers=HEADERS, json=up_o_payload, timeout=5)
                        if res.status_code in [200, 204]: st.success("🎉 订单明细更新完成！"); st.rerun()

# ==========================================
# 6. 🏦 复式财务管理中心
# ==========================================
elif menu == "🏦 复式财务管理中心":
    st.title("🏛️ 极客多维复式财务账本控制台 (hledger 理念版)")
    st.markdown("精密的借贷流平衡校验，支持一笔交易无上限拆分至多个来源与去向科目，完全自由贴标签。")
    
    f_tabs = st.tabs(["📊 资金网络多维雷达", "📜 复式分录明细长卷 (Journal)", "✍️ 多账户原子拆分记账"])
    
    with f_tabs[0]:
        st.subheader("📡 开销构成与自定义 Tag 深度拦截仪")
        if not ledgers: st.info("暂无复式记账明细。")
        else:
            df_l = pd.DataFrame(ledgers)
            df_exp = df_l[df_l["account_to"].str.startswith("Expenses:")]
            sc1, sc2 = st.columns(2)
            with sc1:
                st.markdown("#### 🍕 动态开销分类树占比")
                if not df_exp.empty:
                    fig_pie_l = px.pie(df_exp, names="account_to", values="amount", hole=0.4, template="plotly_dark", title="动态 Expenses 支出模型")
                    fig_pie_l.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_pie_l, use_container_width=True)
                else: st.text("暂无 Expenses 费用数据支出。")
            with sc2:
                st.markdown("#### 🏷️ 自由 Tags 专项穿透柱状图")
                all_tag_stats = {}
                for _, row in df_l.iterrows():
                    raw_tags = str(row["tags"]).replace(",", " ").replace("，", " ").split()
                    for t in raw_tags:
                        t = t.strip().lower()
                        if t: all_tag_stats[t] = all_tag_stats.get(t, 0.0) + row["amount"]
                if all_tag_stats:
                    df_tags = pd.DataFrame(list(all_tag_stats.items()), columns=["自定义Tag标签", "累计涉及金额(元)"]).sort_values(by="累计涉及金额(元)", ascending=False)
                    fig_tag_bar = px.bar(df_tags, x="自定义Tag标签", y="累计涉及金额(元)", text_auto=True, template="plotly_dark", title="自由标签捕获明细")
                    fig_tag_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_tag_bar, use_container_width=True)
                else: st.text("大盘交易目前未打上任何 Tag 标签。")

    with f_tabs[1]:
        st.subheader("📖 标定 Journal 分录流水长卷")
        if ledgers:
            df_journal = pd.DataFrame(ledgers)[["date", "description", "account_from", "account_to", "amount", "tags", "comment"]]
            df_journal.columns = ["交易日期", "交易描述", "资金来源 (贷/From)", "资金去向 (借/To)", "金额(元)", "自由Tags", "详细备注"]
            st.dataframe(df_journal, use_container_width=True, hide_index=True)
        else: st.info("控制舱内未检测到记账流水。")

    with f_tabs[2]:
        st.subheader("✍️ 录入原子复合分录（极致对等平衡校验）")
        l_date = st.date_input("1. 设定交易日期", value=datetime.now()).strftime("%Y-%m-%d")
        l_desc = st.text_input("2. 标定交易事务/商户 *", placeholder="例如：加油站充值(主卡+积分+自费分拆支付)")
        st.markdown("---")
        st.markdown("### 🧩 多源借贷账户智能配平拆分")
        if "legs_count" not in st.session_state: st.session_state.legs_count = 2
        def add_leg(): st.session_state.legs_count += 1
        def remove_leg():
            if st.session_state.legs_count > 2: st.session_state.legs_count -= 1

        leg_data = []
        for i in range(st.session_state.legs_count):
            st.markdown(f"**微型分录节点 #{i+1} :**")
            c1, c2, c3, c4 = st.columns([2, 3, 3, 2])
            direction = c1.selectbox(f"交易动向#{i+1}", ["资金去向 (借/To/支出或资产增加)", "资金来源 (贷/From/资产减少或收入)"], key=f"dir_{i}")
            acc_select = c2.selectbox(f"锁定既有科目树#{i+1}", ["[+ 手工输入自生长全新账户]"] + DYNAMIC_ACCOUNT_LIST, key=f"acc_sel_{i}")
            if acc_select == "[+ 手工输入自生长全新账户]":
                acc_final = c3.text_input(f"✍️ 自生长账户节点命名#{i+1}", placeholder="例如 Expenses:Food:Snacks", key=f"acc_raw_{i}")
            else:
                acc_final = acc_select
                c3.info(f"已锁定节点: `{acc_final}`")
            amt = c4.number_input(f"份额金额(元)#{i+1}", min_value=0.0, step=10.0, key=f"amt_{i}")
            leg_data.append({"direction": direction, "account": acc_final, "amount": amt})

        b_col1, b_col2, _ = st.columns([2, 2, 8])
        b_col1.button("➕ 扩增配平肢体/账户拆分", on_click=add_leg)
        b_col2.button("➖ 剔除末尾节点", on_click=remove_leg)

        st.markdown("---")
        total_to = sum(item["amount"] for item in leg_data if "去向" in item["direction"])
        total_from = sum(item["amount"] for item in leg_data if "来源" in item["direction"])
        balance_gap = round(total_to - total_from, 2)
        
        st.markdown(f"### 🧮 借贷底层平账实时审计模块:")
        ck1, ck2, ck3 = st.columns(3)
        ck1.metric("资金去向(借/To)总计", f"¥{total_to:,.2f}")
        ck2.metric("资金来源(贷/From)总计", f"¥{total_from:,.2f}")
        if balance_gap == 0: ck3.success("✅ 借贷零误差，准许入账！")
        else: ck3.error(f"❌ 借贷失衡差额: ¥{balance_gap:,.2f}")
            
        st.markdown("---")
        l_tags = st.text_input("4. 自由打标 Tag 空间 (多个标签空客或逗号隔开)", placeholder="例如: child 装修 报销")
        l_comment = st.text_input("5. 分录长备注说明")
        
        if st.button("🚀 复合原子流水强行注入云端集群", disabled=(balance_gap != 0 or not l_desc)):
            if not l_desc: st.error("❌ 必须填写交易描述！")
            else:
                success_flag = True
                to_legs = [x for x in leg_data if "去向" in x["direction"] and x["amount"] > 0]
                from_legs = [x for x in leg_data if "来源" in x["direction"] and x["amount"] > 0]
                
                payload_list = []
                for t_leg in to_legs:
                    t_acc = t_leg["account"]
                    t_amt = t_leg["amount"]
                    for f_leg in from_legs:
                        if t_amt <= 0: break
                        f_acc = f_leg["account"]
                        f_amt = f_leg["amount"]
                        if f_amt <= 0: continue
                        match_amt = min(t_amt, f_amt)
                        t_amt -= match_amt
                        f_leg["amount"] -= match_amt
                        payload_list.append({"tx_date": l_date, "description": l_desc, "account_from": f_acc, "account_to": t_acc, "amount": match_amt, "tags": l_tags.strip(), "comment": l_comment})

                for payload in payload_list:
                    res = requests.post(f"{SB_URL}/rest/v1/ledger_entries", headers=HEADERS, json=payload, timeout=5)
                    if res.status_code not in [200, 201]: success_flag = False
                if success_flag:
                    st.success("🎉 复式记账分布式拆流分录成功入库！")
                    st.rerun()
                else: st.error("集群响应异常，写入中止。")

# ==========================================
# 7. 💾 往年库容释放与数据导出中心
# ==========================================
elif menu == "💾 往年库容释放与数据导出":
    st.title("💾 库容熔断释放与本地冷冷数据备份中枢")
    
    st.subheader("🏦 财务全量专项：全量复式 Journal 流水备份导入口")
    st.markdown("不受业务年度锁限制，一键倾倒所有财务流水用于本地离线 MySQL 回填或高级数据建模。")
    if ledgers:
        df_all_ledgers = pd.DataFrame(ledgers)[["id", "date", "code", "description", "account_from", "account_to", "amount", "tags", "comment"]]
        df_all_ledgers.columns = ["id", "tx_date", "code", "description", "account_from", "account_to", "amount", "tags", "comment"]
        csv_all_l = make_csv_buffer(df_all_ledgers)
        if csv_all_l:
            st.download_button(label=f"📥 拉取全量财务明细长卷 (共 {len(df_all_ledgers)} 分录).csv", data=csv_all_l, file_name="mysql_ledger_entries_all.csv", mime="text/csv", type="primary")
    else: st.info("📊 没有检测到财务账本留存。")
        
    st.markdown("---")
    
    st.subheader("📅 销售阶段数据专项：年度冷归档与清障清空")
    export_year = st.selectbox("请确定要清理的业务历史年份：", list(range(system_current_year-3, system_current_year+2)), index=3)
    st.write(f"📡 动态扫描云数据库内 `{export_year}` 销售大盘容量...")

    p_exported = [{"id": p["id"], "name": p["name"], "client": p["client"], "target": p["target"], "stage": p["stage"], "bid_date": p["bid_date"]} for p in projects.values() if datetime.strptime(p["bid_date"], "%Y-%m-%d").year == export_year]
    o_exported = [{"id": o["id"], "project_ref": o["p_ref"], "order_date": o["date"], "province": o["province"], "client": o["client"], "product": o["product"], "price_no_tax": o["price_no_tax"], "tax_rate": o["tax_rate"], "quantity": o["quantity"], "amt_no_tax": o["amt_no_tax"], "amt_with_tax": o["amt_with_tax"], "order_p_name": o["order_p_name"]} for o in orders.values() if datetime.strptime(o["date"], "%Y-%m-%d").year == export_year]
    c_exported = [{"order_ref": row["o_ref"], "amount": row["amount"], "collection_date": row["date"], "invoice_no": row["invoice_no"]} for row in collections if datetime.strptime(row["date"], "%Y-%m-%d").year == export_year]
    r_exported = [{"order_ref": row["o_ref"], "amount": row["amount"], "revenue_date": row["date"]} for row in revenues if datetime.strptime(row["date"], "%Y-%m-%d").year == export_year]

    df_export_p = pd.DataFrame(p_exported); df_export_o = pd.DataFrame(o_exported); df_export_c = pd.DataFrame(c_exported); df_export_r = pd.DataFrame(r_exported)

    dl_col1, dl_col2, dl_col3, dl_col4 = st.columns(4)
    with dl_col1:
        csv_p = make_csv_buffer(df_export_p)
        if csv_p: st.download_button(f"📥 下载 projects_{export_year}.csv", csv_p, f"mysql_projects_{export_year}.csv", "text/csv")
    with dl_col2:
        csv_o = make_csv_buffer(df_export_o)
        if csv_o: st.download_button(f"📥 下载 orders_{export_year}.csv", csv_o, f"mysql_orders_{export_year}.csv", "text/csv")
    with dl_col3:
        csv_c = make_csv_buffer(df_export_c)
        if csv_c: st.download_button(f"📥 下载 collections_{export_year}.csv", csv_c, f"mysql_collections_{export_year}.csv", "text/csv")
    with dl_col4:
        csv_r = make_csv_buffer(df_export_r)
        if csv_r: st.download_button(f"📥 下载 revenues_{export_year}.csv", csv_r, f"mysql_revenues_{export_year}.csv", "text/csv")

    st.markdown("---")
    if export_year >= system_current_year:
        st.error(f"🔒 **核心系统防误删硬熔断**：当前或未来活跃年度数据已锁定，禁止擦除！")
    else:
        st.warning(f"⚠️ 触发历史归档指令（{export_year} 年历史老账）物理删除许可。")
        confirm_downloaded = st.checkbox(f"🔴 **我确认：上面对应的销售明细数据我已妥善离线保存并核对完毕！**")
        if confirm_downloaded:
            if st.button(f"🗑️ 彻底物理粉碎云端 {export_year} 历史销售挂账", type="primary"):
                requests.delete(f"{SB_URL}/rest/v1/projects?bid_date=gte.{export_year}-01-01&bid_date=lte.{export_year}-12-31", headers=HEADERS, timeout=5)
                requests.delete(f"{SB_URL}/rest/v1/orders?order_date=gte.{export_year}-01-01&order_date=lte.{export_year}-12-31", headers=HEADERS, timeout=5)
                requests.delete(f"{SB_URL}/rest/v1/collections?collection_date=gte.{export_year}-01-01&collection_date=lte.{export_year}-12-31", headers=HEADERS, timeout=5)
                requests.delete(f"{SB_URL}/rest/v1/revenues?revenue_date=gte.{export_year}-01-01&revenue_date=lte.{export_year}-12-31", headers=HEADERS, timeout=5)
                st.success("老销售业务数据已被安全擦除粉碎，库容已释放！"); st.rerun()
