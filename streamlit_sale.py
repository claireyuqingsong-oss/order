import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import requests
import io

# ==========================================
# 0. 页面基础配置 (必须作为首句)
# ==========================================
st.set_page_config(page_title="通信销售与复式财务全能云工作台", layout="wide")

PROJECT_STAGES = ["线索", "机会点", "招投标", "已中标"]

# ==========================================
# 🗄️ 永久冷数据存储：往年离线归档数据集 (本地永久存储，不占 Supabase 云容量)
# ==========================================
HISTORY_ARCHIVE = {
    "2024": {"revenue": 4200000.0, "collection": 3900000.0}, 
    "2025": {"revenue": 4800000.0, "collection": 4600000.0},
}

# 💡 复式记账基础常用账户树种子 (系统运行时会自动把用户新填写的账户吸纳进来)
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
    """实时读取 Supabase 云数据库数据(融入复式记账表)"""
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
            p_ref = orders_dict[c["o_ref"]]["p_ref"]
            if p_ref and p_ref in projects_dict: projects_dict[p_ref]["collect_total"] += c["amount"]

    for r in revenues_list:
        if r["o_ref"] in orders_dict: orders_dict[r["o_ref"]]["revenue_total"] += r["amount"]

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

# 动态提取自定义账户
existing_accounts = set(BASE_ACCOUNTS)
for l in ledgers:
    if l["account_from"]: existing_accounts.add(l["account_from"])
    if l["account_to"]: existing_accounts.add(l["account_to"])
DYNAMIC_ACCOUNT_LIST = sorted(list(existing_accounts))

# ==========================================
# 2. 侧边栏导航控制
# ==========================================
st.sidebar.title("📱 业务与财务拉通工作台")
st.sidebar.markdown("💡 **数据同步引擎**：`🟢 Supabase REST 高速通道已就绪`")

system_current_year = datetime.now().year

with st.sidebar.expander("⚙️ 运营大屏 KPI 考核目标设置"):
    cfg_rev = st.number_input("本年度确认收入目标(元)", min_value=0.0, value=5000000.0, step=50000.0)
    cfg_col = st.number_input("本年度到账回款目标(元)", min_value=0.0, value=4500000.0, step=50000.0)

menu = st.sidebar.radio("功能导航", ["📊 业绩与KPI大屏", "📝 综合业务台账", "➕ 业务数据维护中心", "🏦 复式财务管理中心", "💾 往年库容释放与数据导出"])

# ==========================================
# [老核心模块代码保持不变，稳定兼容]
# ==========================================
if menu == "📊 业绩与KPI大屏":
    st.title("🏆 销售业绩与年/季双轨 KPI 战略大屏")
    current_year = system_current_year
    annual_revenue_done = sum(r["amount"] for r in revenues if datetime.strptime(r["date"], "%Y-%m-%d").year == current_year)
    annual_collection_done = sum(c["amount"] for c in collections if datetime.strptime(c["date"], "%Y-%m-%d").year == current_year)
    rev_annual_rate = (annual_revenue_done / cfg_rev) if cfg_rev > 0 else 0.0
    col_annual_rate = (annual_collection_done / cfg_col) if cfg_col > 0 else 0.0
    st.markdown(f"### 📅 {current_year}年度动态 KPI 达成看板")
    def render_custom_metric(title, value, sub_text=""):
        return f"<div style='background-color:#f8f9fa; padding:12px; border-radius:6px; border:1px solid #e9ecef; text-align:center; min-height:100px;'><p style='margin:0; font-size:13px; color:#6c757d; font-weight:500;'>{title}</p><h3 style='margin:6px 0; font-size:18px; color:#212529; font-weight:700;'>{value}</h3><p style='margin:0; font-size:12px; color:#28a745; font-weight:bold;'>{sub_text}</p></div>"
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.markdown(render_custom_metric(f"{current_year}年度确收目标", f"¥{cfg_rev:,.2f}"), unsafe_allow_html=True)
    m_col2.markdown(render_custom_metric("当前已确收(已到货)", f"¥{annual_revenue_done:,.2f}", f"已达成 {rev_annual_rate*100:.1f}%"), unsafe_allow_html=True)
    m_col3.markdown(render_custom_metric(f"{current_year}年度回款目标", f"¥{cfg_col:,.2f}"), unsafe_allow_html=True)
    m_col4.markdown(render_custom_metric("全年度累计到账回款", f"¥{annual_collection_done:,.2f}", f"已达成 {col_annual_rate*100:.1f}%"), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.progress(min(1.0, rev_annual_rate))
    st.progress(min(1.0, col_annual_rate))

elif menu == "📝 综合业务台账":
    st.title("📝 综合业务拉通明细台账")
    f_col1, f_col2, f_col3 = st.columns(3)
    unique_projects = ["全部项目"] + sorted(list(set(p["name"] for p in projects.values())))
    unique_provinces = ["全部省份"] + sorted(list(set(o["province"] for o in orders.values())))
    selected_project = f_col1.selectbox("🎯 按关联框架项目过滤：", unique_projects)
    selected_province = f_col2.selectbox("📍 按订单区域省份过滤：", unique_provinces)
    date_range = f_col3.date_input("📅 筛选接单下发日期范围：", value=(date(date.today().year, 1, 1), date.today()))
    st.subheader("🤝 正式订单追缴看板")
    order_rows = []
    for oid, o in orders.items():
        related_p_name = projects[o["p_ref"]]["name"] if o["p_ref"] and o["p_ref"] in projects else "历史老账"
        if selected_project != "全部项目" and related_p_name != selected_project: continue
        if selected_province != "全部省份" and o["province"] != selected_province: continue
        uncollected = max(0.0, o["amt_with_tax"] - o["collect_total"])
        order_rows.append({"订单编号": o["id"], "订单下发日期": o["date"], "区域省份": o["province"], "客户简称": o["client"], "订购产品明细": o["product"], "接单含税金额": o["amt_with_tax"], "累计已确收": o["revenue_total"], "累计已回款": o["collect_total"], "待追收尾款": uncollected})
    if order_rows: st.dataframe(pd.DataFrame(order_rows), use_container_width=True, hide_index=True)

elif menu == "➕ 业务数据维护中心":
    st.title("🛠️ 业务数据全生命周期维护中心")
    sub_step = st.radio("请选择录入的业务阶段：", ["🎯 项目前期录入", "🤝 中标订单录入"], horizontal=True)
    if sub_step == "🎯 项目前期录入":
        with st.form("p_form"):
            p_name = st.text_input("项目框架/名称 *")
            p_client = st.text_input("客户简称 *")
            p_target = st.number_input("项目框架标的额 (元) *", min_value=0.0)
            if st.form_submit_button("💾 保存项目"):
                res = requests.post(f"{SB_URL}/rest/v1/projects", headers=HEADERS, json={"id": f"PRJ{int(datetime.now().timestamp())}", "name": p_name, "client": p_client, "target": p_target, "stage": "线索", "bid_date": str(date.today())})
                if res.status_code in [200, 201]: st.success("写入成功！"); st.rerun()

# ==========================================
# 6. 🏦 复式财务管理中心
# ==========================================
elif menu == "🏦 复式财务管理中心":
    st.title("🏦 个人与家庭复式财务账本中心 (hledger 高度自由版)")
    st.markdown("基于复式记账法原理，**支持一笔交易拆分至多个来源/去向账户**，支持完全自定义层级账户与自由 Tag。")
    
    f_tabs = st.tabs(["📊 个人财务分析大屏", "📝 复式分录明细账", "✍️ 极速记账与多账户拆分"])
    
    with f_tabs[0]:
        st.subheader("📊 个人资产与专项标签开销穿透")
        if not ledgers: st.info("暂无复式记账明细。")
        else:
            df_l = pd.DataFrame(ledgers)
            df_exp = df_l[df_l["account_to"].str.startswith("Expenses:")]
            sc1, sc2 = st.columns(2)
            with sc1:
                st.markdown("#### 🍕 动态消费去向科目构成")
                if not df_exp.empty:
                    fig_pie_l = px.pie(df_exp, names="account_to", values="amount", hole=0.3, title="各项 Expenses 账户开销占比")
                    st.plotly_chart(fig_pie_l, use_container_width=True)
                else: st.text("暂无费用支出数据。")
            with sc2:
                st.markdown("#### 🏷️ 自由 Tag 标签多维深度统计")
                all_tag_stats = {}
                for _, row in df_l.iterrows():
                    raw_tags = str(row["tags"]).replace(",", " ").replace("，", " ").split()
                    for t in raw_tags:
                        t = t.strip().lower()
                        if t: all_tag_stats[t] = all_tag_stats.get(t, 0.0) + row["amount"]
                if all_tag_stats:
                    df_tags = pd.DataFrame(list(all_tag_stats.items()), columns=["自定义Tag标签", "累计涉及金额(元)"]).sort_values(by="累计涉及金额(元)", ascending=False)
                    fig_tag_bar = px.bar(df_tags, x="自定义Tag标签", y="累计涉及金额(元)", text_auto=True, title="自由输入标签累计统计柱状图")
                    st.plotly_chart(fig_tag_bar, use_container_width=True)
                else: st.text("未检索到任何交易带有 Tag 标签。")

    with f_tabs[1]:
        st.subheader("📜 复式记账标准分录流水 (Journal)")
        if ledgers:
            df_journal = pd.DataFrame(ledgers)[["date", "description", "account_from", "account_to", "amount", "tags", "comment"]]
            df_journal.columns = ["交易日期", "交易描述", "资金来源账户 (贷/From)", "资金去向账户 (借/To)", "金额(元)", "自由Tags", "详细备注"]
            st.dataframe(df_journal, use_container_width=True, hide_index=True)
        else: st.info("目前还没有账目流水。")

    with f_tabs[2]:
        st.subheader("✍️ 录入复式流水分录（完美支持单笔交易多账户分拆）")
        l_date = st.date_input("1. 交易日期", value=datetime.now()).strftime("%Y-%m-%d")
        l_desc = st.text_input("2. 交易描述/商户名称 *", placeholder="例如：汉庭酒店住宿(部分报销)")
        st.markdown("---")
        st.markdown("### 🧩 复式分录借贷平衡配置")
        if "legs_count" not in st.session_state: st.session_state.legs_count = 2
        def add_leg(): st.session_state.legs_count += 1
        def remove_leg():
            if st.session_state.legs_count > 2: st.session_state.legs_count -= 1

        leg_data = []
        for i in range(st.session_state.legs_count):
            st.markdown(f"**科目分录 #{i+1} :**")
            c1, c2, c3, c4 = st.columns([2, 3, 3, 2])
            direction = c1.selectbox(f"方向#{i+1}", ["资金去向 (借/To/支出或资产增加)", "资金来源 (贷/From/资产减少或收入)"], key=f"dir_{i}")
            acc_select = c2.selectbox(f"选择已有账户#{i+1}", ["[+ 手工输入全新账户]"] + DYNAMIC_ACCOUNT_LIST, key=f"acc_sel_{i}")
            if acc_select == "[+ 手工输入全新账户]":
                acc_final = c3.text_input(f"✍️ 自定义新账户名#{i+1}", placeholder="层级用英文冒号隔开如 Expenses:Food:Snacks", key=f"acc_raw_{i}")
            else:
                acc_final = acc_select
                c3.info(f"已锁定账户: `{acc_final}`")
            amt = c4.number_input(f"金额(元)#{i+1}", min_value=0.0, step=10.0, key=f"amt_{i}")
            leg_data.append({"direction": direction, "account": acc_final, "amount": amt})

        b_col1, b_col2, _ = st.columns([2, 2, 8])
        b_col1.button("➕ 添加拆分分录/多账户", on_click=add_leg)
        b_col2.button("➖ 减少末尾分录", on_click=remove_leg)

        st.markdown("---")
        total_to = sum(item["amount"] for item in leg_data if "去向" in item["direction"])
        total_from = sum(item["amount"] for item in leg_data if "来源" in item["direction"])
        balance_gap = round(total_to - total_from, 2)
        
        st.markdown(f"### 🧮 借贷平衡实时审计看盘:")
        ck1, ck2, ck3 = st.columns(3)
        ck1.metric("去向账户(借/To)总计", f"¥{total_to:,.2f}")
        ck2.metric("资金来源(贷/From)总计", f"¥{total_from:,.2f}")
        if balance_gap == 0: ck3.success("✅ 借贷平衡，准许入账！")
        else: ck3.error(f"❌ 借贷失衡差额: ¥{balance_gap:,.2f}")
            
        st.markdown("---")
        l_tags = st.text_input("4. 自由 Tag 标签 (多个标签用空格或逗号隔开)", placeholder="例如: child 装修 报销凭证")
        l_comment = st.text_input("5. 附加交易备注说明")
        
        if st.button("💾 确认复合复式记账同步写入云端", disabled=(balance_gap != 0 or not l_desc)):
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
                    st.success("🎉 复式记账多边拆分分录成功写入云端！")
                    st.cache_data.clear(); st.rerun()
                else: st.error("网络握手异常，写入失败。")

# ==========================================
# 7. 💾 往年库容释放与数据导出中心 (💡 增加不区分年份财务全量导出功能)
# ==========================================
elif menu == "💾 往年库容释放与数据导出":
    st.title("💾 往年库容释放与本地数据备份中心")
    
    # 💡 新增：不区分年份，全量一键导出财务账本通道
    st.subheader("🏦 财务数据专项：全量历史复式财务账本下载通道")
    st.markdown("此备份通道不区分业务年份，一键拉取云端数据库中**所有年份、所有科目和动态标签**的完整明细流水，可直接导入本地 MySQL 数据库，或使用 Excel/Python 进行全景财务透视。")
    if ledgers:
        df_all_ledgers = pd.DataFrame(ledgers)[["id", "date", "code", "description", "account_from", "account_to", "amount", "tags", "comment"]]
        df_all_ledgers.columns = ["id", "tx_date", "code", "description", "account_from", "account_to", "amount", "tags", "comment"] # 完美契合 MySQL 结构
        csv_all_l = make_csv_buffer(df_all_ledgers)
        if csv_all_l:
            st.download_button(
                label=f"📥 导出全量历史复式财务账本 (共 {len(df_all_ledgers)} 条分录).csv", 
                data=csv_all_l, 
                file_name="mysql_ledger_entries_all.csv", 
                mime="text/csv",
                type="primary"
            )
    else:
        st.info("📊 暂无财务记账数据留存，无法导出。")
        
    st.markdown("---")
    
    # 下方保持原有业务订单按年份的熔断清空逻辑不变
    st.subheader("📅 业务销售数据专项：按年度归档与容量清空")
    export_year = st.selectbox("请选择要处理的销售业务年份：", list(range(system_current_year-3, system_current_year+2)), index=3)
    st.write(f"📡 正在动态扫描 `{export_year}` 年的销售回款台账...")

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
        st.error(f"🔒 **物理删除硬熔断锁死**：当前或活跃年度禁止执行清空删除！")
    else:
        st.warning(f"⚠️ 允许执行往年历史老数据（{export_year} 年）清空。")
        confirm_downloaded = st.checkbox(f"🔴 **我发誓确认：我刚才已经下载了销售相关明细 CSV 文件并完成备份！**")
        if confirm_downloaded:
            if st.button(f"🗑️ 物理清空云端 {export_year} 全部销售账目数据", type="primary"):
                requests.delete(f"{SB_URL}/rest/v1/projects?bid_date=gte.{export_year}-01-01&bid_date=lte.{export_year}-12-31", headers=HEADERS, timeout=5)
                requests.delete(f"{SB_URL}/rest/v1/orders?order_date=gte.{export_year}-01-01&order_date=lte.{export_year}-12-31", headers=HEADERS, timeout=5)
                requests.delete(f"{SB_URL}/rest/v1/collections?collection_date=gte.{export_year}-01-01&collection_date=lte.{export_year}-12-31", headers=HEADERS, timeout=5)
                requests.delete(f"{SB_URL}/rest/v1/revenues?revenue_date=gte.{export_year}-01-01&revenue_date=lte.{export_year}-12-31", headers=HEADERS, timeout=5)
                st.success("老业务数据成功物理粉碎！"); st.cache_data.clear(); st.rerun()
