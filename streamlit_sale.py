import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import requests
import io

# ==========================================
# 🎨 1. 全量视觉重构：YouTube/X 极高对比度扁平化科技主题 CSS
# ==========================================
st.set_page_config(page_title="通信销售与复式财务全能云工作台", layout="wide", page_icon="📈")

# 核心现代配色方案
X_PRIMARY = "#1D9BF0"      # X 科技蓝
X_BG_MAIN = "#F7F9F9"      # 极简钛白背景
X_BG_SIDEBAR = "#0F1419"   # 极夜黑侧边栏
X_TXT_DARK = "#0F1419"     # 主界面深空黑字
X_TXT_LIGHT = "#FFFFFF"    # 侧边栏纯白字
X_TXT_MUTED = "#536471"    # 现代哑光灰

st.markdown(f"""
<style>
    /* 全局背景及字体定义 */
    .stApp {{
        background-color: {X_BG_MAIN} !important;
        color: {X_TXT_DARK} !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}

    /* === 左侧暗黑科技侧边栏 (Sidebar) 全量重构 === */
    [data-testid="stSidebar"] {{
        background-color: {X_BG_SIDEBAR} !important;
        border-right: 1px solid #2F3336 !important;
    }}
    
    /* 强制侧边栏中的各种表单组件标签、文本变为高对比度白色 */
    [data-testid="stSidebar"] .stText, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stRadio label {{
        color: {X_TXT_LIGHT} !important;
        font-weight: 600 !important;
    }}
    
    /* 侧边栏标题及展开折叠器 header */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
        color: {X_TXT_LIGHT} !important;
        font-weight: 800 !important;
    }}
    [data-testid="stSidebar"] .stExpander {{
        background-color: #1E2732 !important;
        border: 1px solid #38444D !important;
        border-radius: 12px !important;
    }}

    /* 侧边栏单选导航项美化：完全像素级致敬 X 导航按钮 */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] {{
        gap: 12px !important;
        padding-top: 15px !important;
    }}
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {{
        background-color: transparent !important;
        border-radius: 9999px !important;
        padding: 12px 24px !important;
        margin: 0 !important;
        transition: all 0.2s ease-in-out;
        width: 100%;
        display: flex;
        align-items: center;
        cursor: pointer;
    }}
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {{
        background-color: rgba(255, 255, 255, 0.08) !important;
    }}
    /* 被选中时的极高对比度蓝色光标状态 */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-selected="true"] {{
        background-color: rgba(29, 155, 240, 0.15) !important;
        border: 1px solid {X_PRIMARY} !important;
    }}
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-selected="true"] p {{
        color: {X_PRIMARY} !important;
        font-weight: 800 !important;
    }}

    /* === 右侧主界面 (Main Content) 卡片与排版重构 === */
    h1 {{ 
        color: {X_TXT_DARK} !important; 
        font-weight: 800 !important; 
        letter-spacing: -0.04em !important; 
        margin-bottom: 1.5rem !important; 
    }}
    h2, h3, h4 {{ 
        color: {X_TXT_DARK} !important; 
        font-weight: 700 !important; 
        margin-top: 1.5rem !important; 
    }}

    /* YouTube 风格的独立悬浮白卡片 */
    .dashboard-card {{
        background-color: #FFFFFF !important;
        padding: 24px !important;
        border-radius: 16px !important;
        border: 1px solid #E1E8ED !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03) !important;
        margin-bottom: 16px !important;
        transition: transform 0.2s ease;
    }}
    .dashboard-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06) !important;
    }}

    /* 表单输入框、选择框现代扁平化设计 */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div, .stDateInput>div>div>input {{
        background-color: #FFFFFF !important;
        color: {X_TXT_DARK} !important;
        border: 1.5px solid #CFD9DE !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        padding: 10px 14px !important;
    }}
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {{
        border-color: {X_PRIMARY} !important;
        box-shadow: 0 0 0 3px rgba(29, 155, 240, 0.15) !important;
    }}

    /* X 风格胶囊型大按钮 */
    .stButton>button {{
        background-color: {X_PRIMARY} !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 9999px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        padding: 12px 32px !important;
        width: auto !important;
        transition: background-color 0.2s;
    }}
    .stButton>button:hover {{
        background-color: #1A8CD8 !important;
    }}

    /* 选项卡 Tabs 美化 */
    button[data-baseweb="tab"] {{
        color: {X_TXT_MUTED} !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        border-bottom-width: 3px !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {X_PRIMARY} !important;
        border-bottom-color: {X_PRIMARY} !important;
        font-weight: 700 !important;
    }}

    /* 进度条轨道与滑块 */
    .stProgress > div > div {{
        background-color: #E1E8ED !important;
        height: 10px !important;
        border-radius: 999px !important;
    }}
    .stProgress > div > div > div > div {{
        background-color: {X_PRIMARY} !important;
        border-radius: 999px !important;
    }}

    /* 数据表格美化 */
    [data-testid="stDataTable"] {{
        border: 1px solid #E1E8ED !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 💡 数据及业务指标初始化 (功能与数据安全锚定)
# ==========================================
PROJECT_STAGES = ["线索", "机会点", "招投标", "已中标"]

HISTORY_ARCHIVE = {
    "2024": {"revenue": 4200000.0, "collection": 3900000.0}, 
    "2025": {"revenue": 4800000.0, "collection": 4600000.0},
}

BASE_ACCOUNTS = [
    "Assets:WeChat", "Assets:Alipay", "Assets:Card:ICBC", "Assets:Cash", "Assets:Reimbursement",
    "Expenses:Food", "Expenses:Child", "Expenses:Decoration", "Expenses:Travel", "Expenses:Daily",
    "Liabilities:CreditCard", "Income:Salary", "Income:SalesBonus"
]

system_current_year = datetime.now().year

# --- 侧边栏：KPI 目标动态配置 ---
with st.sidebar.expander("⚙️ 运营大屏 KPI 智能目标配置", expanded=False):
    st.markdown(f"设定 **{system_current_year}** 年的核心硬性考核指标：")
    cfg_rev = st.number_input("年度确收目标(元)", min_value=0.0, value=5000000.0, step=50000.0)
    cfg_col = st.number_input("年度回款目标(元)", min_value=0.0, value=4500000.0, step=50000.0)

# ==========================================
# 2. 🚀 云数据库 API 驱动引擎
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
    try:
        res_p = requests.get(f"{SB_URL}/rest/v1/projects?select=*", headers=HEADERS, timeout=5).json()
        res_o = requests.get(f"{SB_URL}/rest/v1/orders?select=*", headers=HEADERS, timeout=5).json()
        res_c = requests.get(f"{SB_URL}/rest/v1/collections?select=*", headers=HEADERS, timeout=5).json()
        res_r = requests.get(f"{SB_URL}/rest/v1/revenues?select=*", headers=HEADERS, timeout=5).json() 
        res_l = requests.get(f"{SB_URL}/rest/v1/ledger_entries?select=*", headers=HEADERS, timeout=5).json()
    except Exception as e:
        st.error(f"📡 连不上云数据库: {e}")
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
            raw_order_id = row['id'].split("_")[0] if "_" in row['id'] else row['id']
            orders_dict[row['id']] = {
                "id": row['id'], "raw_id": raw_order_id, "date": str(row['order_date']), "province": row['province'],
                "client": row['client'], "product": row['product'], "price_no_tax": float(row['price_no_tax']),
                "tax_rate": float(row['tax_rate']), "quantity": int(row['quantity']),
                "amt_no_tax": float(row['amt_no_tax']), "amt_with_tax": float(row['amt_with_tax']),
                "p_ref": row.get('project_ref'), "order_p_name": row['order_p_name'], 
                "collect_total": 0.0, "revenue_total": 0.0, "is_history": row.get('project_ref') is None 
            }
        
    collections_list = []
    if isinstance(res_c, list):
        for row in res_c:
            collections_list.append({"o_ref": row['order_ref'], "amount": float(row['amount']), "date": str(row['collection_date']), "invoice_no": row.get('invoice_no', '-')})

    revenues_list = [] 
    if isinstance(res_r, list):
        for row in res_r: revenues_list.append({"o_ref": row['order_ref'], "amount": float(row['amount']), "date": str(row['revenue_date'])})

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
        if o["p_ref"] and o["p_ref"] in projects_dict: projects_dict[o["p_ref"]]["amt_with_tax_total"] += o["amt_with_tax"]
            
    for c in collections_list:
        if c["o_ref"] in orders_dict:
            orders_dict[c["o_ref"]]["collect_total"] += c["amount"]
        else:
            for oid, o in orders_dict.items():
                if o["raw_id"] == c["o_ref"]: orders_dict[oid]["collect_total"] += c["amount"]

    for r in revenues_list:
        if r["o_ref"] in orders_dict: orders_dict[r["o_ref"]]["revenue_total"] += r["amount"]

    return projects_dict, orders_dict, collections_list, revenues_list, ledger_list

st.cache_data.clear()
projects, orders, collections, revenues, ledgers = load_db_data()

# 用于 CSV 导出的辅助函数
def make_csv_buffer(df):
    if df.empty: return None
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    return csv_buffer.getvalue()

dynamic_accounts = set(BASE_ACCOUNTS)
for l in ledgers:
    if l["account_from"]: dynamic_accounts.add(l["account_from"])
    if l["account_to"]: dynamic_accounts.add(l["account_to"])
DYNAMIC_ACCOUNT_LIST = sorted(list(dynamic_accounts))

# ==========================================
# 3. 🗺️ 左侧导航重构：高对比度、大气的命名
# ==========================================
menu_options = [
    "📊 集团核心业绩与双轨 KPI 战略大屏", 
    "📝 通信业务拉通一体化智能流水台账", 
    "➕ 核心业务数据全生命周期控制中心", 
    "🏦 现代复式财务云账本 (hledger 架构)", 
    "💾 库容安全熔断释放与本地备份中枢"
]

with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #FFFFFF; padding-bottom: 10px;'>📊 业务导航</h2>", unsafe_allow_html=True)
    menu = st.radio("系统功能导航", menu_options, key="nav_menu", label_visibility="collapsed")

# ==========================================
# 4. 页面 1: 集团核心业绩与双轨 KPI 战略大屏
# ==========================================
if menu == "📊 集团核心业绩与双轨 KPI 战略大屏":
    st.title("📈 集团核心业绩与双轨 KPI 战略大屏")
    
    current_year = system_current_year 
    
    annual_revenue_done = sum(r["amount"] for r in revenues if datetime.strptime(r["date"], "%Y-%m-%d").year == current_year)
    annual_collection_done = sum(c["amount"] for c in collections if datetime.strptime(c["date"], "%Y-%m-%d").year == current_year)
    
    rev_annual_rate = (annual_revenue_done / cfg_rev) if cfg_rev > 0 else 0.0
    col_annual_rate = (annual_collection_done / cfg_col) if cfg_col > 0 else 0.0

    st.markdown(f"### 🎯 {current_year} 年度双轨 KPI 实时观测中枢")
    
    # --- KPI 卡片渲染器 (优雅卡片，带有顶部炫彩边条) ---
    def render_kpi_card(title, value, sub_text="", accent_color="#E1E8ED", value_color="#0F1419"):
        return f"""
        <div class="dashboard-card" style="border-top: 6px solid {accent_color};">
            <p style="margin:0; font-size:14px; color:{X_TXT_MUTED}; font-weight:600; text-transform: uppercase;">{title}</p>
            <h1 style="margin:12px 0; font-size:32px; color:{value_color}; font-weight:800; font-family: sans-serif; letter-spacing:-0.03em;">{value}</h1>
            <p style="margin:0; font-size:13px; color:{accent_color}; font-weight:700;">{sub_text}</p>
        </div>
        """
        
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.markdown(render_kpi_card(f"{current_year}年度确收指标", f"¥{cfg_rev:,.2f}", "年度硬性指标", "#CFD9DE"), unsafe_allow_html=True)
    m_col2.markdown(render_kpi_card("大盘当前已确收", f"¥{annual_revenue_done:,.2f}", f"🎯 达成率 {rev_annual_rate*100:.1f}%", X_PRIMARY, "#0F1419"), unsafe_allow_html=True)
    m_col3.markdown(render_kpi_card(f"{current_year}年度回款目标", f"¥{cfg_col:,.2f}", "年度资金链红线", "#CFD9DE"), unsafe_allow_html=True)
    m_col4.markdown(render_kpi_card("大盘累计资金进账", f"¥{annual_collection_done:,.2f}", f"⚡ 达成率 {col_annual_rate*100:.1f}%", "#7856FF", "#0F1419"), unsafe_allow_html=True)
    
    # 推进进度条
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"**🔷 {current_year}年度确认收入 KPI 推进链:**")
    st.progress(min(1.0, rev_annual_rate))
    st.markdown(f"**🔷 {current_year}年度实际回款 KPI 资金链脉搏:**")
    st.progress(min(1.0, col_annual_rate))
    
    st.markdown("---")
    
    # 历史演进模块
    st.markdown('<h3>🗂️ 跨断代全景历史业绩演进脉络</h3>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    
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
            barmode="group", text_auto='.3s', title="多跨度年度营收/进账全景历史推演",
            template="plotly_white",
            color_discrete_sequence=[X_PRIMARY, "#AAB8C2"]
        )
        fig_history.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)', 
            font_color=X_TXT_MUTED, 
            title_font_color=X_TXT_DARK,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#E1E8ED")
        )
        st.plotly_chart(fig_history, use_container_width=True)
    except: st.info("📊 演进图深度加载中...")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 5. 页面 2: 通信业务拉通一体化智能流水台账
# ==========================================
elif menu == "📝 通信业务拉通一体化智能流水台账":
    st.title("🖥️ 通信业务拉通一体化智能流水台账")
    
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns([2, 2, 3])
    unique_projects = ["全部项目"] + sorted(list(set(p["name"] for p in projects.values())))
    unique_provinces = ["全部省份"] + sorted(list(set(o["province"] for o in orders.values())))
    selected_project = f_col1.selectbox("🎯 关联框架项目：", unique_projects)
    selected_province = f_col2.selectbox("📍 订单所属省份：", unique_provinces)
    date_range = f_col3.date_input("📅 锁定业务周期范围：", value=(date(date.today().year, 1, 1), date.today()))
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🚧 售前项目框架水位安全警报")
    project_rows = []
    for pid, p in projects.items():
        if selected_project != "全部项目" and p["name"] != selected_project: continue
        ratio = (p["amt_with_tax_total"] / p["target"]) if p["target"] > 0 else 0.0
        warning_status = "✅ 安全水位"
        if ratio >= 1.0: warning_status = "🚨 超标！"
        elif ratio >= 0.8: warning_status = "⚠️ 告急！"
        project_rows.append({"项目框架名称": p["name"], "客户简称": p["client"], "框架标的总额": p["target"], "已下订单含税总额": p["amt_with_tax_total"], "额度消耗比例": f"{ratio*100:.1f}%", "安全预警": warning_status, "创建日期": p["bid_date"], "当前状态": p["stage"]})
    if project_rows:
        df_p_view = pd.DataFrame(project_rows)
        st.dataframe(df_p_view.style.map(lambda v: "background-color: #FEE2E2; color: #991B1B; font-weight: 700;" if "🚨" in str(v) else ("background-color: #FEF3C7; color: #92400E; font-weight: 700;" if "⚠️" in str(v) else ""), subset=["安全预警"]), use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🤝 中标订单及【确收/回款】生命周期流水")
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
        order_rows.append({"订单编号": o["raw_id"], "区域省份": o["province"], "客户简称": o["client"], "订购产品明细": o["product"], "接单含税金额": o["amt_with_tax"], "累计已确收收入": o["revenue_total"], "⏳ 尚未签收": unrevenue, "累计已回款": o["collect_total"], "待追收尾款": uncollected})
        
    if order_rows:
        df_o_view = pd.DataFrame(order_rows)
        st.dataframe(df_o_view, use_container_width=True, hide_index=True)

# ==========================================
# 6. 页面 3: 核心业务数据全生命周期控制中心
# ==========================================
elif menu == "➕ 核心业务数据全生命周期控制中心":
    st.title("🔧 核心业务数据全生命周期控制中心")
    op_type = st.radio("请选择维护操作类型：", ["🆕 录入全新数据", "⚙️ 修改已有信息"], horizontal=True)
    st.markdown("---")

    if op_type == "🆕 录入全新数据":
        sub_step = st.radio("请选择录入的业务阶段：", ["🎯 项目前期录入", "🤝 中标订单录入", "📈 确收登记", "🏦 回款销账"], horizontal=True) 
        st.markdown("---")
        
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        if sub_step == "🎯 项目前期录入":
            with st.form("p_form", clear_on_submit=True):
                st.markdown("##### 填写项目前期框架协议")
                p_name = st.text_input("1. 项目框架/名称 *")
                p_client = st.text_input("2. 客户简称 *")
                p_target = st.number_input("3. 项目框架标的额 (元) *", min_value=0.0)
                p_stage = st.selectbox("4. 项目阶段 *", PROJECT_STAGES)
                p_bid_date = st.date_input("5. 开标/签署时间 *", value=datetime.now()).strftime("%Y-%m-%d")
                if st.form_submit_button("💾 确认保存至 Supabase"):
                    if not p_name or not p_client: st.error("❌ 项目名称和客户简称为必填项！")
                    else:
                        payload = {"id": f"PRJ{int(datetime.now().timestamp())}", "name": p_name, "client": p_client, "target": p_target, "stage": p_stage, "bid_date": p_bid_date}
                        res = requests.post(f"{SB_URL}/rest/v1/projects", headers=HEADERS, json=payload, timeout=5)
                        if res.status_code in [200, 201]: st.success("✔️ 项目入库完成！"); st.rerun()

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
                price = cp.number_input("6. 单价(不含税) *", min_value=0.0)
                tax_rate = cr.number_input("7. 税率 *", min_value=0.0, max_value=1.0, value=0.13)
                qty = cq.number_input("8. 数量 *", min_value=1, value=1)
                amt_no_tax = price * qty
                amt_with_tax = amt_no_tax * (1 + tax_rate)
                st.info(f"📊 自动核税预览含税额: ¥{amt_with_tax:,.2f}")
                o_p_name = st.text_input("12. 对应订单项目名称 *")

                if st.button("⚡ 确认订单下发入库"):
                    if not o_id or not o_province or not o_client or not o_product or not o_p_name: st.error("❌ 请完整填写必填字段！")
                    else:
                        pid_ref = p_opts[sel_p]
                        unique_internal_id = f"{o_id.strip()}_{int(datetime.now().timestamp() * 1000)}"
                        requests.patch(f"{SB_URL}/rest/v1/projects?id=eq.{pid_ref}", headers=HEADERS, json={"stage": "已中标"}, timeout=5)
                        o_payload = {"id": unique_internal_id, "project_ref": pid_ref, "order_date": o_date, "province": o_province, "client": o_client, "product": o_product, "price_no_tax": price, "tax_rate": tax_rate, "quantity": qty, "amt_no_tax": amt_no_tax, "amt_with_tax": amt_with_tax, "order_p_name": o_p_name}
                        res = requests.post(f"{SB_URL}/rest/v1/orders", headers=HEADERS, json=o_payload, timeout=5)
                        if res.status_code in [200, 201]: st.success("✔️ 分项产品明细入库成功！"); st.rerun()

        elif sub_step == "📈 确收登记":
            if not orders: st.warning("⚠️ 系统内暂无订单。")
            else:
                with st.form("r_form", clear_on_submit=True):
                    st.markdown("##### 填写确认收入流水信息")
                    o_opts = {f"订单:{o['raw_id']} ({o['product']} | 含税:¥{o['amt_with_tax']})": oid for oid, o in orders.items()}
                    sel_o = st.selectbox("1. 选择产品分项 *", list(o_opts.keys())); oid_final = o_opts[sel_o]
                    r_amt = st.number_input("2. 本次确收金额 (元) *", min_value=0.0)
                    r_date = st.date_input("3. 实际确认收入日期 *", value=datetime.now()).strftime("%Y-%m-%d")
                    if st.form_submit_button("⚡ 提交确收"):
                        if r_amt <= 0: st.error("❌ 金额需大于0元！")
                        else:
                            res = requests.post(f"{SB_URL}/rest/v1/revenues", headers=HEADERS, json={"order_ref": oid_final, "amount": r_amt, "revenue_date": r_date}, timeout=5)
                            if res.status_code in [200, 201]: st.success("🎉 确收流水已登记！"); st.rerun()

        elif sub_step == "🏦 回款销账":
            is_legacy_history = st.checkbox("⏳ 陈年遗留历史挂账核销")
            with st.form("c_form", clear_on_submit=True):
                st.markdown("##### 填写财务到账及发票匹配销账信息")
                if not is_legacy_history:
                    if not orders: st.warning("⚠️ 系统内暂无订单。"); st.form_submit_button("不可提交", disabled=True); raw_oid_input = ""
                    else:
                        o_opts = {f"订单:{o['raw_id']} (剩余尾款:¥{o['amt_with_tax'] - o['collect_total']:.2f})": oid for oid, o in orders.items()}
                        selected_order_labels = st.multiselect("1. 选择本次合并核销的多个订单明细分项*", list(o_opts.keys()))
                        raw_oid_input = ",".join([o_opts[lbl] for lbl in selected_order_labels])
                else: raw_oid_input = st.text_input("1. 手动输入历史客户订单号 *")

                c_amt = st.number_input("2. 本次财务到账回款总额 (元) *", min_value=0.0)
                c_date = st.date_input("3. 实际回款到账日期 *", value=datetime.now()).strftime("%Y-%m-%d")
                c_invoice = st.text_input("4. 匹配销账发票号 / 凭证号 (选填)")

                if st.form_submit_button("⚡ 执行销账"):
                    cleaned_input = str(raw_oid_input).strip()
                    if not cleaned_input: st.error("❌ 必须选择至少一个识别节点！")
                    elif c_amt <= 0: st.error("❌ 金额需大于0元！")
                    else:
                        target_orders = [x.strip() for x in cleaned_input.split(",") if x.strip()]
                        if len(target_orders) == 1:
                            single_oid = target_orders[0]
                            c_payload = {"order_ref": single_oid, "amount": c_amt, "collection_date": c_date, "invoice_no": c_invoice if c_invoice else f"REG_{int(datetime.now().timestamp())}"}
                            requests.post(f"{SB_URL}/rest/v1/collections", headers=HEADERS, json=c_payload, timeout=5)
                        else:
                            debt_dict = {tid: max(0.0, orders[tid]["amt_with_tax"] - orders[tid]["collect_total"]) for tid in target_orders if tid in orders}
                            total_debt = sum(debt_dict.values())
                            remaining_pool = c_amt
                            for idx, target_id in enumerate(target_orders):
                                if idx == len(target_orders) - 1: split_amt = remaining_pool
                                else:
                                    split_amt = round(c_amt * (debt_dict.get(target_id, 0.0) / total_debt), 2) if total_debt > 0 else round(c_amt / len(target_orders), 2)
                                    remaining_pool -= split_amt
                                each_payload = {"order_ref": target_id, "amount": split_amt, "collection_date": c_date, "invoice_no": f"{c_invoice}_P{idx}" if c_invoice else f"MUL_{int(datetime.now().timestamp())}_{idx}"}
                                requests.post(f"{SB_URL}/rest/v1/collections", headers=HEADERS, json=each_payload, timeout=5)
                        st.success("🎉 分批次/多订单流水分摊销账完毕！"); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif op_type == "⚙️ 修改已有信息":
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
                o_edit_reason = st.text_area("🔧 请输入本次项目调整的原因备注 * (强审计留痕)")
                if st.button("💾 覆写更新项目"):
                    if not o_edit_reason.strip(): st.error("❌ 必须填写修改原因！")
                    else:
                        trace_stamp = f" [修改痕迹 {datetime.now().strftime('%Y-%m-%d')}: {o_edit_reason.strip()}]"
                        up_payload = {"name": up_p_name, "client": up_p_client, "target": up_p_target, "stage": up_p_stage + trace_stamp, "bid_date": old_p["bid_date"]}
                        requests.patch(f"{SB_URL}/rest/v1/projects?id=eq.{pid_edit}", headers=HEADERS, json=up_payload, timeout=5)
                        st.success("🎉 项目强审计链更新成功！"); st.rerun()

        elif edit_target == "🤝 修改订单明细":
            if not orders: st.info("云端暂无订单数据可修改")
            else:
                o_edit_opts = {f"订单号:{o['raw_id']} | 品类:{o['product']}": oid for oid, o in orders.items()}
                sel_edit_o = st.selectbox("请选择更正订单分项：", list(o_edit_opts.keys())); oid_edit = o_edit_opts[sel_edit_o]; old_o = orders[oid_edit]
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
                o_edit_reason = st.text_area("🔧 请输入本次订单调整的原因备注 * (强审计留痕)")
                if st.button("💾 覆写更新订单分项"):
                    if not o_edit_reason.strip(): st.error("❌ 必须填写修改原因！")
                    else:
                        trace_stamp = f" [修改痕迹 {datetime.now().strftime('%Y-%m-%d')}: {o_edit_reason.strip()}]"
                        up_o_payload = {"province": up_o_province, "client": up_o_client, "product": up_o_product + trace_stamp, "order_p_name": up_o_p_name, "price_no_tax": up_price, "tax_rate": up_tax_rate, "quantity": up_qty, "amt_no_tax": new_no_tax, "amt_with_tax": new_tax_in, "order_date": old_o["date"]}
                        requests.patch(f"{SB_URL}/rest/v1/orders?id=eq.{oid_edit}", headers=HEADERS, json=up_o_payload, timeout=5)
                        st.success("🎉 订单分项明细审计链覆写成功！"); st.rerun()

# ==========================================
# 7. 🏦 现代复式财务云账本 (hledger 架构)
# ==========================================
elif menu == "🏦 现代复式财务云账本 (hledger 架构)":
    st.title("🏛️ 现代复式财务云账本 (hledger 架构)")
    
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    f_tabs = st.tabs(["📊 资产分布雷达分析", "📖 Journal 账务明细流水长卷", "✍️ 复合记账表单 (多级平衡校验)"])
    
    with f_tabs[0]:
        if not ledgers: st.info("云端暂无复式记账明细。")
        else:
            df_l = pd.DataFrame(ledgers)
            df_exp = df_l[df_l["account_to"].str.startswith("Expenses:")]
            sc1, sc2 = st.columns(2)
            with sc1:
                if not df_exp.empty:
                    fig_pie_l = px.pie(
                        df_exp, names="account_to", values="amount", 
                        hole=0.5, template="plotly_white", title="Exp. 支出类科目占比分析",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig_pie_l.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color=X_TXT_MUTED)
                    st.plotly_chart(fig_pie_l, use_container_width=True)
            with sc2:
                all_tag_stats = {}
                for _, row in df_l.iterrows():
                    raw_tags = str(row["tags"]).replace(",", " ").replace("，", " ").split()
                    for t in raw_tags:
                        t = t.strip().lower()
                        if t: all_tag_stats[t] = all_tag_stats.get(t, 0.0) + row["amount"]
                if all_tag_stats:
                    df_tags = pd.DataFrame(list(all_tag_stats.items()), columns=["自定义标签Tag", "涉及总金额"]).sort_values(by="涉及总金额", ascending=False)
                    fig_tag_bar = px.bar(
                        df_tags, x="自定义标签Tag", y="涉及总金额", text_auto='.2s', 
                        template="plotly_white", title="动态自由标签穿透穿深分析",
                        color_discrete_sequence=[X_PRIMARY]
                    )
                    fig_tag_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color=X_TXT_MUTED, xaxis=dict(showgrid=False))
                    st.plotly_chart(fig_tag_bar, use_container_width=True)

    with f_tabs[1]:
        if ledgers:
            df_journal = pd.DataFrame(ledgers)[["date", "description", "account_from", "account_to", "amount", "tags", "comment"]]
            df_journal.columns = ["交易核算日期", "核心经济事务描述", "资金去处 (贷/From)", "资金归结 (借/To)", "涉及金额 (元)", "流向Tags", "详细备注"]
            st.dataframe(df_journal, use_container_width=True, hide_index=True)

    with f_tabs[2]:
        st.subheader("✍️ 录入多科目复式分录（借贷平衡配平锁定）")
        l_date = st.date_input("1. 设定记账日期", value=datetime.now()).strftime("%Y-%m-%d")
        l_desc = st.text_input("2. 交易事务/商户描述说明 *", placeholder="如：报销与自费组合购买设备")
        st.markdown("---")
        if "legs_count" not in st.session_state: st.session_state.legs_count = 2
        
        leg_data = []
        for i in range(st.session_state.legs_count):
            c1, c2, c3 = st.columns([3, 4, 2])
            direction = c1.selectbox(f"交易动向#{i+1}", ["去向 (借/To/支出增加或资产增加)", "来源 (贷/From/资产减少或收入)"], key=f"dir_{i}")
            acc_select = c2.selectbox(f"选择科目#{i+1}", DYNAMIC_ACCOUNT_LIST + ["[手动键入全新层级科目]"], key=f"acc_sel_{i}")
            acc_final = c2.text_input(f"✍️ 节点名称#{i+1}", placeholder="如 Expenses:Daily", key=f"acc_raw_{i}") if acc_select == "[手动键入全新层级科目]" else acc_select
            amt = c3.number_input(f"份额金额(元)#{i+1}", min_value=0.0, step=10.0, key=f"amt_{i}")
            leg_data.append({"direction": direction, "account": acc_final, "amount": amt})

        st.markdown("---")
        total_to = sum(item["amount"] for item in leg_data if "去向" in item["direction"])
        total_from = sum(item["amount"] for item in leg_data if "来源" in item["direction"])
        balance_gap = round(total_to - total_from, 2)
        
        b1, b2, b3 = st.columns(3)
        b1.metric("资金去向总额 (借/To)", f"¥{total_to:,.2f}")
        b2.metric("资金来源总额 (贷/From)", f"¥{total_from:,.2f}")
        if balance_gap == 0: b3.success("✅ 借贷零差额，完美配平")
        else: b3.error(f"❌ 借贷差额: ¥{balance_gap:,.2f} (锁定提交)")
            
        l_tags = st.text_input("4. 贴签 Tags (以空格分隔)", placeholder="reimbursement decoration child")
        l_comment = st.text_input("5. 记账说明附加备注")
        
        if st.button("💾 复合复式流水分拆记账", disabled=(balance_gap != 0 or not l_desc)):
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
            if success_flag: st.success("🎉 复合多借多贷账目配平成功！"); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 8. 页面 5: 库容安全熔断释放与本地备份中枢
# ==========================================
elif menu == "💾 库容安全熔断释放与本地备份中枢":
    st.title("💾 库容安全熔断释放与本地备份中枢")
    
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("📊 财务专项：云端复式财务流水一键导出备份")
    if ledgers:
        df_all_ledgers = pd.DataFrame(ledgers)[["date", "description", "account_from", "account_to", "amount", "tags", "comment"]]
        csv_all_l = make_csv_buffer(df_all_ledgers)
        if csv_all_l: st.download_button(label=f"📥 导出财务账目明细卷 (共 {len(df_all_ledgers)} 笔分录).csv", data=csv_all_l, file_name="ledger_entries_all.csv", mime="text/csv")
    st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("📅 历史陈年销售数据归档与熔断粉碎")
    export_year = st.selectbox("请选择要归档归集的目标业务年份：", list(range(system_current_year-3, system_current_year+2)), index=3)

    p_exported = [{"id": p["id"], "name": p["name"], "client": p["client"], "target": p["target"], "stage": p["stage"], "bid_date": p["bid_date"]} for p in projects.values() if datetime.strptime(p["bid_date"], "%Y-%m-%d").year == export_year]
    o_exported = [{"id": o["id"], "project_ref": o["p_ref"], "order_date": o["date"], "province": o["province"], "client": o["client"], "product": o["product"], "price_no_tax": o["price_no_tax"], "tax_rate": o["tax_rate"], "quantity": o["quantity"], "amt_no_tax": o["amt_no_tax"], "amt_with_tax": o["amt_with_tax"], "order_p_name": o["order_p_name"]} for o in orders.values() if datetime.strptime(o["date"], "%Y-%m-%d").year == export_year]
    c_exported = [{"order_ref": row["o_ref"], "amount": row["amount"], "collection_date": row["date"], "invoice_no": row["invoice_no"]} for row in collections if datetime.strptime(row["date"], "%Y-%m-%d").year == export_year]
    r_exported = [{"order_ref": row["o_ref"], "amount": row["amount"], "revenue_date": row["date"]} for row in revenues if datetime.strptime(row["date"], "%Y-%m-%d").year == export_year]

    dl_col1, dl_col2, dl_col3, dl_col4 = st.columns(4)
    with dl_col1:
        csv_p = make_csv_buffer(pd.DataFrame(p_exported))
        if csv_p: st.download_button(f"📥 框架协议 projects_{export_year}.csv", csv_p, f"projects_{export_year}.csv", "text/csv")
    with dl_col2:
        csv_o = make_csv_buffer(pd.DataFrame(o_exported))
        if csv_o: st.download_button(f"📥 中标订单 orders_{export_year}.csv", csv_o, f"orders_{export_year}.csv", "text/csv")
    with dl_col3:
        csv_c = make_csv_buffer(pd.DataFrame(c_exported))
        if csv_c: st.download_button(f"📥 资金回款 collections_{export_year}.csv", csv_c, f"collections_{export_year}.csv", "text/csv")
    with dl_col4:
        csv_r = make_csv_buffer(pd.DataFrame(r_exported))
        if csv_r: st.download_button(f"📥 签收确收 revenues_{export_year}.csv", csv_r, f"revenues_{export_year}.csv", "text/csv")

    st.markdown("---")
    if export_year >= system_current_year:
        st.error(f"🔒 **大盘控制安全断路器阻断**：当前活跃年度数据禁止物理清空！")
    else:
        st.warning(f"⚠️ 允许操作往年历史数据归档清空。")
        confirm_downloaded = st.checkbox(f"🔴 我确认：往年历史数据已导出离线转存备份，请求从 Supabase 云数据库完全清空库容以释放空间。")
        if confirm_downloaded and st.button(f"🗑️ 彻底物理粉碎云端 {export_year} 年往期历史业务流水", type="primary"):
            requests.delete(f"{SB_URL}/rest/v1/projects?bid_date=gte.{export_year}-01-01&bid_date=lte.{export_year}-12-31", headers=HEADERS, timeout=5)
            requests.delete(f"{SB_URL}/rest/v1/orders?order_date=gte.{export_year}-01-01&order_date=lte.{export_year}-12-31", headers=HEADERS, timeout=5)
            requests.delete(f"{SB_URL}/rest/v1/collections?collection_date=gte.{export_year}-01-01&collection_date=lte.{export_year}-12-31", headers=HEADERS, timeout=5)
            requests.delete(f"{SB_URL}/rest/v1/revenues?revenue_date=gte.{export_year}-01-01&revenue_date=lte.{export_year}-12-31", headers=HEADERS, timeout=5)
            st.success("云端历史库容安全熔断释放完毕！"); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
