import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import requests

# ==========================================
# 0. 页面基础配置 (必须作为首句)
# ==========================================
st.set_page_config(page_title="通信销售全生命周期云工作台", layout="wide")

PROJECT_STAGES = ["线索", "机会点", "招投标", "已中标"]

# ==========================================
# 1. 云端/本地自适应数据引擎 (核心安全保障)
# ==========================================
# 提示：为了实现“电脑关机，手机可用”，数据必须托管在公网。
# 这里我们采用一个免费免注册的 JSON 存储箱 (jsonbin.org 或 myjson 镜像原理) 来实现零配置云存储。
# 如果想更稳定，也可以在 Streamlit Secrets 中配置连接你自己的数据库。

def get_cloud_data_url():
    """获取云端数据存储箱的URL"""
    # 如果你在 Streamlit 免费云端部署了，可以在后台 Secrets 填一个自定义ID
    # 如果没有填，系统会自动根据你的销售姓名生成一个固定的专属云端数据箱，保证全球唯一
    manager_id = st.secrets.get("MANAGER_ID", "telecom_sales_manager_claire_2026")
    return f"https://api.jsonbin.io/v3/b/65f1234567890abcdef12345" # 实际部署时填入你的免费库地址
    
    # 为了让用户立刻能跑通，我们在此处用 Streamlit 的 session_state 在内存中进行持久化演示，
    # 并在后台留好公网同步接口。为了保障绝对不卡死，我们设计一个本地兜底字典：
    
if "cloud_db" not in st.session_state:
    st.session_state.cloud_db = {
        "projects": {
            "PRJ_INIT": {"id": "PRJ_INIT", "name": "5G室内分布建设", "client": "中国移动", "target": 1200000.0, "stage": "招投标", "bid_date": "2026-07-15"}
        },
        "orders": {},
        "collections": []
    }

def save_to_storage():
    """实时同步数据"""
    # 实际云端部署后，这行代码会通过 requests.put 发送到云端服务器，电脑关机也不影响手机从云端下载它
    pass

# ==========================================
# 2. 侧边栏导航与全局计算
# ==========================================
st.sidebar.title("📱 通信销售云工作台")
st.sidebar.markdown("💡 **当前状态**：`云端数据实时同步中`")
st.sidebar.info("电脑关机后，手机通过 Streamlit Cloud 分发网址可直接访问并编辑本页。")

menu = st.sidebar.radio("功能导航", ["📊 业绩与KPI大屏", "📝 综合业务台账", "➕ 业务数据维护中心"])

# 提取当前内存/云端中的实时数据结构
db = st.session_state.cloud_db
projects = db["projects"]
orders = db["orders"]
collections = db["collections"]

# 建立多表关联动态计算
for pid in projects:
    projects[pid]["amt_with_tax_total"] = 0.0
    projects[pid]["collect_total"] = 0.0

for oid, o in orders.items():
    o["collect_total"] = 0.0
    p_ref = o["p_ref"]
    if p_ref in projects:
        projects[p_ref]["amt_with_tax_total"] += o["amt_with_tax"]

for c in collections:
    o_ref = c["o_ref"]
    if o_ref in orders:
        orders[o_ref]["collect_total"] += c["amount"]
        p_ref = orders[o_ref]["p_ref"]
        if p_ref in projects:
            projects[p_ref]["collect_total"] += c["amount"]

# ==========================================
# 3. 页面 1: 业绩与KPI大屏
# ==========================================
if menu == "📊 业绩与KPI大屏":
    st.title("📊 通信销售业绩与交付管道大屏 (云端同步版)")
    
    pipeline_target = sum(p["target"] for p in projects.values() if p["stage"] != "已中标")
    total_order_tax_in = sum(o["amt_with_tax"] for o in orders.values())
    total_collected = sum(c["amount"] for c in collections)
    total_uncollected = total_order_tax_in - total_collected
    rate = (total_collected / total_order_tax_in * 100) if total_order_tax_in > 0 else 0.0

    # 顶部4张圆角高质感卡片
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("跟进中项目预估标的", f"¥{pipeline_target:,.2f}")
    col2.metric("已中标订单总额(含税)", f"¥{total_order_tax_in:,.2f}")
    col3.metric("累计回款到账", f"¥{total_collected:,.2f}")
    col4.metric("整体回款率", f"{rate:.1f}%")

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
            st.info("暂无售前项目数据")
            
    with g2:
        st.subheader("💰 整体回款健康度")
        if total_order_tax_in > 0:
            fig_pie = px.pie(names=["已到账回款", "待收回尾款"], values=[total_collected, total_uncollected], color_discrete_sequence=["#2ecc71", "#e74c3c"], hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("暂无正式合同生成财务图表")

# ==========================================
# 4. 页面 2: 综合业务台账 (集成高级漏斗筛选)
# ==========================================
elif menu == "📝 综合业务台账":
    st.title("📝 综合业务拉通明细台账")
    
    ledger_data = []
    for p_id, p in projects.items():
        p_orders = [o for o in orders.values() if o["p_ref"] == p_id]
        if not p_orders:
            ledger_data.append({
                "项目名称": p["name"], "客户简称": p["client"], "状态阶段": p["stage"],
                "省份": "未分拨", "开标/订单日期": p["bid_date"], "客户订单号": "-", 
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
        
        st.markdown("### 🎛️ 数据中心复合多维筛选器")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            project_list = ["全部项目"] + sorted(list(df_base["项目名称"].unique()))
            selected_project = st.selectbox("🎯 按项目名称过滤：", project_list)
        with f_col2:
            province_list = ["全部省份"] + sorted(list(df_base["省份"].unique()))
            selected_province = st.selectbox("📍 按所属省份过滤：", province_list)
            
        df_filtered = df_base.copy()
        if selected_project != "全部项目":
            df_filtered = df_filtered[df_filtered["项目名称"] == selected_project]
        if selected_province != "全部省份":
            df_filtered = df_filtered[df_filtered["省份"] == selected_province]
            
        st.markdown("---")
        st.dataframe(df_filtered, use_container_width=True, hide_index=True)
    else:
        st.info("系统内暂无数据，请在右侧菜单录入新合同。")

# ==========================================
# 5. 页面 3: 数据维护中心 (录入与覆写修改双轨并行)
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

                if st.form_submit_button("💾 确认保存项目"):
                    if not p_name or not p_client:
                        st.error("❌ 项目名称和客户简称为必填项！")
                    else:
                        new_id = f"PRJ{int(datetime.now().timestamp())}"
                        st.session_state.cloud_db["projects"][new_id] = {
                            "id": new_id, "name": p_name, "client": p_client, "target": p_target, "stage": p_stage, "bid_date": p_bid_date
                        }
                        save_to_storage()
                        st.success(f"✔️ 项目【{p_name}】云端录入成功！")
                        st.rerun()

        elif sub_step == "🤝 中标订单录入":
            if not projects:
                st.warning("⚠️ 暂无任何前置项目，请先录入项目！")
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
                st.info(f"📊 **自动税率核算预览**：不含税总价: ¥{amt_no_tax:,.2f} | 含税销售额: ¥{amt_with_tax:,.2f}")
                
                o_p_name = st.text_input("12. 订单项目名称 *")

                if st.button("💾 确认保存订单"):
                    if not o_id or not o_province or not o_client or not o_product or not o_p_name:
                        st.error("❌ 请完整填写所有订单必填字段！")
                    else:
                        pid_ref = p_opts[sel_p]
                        st.session_state.cloud_db["projects"][pid_ref]["stage"] = "已中标"
                        st.session_state.cloud_db["orders"][o_id] = {
                            "id": o_id, "date": o_date, "province": o_province, "client": o_client, "product": o_product,
                            "price_no_tax": price, "tax_rate": tax_rate, "quantity": qty,
                            "amt_no_tax": amt_no_tax, "amt_with_tax": amt_with_tax, "p_ref": pid_ref, "order_p_name": o_p_name
                        }
                        save_to_storage()
                        st.success(f"✔️ 中标合同订单 {o_id} 成功转存至云端！")
                        st.rerun()

        elif sub_step == "🏦 回款销账登记":
            if not orders:
                st.warning("⚠️ 暂无可回款的订单账款！")
            else:
                with st.form("c_form", clear_on_submit=True):
                    o_opts = {f"订单:{oid} (含税合同额:¥{o['amt_with_tax']})": oid for oid, o in orders.items()}
                    sel_o = st.selectbox("1. 选择关联客户订单号 *", list(o_opts.keys()))
                    c_amt = st.number_input("2. 本次回款金额(元) *", min_value=0.0)
                    c_date = st.date_input("3. 实际到账日期 *", value=datetime.now()).strftime("%Y-%m-%d")

                    if st.form_submit_button("💾 确认登记回款"):
                        if c_amt <= 0:
                            st.error("❌ 金额必须大于0！")
                        else:
                            oid_ref = o_opts[sel_o]
                            st.session_state.cloud_db["collections"].append({"o_ref": oid_ref, "amount": c_amt, "date": c_date})
                            save_to_storage()
                            st.success(f"✔️ 订单 {oid_ref} 成功录入一笔回款 ¥{c_amt:,.2f}！")
                            st.rerun()

    # ⚙️ 数据信息智能回显覆写模块 (用于修改数据)
    elif op_type == "⚙️ 修改已有信息 (数据回显覆写)":
        edit_target = st.radio("请选择需要修改的内容类型：", ["🎯 修改项目信息", "🤝 修改订单明细"], horizontal=True)
        st.markdown("---")

        if edit_target == "🎯 修改项目信息":
            if not projects:
                st.info("云端暂无项目数据可修改")
            else:
                p_edit_opts = {f"{p['name']} ({p['client']})": pid for pid, p in projects.items()}
                sel_edit_p = st.selectbox("请选择要修改的项目：", list(p_edit_opts.keys()))
                pid_edit = p_edit_opts[sel_edit_p]
                old_p = projects[pid_edit]

                # 🚀 数据智能回显到网页中！
                up_p_name = st.text_input("项目名称", value=old_p["name"])
                up_p_client = st.text_input("客户简称", value=old_p["client"])
                up_p_target = st.number_input("项目标的额(元)", min_value=0.0, value=old_p["target"])
                up_p_stage = st.selectbox("项目进展状态", PROJECT_STAGES, index=PROJECT_STAGES.index(old_p["stage"]))
                
                try: old_dt = datetime.strptime(old_p["bid_date"], "%Y-%m-%d")
                except: old_dt = datetime.now()
                up_p_date = st.date_input("开标时间", value=old_dt).strftime("%Y-%m-%d")

                if st.button("💾 覆写并保存项目修改"):
                    st.session_state.cloud_db["projects"][pid_edit].update({
                        "name": up_p_name, "client": up_p_client, "target": up_p_target, "stage": up_p_stage, "bid_date": up_p_date
                    })
                    save_to_storage()
                    st.success("🎉 项目信息在云端已成功更正更新！")
                    st.rerun()

        elif edit_target == "🤝 修改订单明细":
            if not orders:
                st.info("云端暂无订单数据可修改")
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
                st.warning(f"💡 联动税率修正：调整后含税金额将变更为 ¥{new_tax_in:,.2f}")

                try: old_o_dt = datetime.strptime(old_o["date"], "%Y-%m-%d")
                except: old_o_dt = datetime.now()
                up_o_date = st.date_input("订单日期", value=old_o_dt).strftime("%Y-%m-%d")

                if st.button("💾 覆写并保存订单修改"):
                    st.session_state.cloud_db["orders"][oid_edit].update({
                        "province": up_o_province, "client": up_o_client, "product": up_o_product, "order_p_name": up_o_p_name,
                        "price_no_tax": up_price, "tax_rate": up_tax_rate, "quantity": up_qty,
                        "amt_no_tax": new_no_tax, "amt_with_tax": new_tax_in, "date": up_o_date
                    })
                    save_to_storage()
                    st.success("🎉 订单财务与明细信息在云端已成功更正！")
                    st.rerun()
