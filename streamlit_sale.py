import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import requests

# ==========================================
# 0. 页面基础配置 (必须作为首句)
# ==========================================
st.set_page_config(page_title="通信销售全生命周期 Supabase 云工作台", layout="wide")

PROJECT_STAGES = ["线索", "机会点", "招投标", "已中标"]

# 💡 个人年度 KPI 指标设定
ANNUAL_REVENUE_TARGET = 5000000.0   
ANNUAL_COLLECTION_TARGET = 4500000.0 

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

@st.cache_data(ttl=1) # 1秒极速缓存
def load_db_data():
    """通过标准 HTTPS 接口，实时读取 Supabase 云数据库数据"""
    try:
        res_p = requests.get(f"{SB_URL}/rest/v1/projects?select=*", headers=HEADERS, timeout=5).json()
        res_o = requests.get(f"{SB_URL}/rest/v1/orders?select=*", headers=HEADERS, timeout=5).json()
        res_c = requests.get(f"{SB_URL}/rest/v1/collections?select=*", headers=HEADERS, timeout=5).json()
        res_r = requests.get(f"{SB_URL}/rest/v1/revenues?select=*", headers=HEADERS, timeout=5).json() 
    except Exception as e:
        st.error(f"📡 连不上云数据库，网络握手超时！详情: {e}")
        return {}, {}, [], []

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
                "collect_total": 0.0, "revenue_total": 0.0, 
                "is_history": row.get('project_ref') is None 
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
        
    # 交叉核算多表联动财务逻辑
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

    return projects_dict, orders_dict, collections_list, revenues_list

# 强制清空本地缓存以加载最新公网云数据
st.cache_data.clear()
projects, orders, collections, revenues = load_db_data()

def get_quarter(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.year, f"Q{(dt.month - 1) // 3 + 1}"
    except:
        return None, None

# ==========================================
# 2. 侧边栏导航控制
# ==========================================
st.sidebar.title("📱 通信销售云工作台")
st.sidebar.markdown("💡 **数据同步引擎**：`🟢 Supabase REST 高速通道已就绪`")
menu = st.sidebar.radio("功能导航", ["📊 业绩与KPI大屏", "📝 综合业务台账", "➕ 业务数据维护中心"])

# ==========================================
# 3. 页面 1: 业绩与KPI大屏
# ==========================================
if menu == "📊 业绩与KPI大屏":
    st.title("🏆 销售业绩与年/季双轨 KPI 战略大屏")
    current_year = 2026 
    
    annual_revenue_done = sum(r["amount"] for r in revenues if datetime.strptime(r["date"], "%Y-%m-%d").year == current_year)
    annual_collection_done = sum(c["amount"] for c in collections if datetime.strptime(c["date"], "%Y-%m-%d").year == current_year)
    
    rev_annual_rate = (annual_revenue_done / ANNUAL_REVENUE_TARGET) if ANNUAL_REVENUE_TARGET > 0 else 0.0
    col_annual_rate = (annual_collection_done / ANNUAL_COLLECTION_TARGET) if ANNUAL_COLLECTION_TARGET > 0 else 0.0

    st.markdown(f"### 📅 {current_year}年度核心 KPI 战略总览")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    kpi_col1.metric("年度确认收入目标", f"¥{ANNUAL_REVENUE_TARGET:,.2f}")
    kpi_col2.metric("当前已确收(已到货)", f"¥{annual_revenue_done:,.2f}", f"已达成 {rev_annual_rate*100:.1f}%")
    kpi_col3.metric("年度回款到账目标", f"¥{ANNUAL_COLLECTION_TARGET:,.2f}")
    kpi_col4.metric("全年度累计到账回款", f"¥{annual_collection_done:,.2f}", f"已达成 {col_annual_rate*100:.1f}%")
    
    st.markdown("**🎯 年度确收 KPI 进度:**")
    st.progress(min(1.0, rev_annual_rate))
    st.markdown("**🏦 年度回款 KPI 进度:**")
    st.progress(min(1.0, col_annual_rate))
    st.markdown("---")

    st.markdown("### 🔍 季度 KPI 财务战果穿透查询")
    selected_q = st.selectbox("请选择需要复盘的特定季度：", [f"{current_year}年 Q1 (1-3月)", f"{current_year}年 Q2 (4-6月)", f"{current_year}年 Q3 (7-9月)", f"{current_year}年 Q4 (10-12月)"], index=2)
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
    q_box1.markdown(f"<div style='background-color:#f8f9fa; padding:15px; border-left:5px solid #3498db; border-radius:4px;'><h4>📌 当前考察季度</h4><h2 style='color:#3498db;'>{selected_q}</h2></div>", unsafe_allow_html=True)
    q_box2.markdown(f"<div style='background-color:#f8f9fa; padding:15px; border-left:5px solid #2ecc71; border-radius:4px;'><h4>📈 该季度确认收入</h4><h2 style='color:#2ecc71;'>¥{q_revenue_done:,.2f}</h2></div>", unsafe_allow_html=True)
    q_box3.markdown(f"<div style='background-color:#f8f9fa; padding:15px; border-left:5px solid #9b59b6; border-radius:4px;'><h4>🏦 该季度实际催收到账回款</h4><h2 style='color:#9b59b6;'>¥{q_collection_done:,.2f}</h2></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if q_revenue_done > 0 or q_collection_done > 0:
        fig_q = px.bar(x=["季度确认收入数据", "季度回款数据"], y=[q_revenue_done, q_collection_done], color=["确收", "回款"], text_auto='.2f', labels={'x': '财务考评参数', 'y': '金额 (元)'}, title=f"📊 {selected_q} 确收与回款配比直方图")
        st.plotly_chart(fig_q, use_container_width=True)
    else:
        st.info(f"💡 提示：您选择的 {selected_q} 内暂时没有产生到货确收或回款流水。")

# ==========================================
# 4. 页面 2: 综合业务台账
# ==========================================
elif menu == "📝 综合业务台账":
    st.title("📝 综合业务拉通明细台账")
    st.markdown("### 🎛️ 数据中心快速过滤器")
    f_col1, f_col2, f_col3 = st.columns(3)
    
    unique_projects = ["全部项目"] + sorted(list(set(p["name"] for p in projects.values())))
    unique_provinces = ["全部省份"] + sorted(list(set(o["province"] for o in orders.values())))
    
    selected_project = f_col1.selectbox("🎯 按关联框架项目过滤：", unique_projects)
    selected_province = f_col2.selectbox("📍 按订单区域省份过滤：", unique_provinces)
    
    today = date.today()
    start_of_year = date(today.year, 1, 1)
    date_range = f_col3.date_input("📅 筛选接单下发日期范围：", value=(start_of_year, today))
    st.markdown("---")

    st.subheader("🎯 前期售前 / 框架项目看板")
    project_rows = []
    for pid, p in projects.items():
        if selected_project != "全部项目" and p["name"] != selected_project: continue
        ratio = (p["amt_with_tax_total"] / p["target"]) if p["target"] > 0 else 0.0
        warning_status = "✅ 安全范围"
        if ratio >= 1.0: warning_status = "🚨 严重超标！已爆框架"
        elif ratio >= 0.8: warning_status = "⚠️ 额度告急！超过80%"
        project_rows.append({"项目ID": p["id"], "项目/框架名称": p["name"], "客户简称": p["client"], "框架标的总额": p["target"], "已下正式订单含税总额": p["amt_with_tax_total"], "框架额度消耗比例": f"{ratio*100:.1f}%", "框架安全水位预警": warning_status, "开标/创建日期": p["bid_date"], "当前状态": p["stage"]})
    if project_rows:
        df_p_view = pd.DataFrame(project_rows)
        st.dataframe(df_p_view.style.map(lambda v: "background-color: #ffcccc; color: #cc0000; font-weight: bold;" if "🚨" in str(v) else ("background-color: #fff3cd; color: #856404; font-weight: bold;" if "⚠️" in str(v) else ""), subset=["框架安全水位预警"]), use_container_width=True, hide_index=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.subheader("🤝 已中标正式订单及【到货确收】追踪明细表")
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
        s1.metric("当前筛选正式接单额", f"¥{df_o_view['接单含税金额'].sum():,.2f}")
        s2.metric("当前已开网收货确收额", f"¥{df_o_view['💡 累计已确认收入'].sum():,.2f}")
        s3.metric("整个大盘待催收尾款", f"¥{df_o_view['待追收尾款'].sum():,.2f}")
        st.dataframe(df_o_view, use_container_width=True, hide_index=True)
    else:
        st.info("选定的日期范围内暂无符合过滤条件的正式订单数据")

# ==========================================
# 5. 页面 3: 业务数据维护中心
# ==========================================
elif menu == "➕ 业务数据维护中心":
    st.title("🛠️ 业务数据全生命周期维护中心")
    op_type = st.radio("请选择您要执行的维护类型：", ["🆕 录入全新数据", "⚙️ 修改已有信息 (数据回显覆写)"], horizontal=True)
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

                if st.form_submit_button("💾 确认保存至 Supabase"):
                    if not p_name or not p_client: st.error("❌ 项目名称和客户简称为必填项！")
                    else:
                        new_id = f"PRJ{int(datetime.now().timestamp())}"
                        payload = {"id": new_id, "name": p_name, "client": p_client, "target": p_target, "stage": p_stage, "bid_date": p_bid_date}
                        res = requests.post(f"{SB_URL}/rest/v1/projects", headers=HEADERS, json=payload, timeout=5)
                        if res.status_code in [200, 201]: st.success(f"✔️ 框架项目【{p_name}】已经成功同步写入云端！"); st.cache_data.clear(); st.rerun()

        elif sub_step == "🤝 中标订单录入":
            if not projects: st.warning("⚠️ 暂无任何前置项目，请先完成【项目前期录入】！")
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
                st.info(f"📊 自动核税预览：不含税: ¥{amt_no_tax:,.2f} | 本次拟录含税额: ¥{amt_with_tax:,.2f}")
                o_p_name = st.text_input("12. 对应订单项目名称 *")

                if st.button("💾 确认保存订单"):
                    if not o_id or not o_province or not o_client or not o_product or not o_p_name: st.error("❌ 请完整填写带有 * 的必填订单字段！")
                    else:
                        pid_ref = p_opts[sel_p]
                        requests.patch(f"{SB_URL}/rest/v1/projects?id=eq.{pid_ref}", headers=HEADERS, json={"stage": "已中标"}, timeout=5)
                        o_payload = {"id": o_id, "project_ref": pid_ref, "order_date": o_date, "province": o_province, "client": o_client, "product": o_product, "price_no_tax": price, "tax_rate": tax_rate, "quantity": qty, "amt_no_tax": amt_no_tax, "amt_with_tax": amt_with_tax, "order_p_name": o_p_name}
                        res = requests.post(f"{SB_URL}/rest/v1/orders", headers=HEADERS, json=o_payload, timeout=5)
                        if res.status_code in [200, 201]: st.success(f"✔️ 中标正式合同订单 {o_id} 云端同步成功！"); st.cache_data.clear(); st.rerun()

        elif sub_step == "📈 确认收入到货登记":
            if not orders: st.warning("⚠️ 系统内暂无订单。")
            else:
                with st.form("r_form", clear_on_submit=True):
                    o_opts = {f"订单:{oid} (接单含税总额:¥{o['amt_with_tax']} | 已确收:¥{o['revenue_total']})": oid for oid, o in orders.items()}
                    sel_o = st.selectbox("1. 选择要登记收货确收的客户订单号 *", list(o_opts.keys())); oid_final = o_opts[sel_o]
                    r_amt = st.number_input("2. 本次客户签收/确认收入金额 (元) *", min_value=0.0)
                    r_date = st.date_input("3. 实际确认收入到货日期 *", value=datetime.now()).strftime("%Y-%m-%d")
                    if st.form_submit_button("💾 确认登记确收收入"):
                        if r_amt <= 0: st.error("❌ 确收金额需大于0元！")
                        else:
                            r_payload = {"order_ref": oid_final, "amount": r_amt, "revenue_date": r_date}
                            res = requests.post(f"{SB_URL}/rest/v1/revenues", headers=HEADERS, json=r_payload, timeout=5)
                            if res.status_code in [200, 201]: st.success("🎉 确收成功！"); st.cache_data.clear(); st.rerun()

        # 🏦 回款销账（已全面升级解耦：多单合并下拉多选，遗留老账独立手敲）
        elif sub_step == "🏦 回款销账登记":
            st.markdown("### 🏦 客户回款到账流销账登记")
            
            # 1. 拆分逻辑：遗留老账作为单独开关
            is_legacy_history = st.checkbox("⏳ 本次是核销【多年前的陈年遗留老账/挂账】（系统内无此订单号）")
            
            with st.form("c_form", clear_on_submit=True):
                if not is_legacy_history:
                    # 💡 核心改进：系统内账单，默认直接提供多选下拉框！支持单选，也支持自由组合鼠标勾选！
                    if not orders: 
                        st.warning("⚠️ 系统内暂无订单。")
                        st.form_submit_button("不可提交", disabled=True)
                        raw_oid_input = ""
                    else:
                        o_opts = {f"订单:{oid} (尾款:¥{o['amt_with_tax'] - o['collect_total']:.2f})": oid for oid, o in orders.items()}
                        selected_order_labels = st.multiselect("1. 请选择本次合并结算包含的订单号（可多选框）*", list(o_opts.keys()))
                        # 自动将多选结果提取出单号，并用英文逗号拼装成底层引擎认识的格式
                        raw_oid_input = ",".join([o_opts[lbl] for lbl in selected_order_labels])
                else: 
                    # 如果是历史老账，才切换为全手动输入框
                    raw_oid_input = st.text_input("1. 手动精确输入历史客户订单号 * (支持多单号逗号隔开，如: OLD_01,OLD_02)")

                c_amt = st.number_input("2. 本次财务实际到账总回款额 (元) *", min_value=0.0)
                c_date = st.date_input("3. 实际回款进账日期 *", value=datetime.now()).strftime("%Y-%m-%d")
                c_invoice = st.text_input("4. 关联销账发票号 / 财务凭证号 (选填)")

                if st.form_submit_button("💾 确认登记回款"):
                    cleaned_input = str(raw_oid_input).strip()
                    if not cleaned_input: st.error("❌ 必须选择或填写至少一个订单号才能提交结算！")
                    elif c_amt <= 0: st.error("❌ 回款金额需大于0元！")
                    else:
                        # 💡 核心分摊引擎解析处理
                        target_orders = [x.strip() for x in cleaned_input.split(",") if x.strip()]
                        
                        if len(target_orders) == 1:
                            # --- 场景 A：单订单极速核销 ---
                            single_oid = target_orders[0]
                            if is_legacy_history and (single_oid not in orders):
                                hedge_payload = {"id": single_oid, "project_ref": None, "order_date": c_date, "province": "历史老账归档区", "client": "历史长账龄客户", "product": "跨年历史账目结转款", "price_no_tax": c_amt, "tax_rate": 0.0, "quantity": 1, "amt_no_tax": c_amt, "amt_with_tax": c_amt, "order_p_name": "多年前老订单挂账"}
                                requests.post(f"{SB_URL}/rest/v1/orders", headers=HEADERS, json=hedge_payload, timeout=5)
                            
                            c_payload = {"order_ref": single_oid, "amount": c_amt, "collection_date": c_date, "invoice_no": c_invoice if c_invoice else "-"}
                            requests.post(f"{SB_URL}/rest/v1/collections", headers=HEADERS, json=c_payload, timeout=5)
                        else:
                            # --- 场景 B：运营商合并账单【智能按欠款比例拆分】 ---
                            debt_dict = {}
                            total_debt = 0.0
                            for target_id in target_orders:
                                if target_id in orders:
                                    current_debt = max(0.0, orders[target_id]["amt_with_tax"] - orders[target_id]["collect_total"])
                                else:
                                    current_debt = 0.0
                                debt_dict[target_id] = current_debt
                                total_debt += current_debt
                            
                            remaining_pool = c_amt
                            for idx, target_id in enumerate(target_orders):
                                if idx == len(target_orders) - 1:
                                    split_amt = remaining_pool
                                else:
                                    if total_debt > 0:
                                        split_amt = round(c_amt * (debt_dict[target_id] / total_debt), 2)
                                    else:
                                        split_amt = round(c_amt / len(target_orders), 2)
                                    remaining_pool -= split_amt
                                
                                if target_id not in orders:
                                    requests.post(f"{SB_URL}/rest/v1/orders", headers=HEADERS, json={"id": target_id, "project_ref": None, "order_date": c_date, "province": "合并结算老账区", "client": "运营商历史长账", "product": "历史批量并单核销款", "price_no_tax": split_amt, "tax_rate": 0.0, "quantity": 1, "amt_no_tax": split_amt, "amt_with_tax": split_amt, "order_p_name": "批量遗留老账合并"}, timeout=5)
                                
                                each_payload = {"order_ref": target_id, "amount": split_amt, "collection_date": c_date, "invoice_no": f"{c_invoice}(多单合并自动拆分)" if c_invoice else "合并拆分流水"}
                                requests.post(f"{SB_URL}/rest/v1/collections", headers=HEADERS, json=each_payload, timeout=5)
                        
                        st.success("🎉 回款处理完毕！已成功通过下拉多选匹配订单，后台自动平摊拆分流水并对冲账目！")
                        st.cache_data.clear(); st.rerun()

    # 修改功能
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
                p_edit_reason = st.text_area("🔧 请硬性输入本次项目调整/修正的原因备注 * (必填)")

                if st.button("💾 覆写并保存项目修改"):
                    if not p_edit_reason.strip(): st.error("❌ 必须填写修改原因才能提交！")
                    else:
                        trace_stamp = f" [修改痕迹 {datetime.now().strftime('%Y-%m-%d')}: {p_edit_reason.strip()}]"
                        up_payload = {"name": up_p_name, "client": up_p_client, "target": up_p_target, "stage": up_p_stage + trace_stamp, "bid_date": up_p_date}
                        res = requests.patch(f"{SB_URL}/rest/v1/projects?id=eq.{pid_edit}", headers=HEADERS, json=up_payload, timeout=5)
                        if res.status_code in [200, 204]: st.success("🎉 框架项目已成功更正！"); st.cache_data.clear(); st.rerun()

        elif edit_target == "🤝 修改订单明细":
            if not orders: st.info("云端暂无订单数据可修改")
            else:
                o_edit_opts = {f"订单号:{oid} | {o['order_p_name']}": oid for oid, o in orders.items()}
                sel_edit_o = st.selectbox("请选择要更正的正式订单：", list(o_edit_opts.keys())); oid_edit = o_edit_opts[sel_edit_o]; old_o = orders[oid_edit]
                up_o_province = st.text_input("省份", value=old_o["province"])
                up_o_client = st.text_input("客户简称", value=old_o["client"])
                up_o_product = st.text_input("订单产品(去除旧留档后缀)", value=old_o["product"].split(" [修改痕迹")[0])
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
                o_edit_reason = st.text_area("🔧 请硬性输入本次订单调整/修正的原因备注 * (必填)")

                if st.button("💾 覆写并保存订单修改"):
                    if not o_edit_reason.strip(): st.error("❌ 必须填写修改原因才能提交！")
                    else:
                        trace_stamp = f" [修改痕迹 {datetime.now().strftime('%Y-%m-%d')}: {o_edit_reason.strip()}]"
                        up_o_payload = {"province": up_o_province, "client": up_o_client, "product": up_o_product + trace_stamp, "order_p_name": up_o_p_name, "price_no_tax": up_price, "tax_rate": up_tax_rate, "quantity": up_qty, "amt_no_tax": new_no_tax, "amt_with_tax": new_tax_in, "order_date": up_o_date}
                        res = requests.patch(f"{SB_URL}/rest/v1/orders?id=eq.{oid_edit}", headers=HEADERS, json=up_o_payload, timeout=5)
                        if res.status_code in [200, 204]: st.success("🎉 订单财务明细已成功更正！"); st.cache_data.clear(); st.rerun()
