import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests

# ==========================================
# 0. 页面基础配置 (必须作为首句)
# ==========================================
st.set_page_config(page_title="通信销售全生命周期 Supabase 云工作台", layout="wide")

PROJECT_STAGES = ["线索", "机会点", "招投标", "已中标"]

# ==========================================
# 1. 🚀 官方 API 高速安全驱动引擎 (已全面修复语法)
# ==========================================
try:
    SB_URL = st.secrets["secrets"]["SUPABASE_URL"]
    SB_KEY = st.secrets["secrets"]["SUPABASE_KEY"]
    HEADERS = {
        "apikey": SB_KEY,
        "Authorization": f"Bearer {SB_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"  # 强制要求云端返回操作结果，防止静默失败
    }
except Exception as e:
    st.error("⚠️ 获取凭证失败！请检查 Streamlit 后台 Secrets 是否正确填入 SUPABASE_URL 和 SUPABASE_KEY。")
    st.stop()

@st.cache_data(ttl=2) # 💡 2秒缓存，既能降压，又能多端无缝秒级同步
def load_db_data():
    """通过 443 端口的标准 HTTPS 接口，实时读取 Supabase 云数据库数据"""
    try:
        res_p = requests.get(f"{SB_URL}/rest/v1/projects?select=*", headers=HEADERS, timeout=5).json()
        res_o = requests.get(f"{SB_URL}/rest/v1/orders?select=*", headers=HEADERS, timeout=5).json()
        res_c = requests.get(f"{SB_URL}/rest/v1/collections?select=*", headers=HEADERS, timeout=5).json()
    except Exception as e:
        st.error(f"📡 连不上云数据库，网络握手超时！请检查配置。详情: {e}")
        return {}, {}, []

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
                "p_ref": row['project_ref'], "order_p_name": row['order_p_name'], "collect_total": 0.0
            }
        
    collections_list = []
    if isinstance(res_c, list):
        for row in res_c:
            collections_list.append({
                "o_ref": row['order_ref'], "amount": float(row['amount']), "date": str(row['collection_date'])
            })
        
    # 交叉核算多表联动财务逻辑
    for oid, o in orders_dict.items():
        if o["p_ref"] in projects_dict:
            projects_dict[o["p_ref"]]["amt_with_tax_total"] += o["amt_with_tax"]
            
    for c in collections_list:
        if c["o_ref"] in orders_dict:
            orders_dict[c["o_ref"]]["collect_total"] += c["amount"]
            p_ref = orders_dict[c["o_ref"]]["p_ref"]
            if p_ref in projects_dict:
                projects_dict[p_ref]["collect_total"] += c["amount"]

    return projects_dict, orders_dict, collections_list

# 强制加载最新云数据
st.cache_data.clear() # 确保每次重载全盘刷清
projects, orders, collections = load_db_data()

# ==========================================
# 2. 侧边栏导航控制
# ==========================================
st.sidebar.title("📱 通信销售云工作台")
st.sidebar.markdown("💡 **数据同步引擎**：`🟢 Supabase REST 高速安全通道已就绪`")
menu = st.sidebar.radio("功能导航", ["📊 业绩与KPI大屏", "📝 综合业务台账", "➕ 业务数据维护中心"])

# ==========================================
# 3. 页面 1: 业绩与KPI大屏
# ==========================================
if menu == "📊 业绩与KPI大屏":
    st.title("📊 通信销售业绩与交付管道大屏")
    
    pipeline_target = sum(p["target"] for p in projects.values() if p["stage"] != "已中标")
    total_order_tax_in = sum(o["amt_with_tax"] for o in orders.values())
    total_collected = sum(c["amount"] for c in collections)
    total_uncollected = total_order_tax_in - total_collected
    rate = (total_collected / total_order_tax_in * 100) if total_order_tax_in > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("跟进中项目预估标的", f"¥{pipeline_target:,.2f}")
    col2.metric("已中标订单总额(含税)", f"¥{total_order_tax_in:,.2f}")
    col3.metric("累计回款到账", f"¥{total_collected:,.2f}")
    col4.metric("整体合同回款率", f"{rate:.1f}%")

    st.markdown("---")
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("🚧 售前项目交付管线分布")
        stage_list = [p["stage"] for p in projects.values()]
        if stage_list:
            df_stage = pd.DataFrame(stage_list, columns=["阶段"])
            fig = px.histogram(df_stage, x="阶段", color="阶段", category_orders={"阶段": PROJECT_STAGES})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无售前项目管道分布数据")
    with g2:
        st.subheader("💰 整体已中标订单回款健康度")
        if total_order_tax_in > 0:
            fig_pie = px.pie(names=["已到账回款", "待收回尾款"], values=[total_collected, total_uncollected], color_discrete_sequence=["#2ecc71", "#e74c3c"], hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("暂无正式中标合同生成财务图表")

# ==========================================
# 4. 页面 2: 综合业务台账
# ==========================================
elif menu == "📝 综合业务台账":
    st.title("📝 综合业务拉通明细台账")
    ledger_data = []
    for p_id, p in projects.items():
        p_orders = [o for o in orders.values() if o["p_ref"] == p_id]
        if not p_orders:
            ledger_data.append({
                "项目名称": p["name"], "客户简称": p["client"], "状态阶段": p["stage"],
                "省份": "未分拨(售前)", "开标/订单日期": p["bid_date"], "客户订单号": "-", 
                "产品": "-", "数量": 0, "不含税总额": 0.0, "订单含税金额": 0.0, "待回尾款": 0.0
            })
        else:
            for o in p_orders:
                uncollected = o["amt_with_tax"] - o["collect_total"]
                ledger_data.append({
                    "项目名称": p["name"], "客户简称": o["client"], "状态阶段": "已中标转订单",
                    "省份": o["province"], "开标/订单日期": o["date"], "客户订单号": o["id"], 
                    "产品": o["product"], "数量": int(o["quantity"]), "不含税总额": o["amt_no_tax"], 
                    "订单含税金额": o["amt_with_tax"], "待回尾款": uncollected
                })

    if ledger_data:
        df_base = pd.DataFrame(ledger_data)
        st.markdown("### 🎛️ 数据中心多维筛选控制面板")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            project_list = ["全部项目"] + sorted(list(df_base["项目名称"].unique()))
            selected_project = st.selectbox("🎯 按关联项目名称过滤：", project_list)
        with f_col2:
            province_list = ["全部省份"] + sorted(list(df_base["省份"].unique()))
            selected_province = st.selectbox("📍 按所属区域省份过滤：", province_list)
            
        df_filtered = df_base.copy()
        if selected_project != "全部项目":
            df_filtered = df_filtered[df_filtered["项目名称"] == selected_project]
        if selected_province != "全部省份":
            df_filtered = df_filtered[df_filtered["省份"] == selected_province]
            
        st.markdown("---")
        st.dataframe(df_filtered, use_container_width=True, hide_index=True)
    else:
        st.info("云端数据库内暂无业务数据。")

# ==========================================
# 5. 页面 3: 业务数据维护中心 (已全面纠正协议逻辑)
# ==========================================
elif menu == "➕ 业务数据维护中心":
    st.title("🛠️ 业务数据全生命周期维护中心")
    op_type = st.radio("请选择您要执行的维护类型：", ["🆕 录入全新数据", "⚙️ 修改已有信息 (数据回显覆写)"], horizontal=True)
    st.markdown("---")

    if op_type == "🆕 录入全新数据":
        sub_step = st.radio("请选择录入的业务阶段：", ["🎯 项目前期录入", "🤝 中标订单录入", "🏦 回款销账登记"], horizontal=True)
        st.markdown("---")

        if sub_step == "🎯 项目前期录入":
            with st.form("p_form", clear_on_submit=True):
                p_name = st.text_input("1. 项目名称 *")
                p_client = st.text_input("2. 客户简称 *")
                p_target = st.number_input("3. 项目标的额 (元) *", min_value=0.0, step=10000.0)
                p_stage = st.selectbox("4. 项目阶段 *", PROJECT_STAGES)
                p_bid_date = st.date_input("5. 开标时间 *", value=datetime.now()).strftime("%Y-%m-%d")

                if st.form_submit_button("💾 确认保存至 Supabase"):
                    if not p_name or not p_client:
                        st.error("❌ 项目名称和客户简称为必填项！")
                    else:
                        new_id = f"PRJ{int(datetime.now().timestamp())}"
                        payload = {"id": new_id, "name": p_name, "client": p_client, "target": p_target, "stage": p_stage, "bid_date": p_bid_date}
                        res = requests.post(f"{SB_URL}/rest/v1/projects", headers=HEADERS, json=payload, timeout=5)
                        if res.status_code in [200, 201]:
                            st.success(f"✔️ 项目【{p_name}】已经通过 API 写入云端！")
                            st.cache_data.clear() # 刷清缓存
                            st.rerun()
                        else:
                            st.error(f"写入失败，请检查数据库权限或表名结构！错误响应: {res.text}")

        elif sub_step == "🤝 中标订单录入":
            if not projects:
                st.warning("⚠️ 暂无任何前置项目，请先前往项目前期录入！")
            else:
                p_opts = {f"{p['name']} ({p['client']})": pid for pid, p in projects.items()}
                sel_p = st.selectbox("11. 关联源头项目 *", list(p_opts.keys()))
                o_id = st.text_input("1. 客户订单号 *")
                o_date = st.date_input("2. 订单日期 *", value=datetime.now()).strftime("%Y-%m-%d")
                o_province = st.text_input("3. 省份 *")
                o_client = st.text_input("4. 客户简称 *")
                o_product = st.text_input("5. 订单产品 *")

                cp, cr, cq = st.columns(3)
                price = cp.number_input("6. 单价(不含税/元) *", min_value=0.0)
                tax_rate = cr.number_input("7. 税率 *", min_value=0.0, max_value=1.0, value=0.13)
                qty = cq.number_input("8. 数量 *", min_value=1, value=1)

                amt_no_tax = price * qty
                amt_with_tax = amt_no_tax * (1 + tax_rate)
                st.info(f"📊 不含税总价: ¥{amt_no_tax:,.2f} | 含税销售额: ¥{amt_with_tax:,.2f}")
                o_p_name = st.text_input("12. 订单项目名称 *")

                if st.button("💾 确认保存订单"):
                    if not o_id or not o_province or not o_client or not o_product or not o_p_name:
                        st.error("❌ 请完整填写带有 * 的必填字段！")
                    else:
                        pid_ref = p_opts[sel_p]
                        # 💡 纠正语法：PostgREST 更新单条数据需使用标准 eq. 语法进行网络穿透
                        requests.patch(f"{SB_URL}/rest/v1/projects?id=eq.{pid_ref}", headers=HEADERS, json={"stage": "已中标"}, timeout=5)
                        
                        o_payload = {"id": o_id, "project_ref": pid_ref, "order_date": o_date, "province": o_province, "client": o_client, "product": o_product, "price_no_tax": price, "tax_rate": tax_rate, "quantity": qty, "amt_no_tax": amt_no_tax, "amt_with_tax": amt_with_tax, "order_p_name": o_p_name}
                        res = requests.post(f"{SB_URL}/rest/v1/orders", headers=HEADERS, json=o_payload, timeout=5)
                        if res.status_code in [200, 201]:
                            st.success(f"✔️ 中标合同订单 {o_id} 云端录入成功！")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"订单写入失败: {res.text}")

        elif sub_step == "🏦 回款销账登记":
            if not orders:
                st.warning("⚠️ 云端数据库内暂无关联订单，无法登记到账款！")
            else:
                with st.form("c_form", clear_on_submit=True):
                    o_opts = {f"订单:{oid} (含税额:¥{o['amt_with_tax']})": oid for oid, o in orders.items()}
                    sel_o = st.selectbox("1. 选择关联客户订单号 *", list(o_opts.keys()))
                    c_amt = st.number_input("2. 本次回款金额(元) *", min_value=0.0)
                    c_date = st.date_input("3. 实际到账日期 *", value=datetime.now()).strftime("%Y-%m-%d")

                    if st.form_submit_button("💾 确认登记回款"):
                        if c_amt <= 0: st.error("❌ 金额必须大于0元！")
                        else:
                            oid_ref = o_opts[sel_o]
                            c_payload = {"order_ref": oid_ref, "amount": c_amt, "collection_date": c_date}
                            res = requests.post(f"{SB_URL}/rest/v1/collections", headers=HEADERS, json=c_payload, timeout=5)
                            if res.status_code in [200, 201]:
                                st.success("✔️ 阶段性财务回款账目已成功录入云端！")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"回款录入失败: {res.text}")

    # 修改功能 (通过 API Patch 覆写更新)
    elif op_type == "⚙️ 修改已有信息 (数据回显覆写)":
        edit_target = st.radio("请选择需要修改的内容类型：", ["🎯 修改项目信息", "🤝 修改订单明细"], horizontal=True)
        st.markdown("---")

        if edit_target == "🎯 修改项目信息":
            if not projects: st.info("云端暂无项目数据可修改")
            else:
                p_edit_opts = {f"{p['name']} ({p['client']})": pid for pid, p in projects.items()}
                sel_edit_p = st.selectbox("请选择要修改的项目：", list(p_edit_opts.keys()))
                pid_edit = p_edit_opts[sel_edit_p]
                old_p = projects[pid_edit]

                up_p_name = st.text_input("项目名称", value=old_p["name"])
                up_p_client = st.text_input("客户简称", value=old_p["client"])
                up_p_target = st.number_input("项目标的额(元)", min_value=0.0, value=old_p["target"])
                up_p_stage = st.selectbox("项目进展状态", PROJECT_STAGES, index=PROJECT_STAGES.index(old_p["stage"]))
                try: old_dt = datetime.strptime(old_p["bid_date"], "%Y-%m-%d")
                except: old_dt = datetime.now()
                up_p_date = st.date_input("开标时间", value=old_dt).strftime("%Y-%m-%d")

                if st.button("💾 覆写并保存项目修改"):
                    up_payload = {"name": up_p_name, "client": up_p_client, "target": up_p_target, "stage": up_p_stage, "bid_date": up_p_date}
                    res = requests.patch(f"{SB_URL}/rest/v1/projects?id=eq.{pid_edit}", headers=HEADERS, json=up_payload, timeout=5)
                    if res.status_code in [200, 204]:
                        st.success("🎉 项目信息在 Supabase 云端已更新覆盖！")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"更新项目失败: {res.text}")

        elif edit_target == "🤝 修改订单明细":
            if not orders: st.info("云端暂无订单数据可修改")
            else:
                o_edit_opts = {f"订单号:{oid} | {o['order_p_name']}": oid for oid, o in orders.items()}
                sel_edit_o = st.selectbox("请选择要修改的订单：", list(o_edit_opts.keys()))
                oid_edit = o_edit_opts[sel_edit_o]
                old_o = orders[oid_edit]

                up_o_province = st.text_input("省份", value=old_o["province"])
                up_o_client = st.text_input("客户简称", value=old_o["client"])
                up_o_product = st.text_input("订单产品", value=old_o["product"])
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

                if st.button("💾 覆写并保存订单修改"):
                    up_o_payload = {"province": up_o_province, "client": up_o_client, "product": up_o_product, "order_p_name": up_o_p_name, "price_no_tax": up_price, "tax_rate": up_tax_rate, "quantity": up_qty, "amt_no_tax": new_no_tax, "amt_with_tax": new_tax_in, "order_date": up_o_date}
                    res = requests.patch(f"{SB_URL}/rest/v1/orders?id=eq.{oid_edit}", headers=HEADERS, json=up_o_payload, timeout=5)
                    if res.status_code in [200, 204]:
                        st.success("🎉 订单明细云端更新覆盖成功！")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"更新订单失败: {res.text}")
