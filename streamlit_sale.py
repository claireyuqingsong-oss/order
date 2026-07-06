
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
    """通过 443 端口的标准 HTTPS 接口，实时读取 Supabase 云数据库数据"""
    try:
        res_p = requests.get(f"{SB_URL}/rest/v1/projects?select=*", headers=HEADERS, timeout=5).json()
        res_o = requests.get(f"{SB_URL}/rest/v1/orders?select=*", headers=HEADERS, timeout=5).json()
        res_c = requests.get(f"{SB_URL}/rest/v1/collections?select=*", headers=HEADERS, timeout=5).json()
    except Exception as e:
        st.error(f"📡 连不上云数据库，网络握手超时！详情: {e}")
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
                "p_ref": row.get('project_ref'), "order_p_name": row['order_p_name'], "collect_total": 0.0,
                "is_history": row.get('project_ref') is None # 💡 标记是否为历史老订单
            }
        
    collections_list = []
    if isinstance(res_c, list):
        for row in res_c:
            collections_list.append({
                "o_ref": row['order_ref'], 
                "amount": float(row['amount']), 
                "date": str(row['collection_date']),
                "invoice_no": row.get('invoice_no', '-')
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

    return projects_dict, orders_dict, collections_list

# 强制清空本地缓存以加载最新公网云数据
st.cache_data.clear()
projects, orders, collections = load_db_data()

# ==========================================
# 2. 侧边栏导航控制
# ==========================================
st.sidebar.title("📱 通信销售云工作台")
st.sidebar.markdown("💡 **数据同步引擎**：`🟢 Supabase REST 高速通道已就绪`")
menu = st.sidebar.radio("功能导航", ["📊 业绩与KPI大屏", "📝 综合业务台账", "➕ 业务数据维护中心"])

# ==========================================
# 3. 页面 1: 业绩与KPI大屏 (核心修改：完美隔离历史老账算法)
# ==========================================
if menu == "📊 业绩与KPI大屏":
    st.title("📊 通信销售业绩与交付管道大屏")
    
    # 1. 前期跟进标的求和
    pipeline_target = sum(p["target"] for p in projects.values() if p["stage"] != "已中标")
    
    # 2. 累计税后订单金额：按实际录入的所有订单金额求和（包含主线和历史老账，确保基础数据对得上）
    total_order_tax_in = sum(o["amt_with_tax"] for o in orders.values())
    
    # 3. 累计回款到账：按录入的所有回款金额无条件累加（财务进账纯流水）
    total_collected = sum(c["amount"] for c in collections)
    
    # 💡 4. 核心隔离算法：整体合同回款率计算（剔除老账干扰）
    # 分母：仅计算系统正常主线业务的订单总额
    main_order_total = sum(o["amt_with_tax"] for o in orders.values() if not o["is_history"])
    # 分子：仅计算系统正常主线业务已收到的回款额
    main_collected_total = sum(o["collect_total"] for o in orders.values() if not o["is_history"])
    
    # 真实计算当下核心业务的回款率
    rate = (main_collected_total / main_order_total * 100) if main_order_total > 0 else 0.0
    
    # 真实计算当下核心业务的待催收尾款
    main_uncollected = max(0.0, main_order_total - main_collected_total)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("跟进中项目预估标的", f"¥{pipeline_target:,.2f}")
    col2.metric("累计税后订单/合计数", f"¥{total_order_tax_in:,.2f}")
    col3.metric("累计回款到账(含历史老账)", f"¥{total_collected:,.2f}")
    col4.metric("核心业务合同回款率", f"{rate:.1f}%", help="此指标已自动为您隔离多年前历史老账回款的污染，精准考核主线业务催收率。")

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
        st.subheader("💰 核心主线业务回款健康度")
        if main_order_total > 0:
            fig_pie = px.pie(names=["主线已到账", "主线待追收尾款"], values=[main_collected_total, main_uncollected], color_discrete_sequence=["#2ecc71", "#e74c3c"], hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("暂无核心正式合同订单生成财务图表")

# ==========================================
# 4. 页面 2: 综合业务台账 
# ==========================================
elif menu == "📝 综合业务台账":
    st.title("📝 综合业务拉通明细台账")
    
    st.markdown("### 🎛️ 数据中心快速过滤器")
    f_col1, f_col2 = st.columns(2)
    
    unique_projects = ["全部项目"] + sorted(list(set(p["name"] for p in projects.values())))
    unique_provinces = ["全部省份"] + sorted(list(set(o["province"] for o in orders.values())))
    
    selected_project = f_col1.selectbox("🎯 按关联框架项目名称过滤：", unique_projects)
    selected_province = f_col2.selectbox("📍 按订单所属区域省份过滤：", unique_provinces)
    st.markdown("---")

    # --- 模块 B：框架项目看板 ---
    st.subheader("🎯 前期售前 / 框架项目看板")
    project_rows = []
    for pid, p in projects.items():
        if selected_project != "全部项目" and p["name"] != selected_project:
            continue
            
        ratio = (p["amt_with_tax_total"] / p["target"]) if p["target"] > 0 else 0.0
        
        warning_status = "✅ 安全范围"
        if ratio >= 1.0:
            warning_status = "🚨 严重超标！已爆框架"
        elif ratio >= 0.8:
            warning_status = "⚠️ 额度告急！超过80%"
            
        project_rows.append({
            "项目ID": p["id"],
            "项目/框架名称": p["name"],
            "客户简称": p["client"],
            "框架标的总额": p["target"],
            "已下正式订单含税总额": p["amt_with_tax_total"],
            "框架额度消耗比例": f"{ratio*100:.1f}%",
            "框架安全水位预警": warning_status,
            "开标/创建日期": p["bid_date"],
            "当前状态": p["stage"]
        })
        
    if project_rows:
        df_p_view = pd.DataFrame(project_rows)
        st.dataframe(
            df_p_view.style.map(
                lambda v: "background-color: #ffcccc; color: #cc0000; font-weight: bold;" if "🚨" in str(v) 
                else ("background-color: #fff3cd; color: #856404; font-weight: bold;" if "⚠️" in str(v) else ""),
                subset=["框架安全水位预警"]
            ), 
            use_container_width=True, hide_index=True
        )
    else:
        st.info("暂无符合筛选条件的项目框架信息")

    st.markdown("<br><br>", unsafe_allow_html=True)

    # --- 模块 C：正式中标合同订单明细表 ---
    st.subheader("🤝 已中标正式订单明细表")
    order_rows = []
    for oid, o in orders.items():
        related_p_name = projects[o["p_ref"]]["name"] if o["p_ref"] and o["p_ref"] in projects else "历史老账/无需补录项目"
        
        if selected_project != "全部项目" and related_p_name != selected_project:
            continue
        if selected_province != "全部省份" and o["province"] != selected_province:
            continue
            
        uncollected = max(0.0, o["amt_with_tax"] - o["collect_total"])
        order_rows.append({
            "订单编号": o["id"],
            "订单下发日期": o["date"],
            "区域省份": o["province"],
            "客户简称": o["client"],
            "订购产品明细": o["product"],
            "单价(不含税)": o["price_no_tax"],
            "税率": f"{o['tax_rate']*100:.0f}%",
            "数量": o["quantity"],
            "不含税总额": o["amt_no_tax"],
            "订单含税金额": o["amt_with_tax"],
            "订单项目名称": o["order_p_name"],
            "累计已回款": o["collect_total"],
            "待追收尾款": uncollected,
            "关联源头框架项目": related_p_name 
        })
        
    if order_rows:
        df_o_view = pd.DataFrame(order_rows)
        column_order = [
            "订单编号", "订单下发日期", "区域省份", "客户简称", "订购产品明细", 
            "单价(不含税)", "税率", "数量", "不含税总额", "订单含税金额", 
            "订单项目名称", "累计已回款", "待追收尾款", "关联源头框架项目"
        ]
        df_o_view = df_o_view.reindex(columns=column_order)
        
        s1, s2, s3 = st.columns(3)
        s1.metric("当前筛选正式订单", f"{len(df_o_view)} 笔")
        s2.metric("当前筛选合同含税额", f"¥{df_o_view['订单含税金额'].sum():,.2f}")
        s3.metric("当前筛选待收总尾款", f"¥{df_o_view['待追收尾款'].sum():,.2f}")
        
        st.dataframe(df_o_view, use_container_width=True, hide_index=True)
    else:
        st.info("暂无符合筛选条件的正式合同订单数据")

# ==========================================
# 5. 页面 3: 业务数据维护中心
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
                p_name = st.text_input("1. 项目框架/名称 *")
                p_client = st.text_input("2. 客户简称 *")
                p_target = st.number_input("3. 项目框架标的额 (元) *", min_value=0.0, step=10000.0)
                p_stage = st.selectbox("4. 项目阶段 *", PROJECT_STAGES)
                p_bid_date = st.date_input("5. 开标/签署时间 *", value=datetime.now()).strftime("%Y-%m-%d")

                if st.form_submit_button("💾 确认保存至 Supabase"):
                    if not p_name or not p_client:
                        st.error("❌ 项目名称和客户简称为必填项！")
                    else:
                        new_id = f"PRJ{int(datetime.now().timestamp())}"
                        payload = {"id": new_id, "name": p_name, "client": p_client, "target": p_target, "stage": p_stage, "bid_date": p_bid_date}
                        res = requests.post(f"{SB_URL}/rest/v1/projects", headers=HEADERS, json=payload, timeout=5)
                        if res.status_code in [200, 201]:
                            st.success(f"✔️ 框架项目【{p_name}】已经成功同步写入云端！")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"写入失败: {res.text}")

        elif sub_step == "🤝 中标订单录入":
            if not projects:
                st.warning("⚠️ 暂无任何前置项目，请先完成【项目前期录入】！")
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
                    if not o_id or not o_province or not o_client or not o_product or not o_p_name:
                        st.error("❌ 请完整填写带有 * 的必填订单字段！")
                    else:
                        pid_ref = p_opts[sel_p]
                        requests.patch(f"{SB_URL}/rest/v1/projects?id=eq.{pid_ref}", headers=HEADERS, json={"stage": "已中标"}, timeout=5)
                        
                        o_payload = {"id": o_id, "project_ref": pid_ref, "order_date": o_date, "province": o_province, "client": o_client, "product": o_product, "price_no_tax": price, "tax_rate": tax_rate, "quantity": qty, "amt_no_tax": amt_no_tax, "amt_with_tax": amt_with_tax, "order_p_name": o_p_name}
                        res = requests.post(f"{SB_URL}/rest/v1/orders", headers=HEADERS, json=o_payload, timeout=5)
                        if res.status_code in [200, 201]:
                            st.success(f"✔️ 中标正式合同订单 {o_id} 云端同步成功！")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"订单写入失败: {res.text}")

        elif sub_step == "🏦 回款销账登记":
            is_manual_order = st.checkbox("⏳ 登记多年前的历史老订单回款（切换为手动输入单号，无需在系统补录订单）")
            
            with st.form("c_form", clear_on_submit=True):
                if not is_manual_order:
                    if not orders:
                        st.warning("⚠️ 系统内暂无订单。")
                        st.form_submit_button("不可提交", disabled=True)
                    else:
                        o_opts = {f"订单:{oid} (系统含税额:¥{o['amt_with_tax']})": oid for oid, o in orders.items()}
                        sel_o = st.selectbox("1. 选择要核销的客户订单号 *", list(o_opts.keys()))
                        oid_final = o_opts[sel_o]
                else:
                    oid_final = st.text_input("1. 手动精确输入历史客户订单号 *")

                c_amt = st.number_input("2. 本次财务实际到账回款额 (元) *", min_value=0.0)
                c_date = st.date_input("3. 实际回款进账日期 *", value=datetime.now()).strftime("%Y-%m-%d")
                c_invoice = st.text_input("4. 关联销账发票号 / 财务凭证号 (选填)")

                if st.form_submit_button("💾 确认登记回款"):
                    cleaned_oid = str(oid_final).strip()
                    if not cleaned_oid:
                        st.error("❌ 客户订单号不能为空！")
                    elif c_amt <= 0: 
                        st.error("❌ 回款金额需大于0元！")
                    else:
                        # 💡 完美的历史与现实对冲隔离机制：
                        if is_manual_order and (cleaned_oid not in orders):
                            hedge_payload = {
                                "id": cleaned_oid,
                                "project_ref": None,  # 🌟 关键：不关联任何项目，标记为纯历史归档订单
                                "order_date": c_date,
                                "province": "历史老账归档区",
                                "client": "历史长账龄客户",
                                "product": "跨年历史账目结转款（无需补录明细）",
                                "price_no_tax": c_amt,
                                "tax_rate": 0.0,
                                "quantity": 1,
                                "amt_no_tax": c_amt,
                                "amt_with_tax": c_amt,
                                "order_p_name": "多年前老订单挂账"
                            }
                            requests.post(f"{SB_URL}/rest/v1/orders", headers=HEADERS, json=hedge_payload, timeout=5)
                        
                        # 标准流水登记
                        c_payload = {
                            "order_ref": cleaned_oid, 
                            "amount": c_amt, 
                            "collection_date": c_date,
                            "invoice_no": c_invoice if c_invoice else "-"
                        }
                        res = requests.post(f"{SB_URL}/rest/v1/collections", headers=HEADERS, json=c_payload, timeout=5)
                        if res.status_code in [200, 201]:
                            st.success("🎉 数据安全入库！大屏【主线核心业务回款率】已启用纯净隔离过滤算法！")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"回款录入失败: {res.text}")

    # 修改功能
    elif op_type == "⚙️ 修改已有信息 (数据回显覆写)":
        edit_target = st.radio("请选择需要修改的内容类型：", ["🎯 修改框架项目", "🤝 修改订单明细"], horizontal=True)
        st.markdown("---")

        if edit_target == "🎯 修改框架项目":
            if not projects: st.info("云端暂无数据可修改")
            else:
                p_edit_opts = {f"{p['name']} ({p['client']})": pid for pid, p in projects.items()}
                sel_edit_p = st.selectbox("请选择要修改的框架项目：", list(p_edit_opts.keys()))
                pid_edit = p_edit_opts[sel_edit_p]
                old_p = projects[pid_edit]

                up_p_name = st.text_input("项目框架/名称", value=old_p["name"])
                up_p_client = st.text_input("客户简称", value=old_p["client"])
                up_p_target = st.number_input("框架标的总额(元)", min_value=0.0, value=old_p["target"])
                up_p_stage = st.selectbox("项目进展状态", PROJECT_STAGES, index=PROJECT_STAGES.index(old_p["stage"]))
                try: old_dt = datetime.strptime(old_p["bid_date"], "%Y-%m-%d")
                except: old_dt = datetime.now()
                up_p_date = st.date_input("开标时间", value=old_dt).strftime("%Y-%m-%d")

                if st.button("💾 覆写并保存项目修改"):
                    up_payload = {"name": up_p_name, "client": up_p_client, "target": up_p_target, "stage": up_p_stage, "bid_date": up_p_date}
                    res = requests.patch(f"{SB_URL}/rest/v1/projects?id=eq.{pid_edit}", headers=HEADERS, json=up_payload, timeout=5)
                    if res.status_code in [200, 204]:
                        st.success("🎉 框架项目信息在 Supabase 云端已成功更新覆写！")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"更新项目失败: {res.text}")

        elif edit_target == "🤝 修改订单明细":
            if not orders: st.info("云端暂无订单数据可修改")
            else:
                o_edit_opts = {f"订单号:{oid} | {o['order_p_name']}": oid for oid, o in orders.items()}
                sel_edit_o = st.selectbox("请选择要更正的正式订单：", list(o_edit_opts.keys()))
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
                        st.success("🎉 订单明细及联动核税在云端已成功更新覆写！")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"更新订单失败: {res.text}")
