import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==========================================
# 0. 页面基础配置 (必须作为首句)
# ==========================================
st.set_page_config(page_title="通信销售全生命周期 Supabase 云工作台", layout="wide")

PROJECT_STAGES = ["线索", "机会点", "招投标", "已中标"]

# ==========================================
# 1. 🚀 核心安全驱动：Supabase (PostgreSQL) 云数据库引擎 (强化防断线重连版)
# ==========================================
try:
    db_uri = st.secrets["secrets"]["CONNECTION_STRING"]
    # 💡 增加 connection_kwargs 参数：
    # pool_pre_ping=True 会在每次手机/电脑刷新发起请求前，自动“戳一下”数据库看看是否活着，死掉则自动重连，完美解决休眠断线卡死！
    conn = st.connection(
        "postgresql", 
        type="sql", 
        url=db_uri,
        client_encoding="utf8",
        pool_pre_ping=True,
        pool_recycle=1800
    )
except Exception as e:
    st.error(f"⚠️ 数据库连接失败！请检查 Streamlit 后台 Secrets 是否正确填入 CONNECTION_STRING。")
    st.info("💡 提示：请确认密码是否正确，且端口是否已从 5432 改为了 6543。")
    st.stop()

def load_db_data():
    """从 Supabase 实时读取项目、订单和回款数据，并处理联动计算"""
    # 1. 读取基础表（自动转化为 Pandas DataFrame，设置 ttl=2 秒缓存保证多端同步响应）
    df_p = conn.query("SELECT * FROM projects;", ttl=2)
    df_o = conn.query("SELECT * FROM orders;", ttl=2)
    df_c = conn.query("SELECT * FROM collections;", ttl=2)
    
    # 2. 转化为标准字典结构适配前端业务流
    projects_dict = {}
    if df_p is not None and not df_p.empty:
        for _, row in df_p.iterrows():
            projects_dict[row['id']] = {
                "id": row['id'], "name": row['name'], "client": row['client'],
                "target": float(row['target']), "stage": row['stage'], "bid_date": str(row['bid_date']),
                "amt_with_tax_total": 0.0, "collect_total": 0.0
            }
        
    orders_dict = {}
    if df_o is not None and not df_o.empty:
        for _, row in df_o.iterrows():
            orders_dict[row['id']] = {
                "id": row['id'], "date": str(row['order_date']), "province": row['province'],
                "client": row['client'], "product": row['product'], "price_no_tax": float(row['price_no_tax']),
                "tax_rate": float(row['tax_rate']), "quantity": int(row['quantity']),
                "amt_no_tax": float(row['amt_no_tax']), "amt_with_tax": float(row['amt_with_tax']),
                "p_ref": row['project_ref'], "order_p_name": row['order_p_name'], "collect_total": 0.0
            }
        
    collections_list = []
    if df_c is not None and not df_c.empty:
        for _, row in df_c.iterrows():
            collections_list.append({
                "o_ref": row['order_ref'], "amount": float(row['amount']), "date": str(row['collection_date'])
            })
        
    # 3. 动态核算多表交叉联动财务逻辑
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

# 全局初始化最新公网云端数据
projects, orders, collections = load_db_data()

# ==========================================
# 2. 侧边栏导航控制
# ==========================================
st.sidebar.title("📱 通信销售云工作台")
st.sidebar.markdown("💡 **数据同步引擎**：`🟢 Supabase 全天候分布式架构托管中`")
st.sidebar.write("电脑可随时关机，手机端读写互通无阻。")
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
            st.info("暂无正式中标合同生成财务健康度图表")

# ==========================================
# 4. 页面 2: 综合业务台账 (集成项目/省份复合筛选)
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
        
        # 实时渲染动态筛选后的小计指标
        s1, s2, s3 = st.columns(3)
        s1.metric("当前显示订单笔数", f"{len(df_filtered[df_filtered['客户订单号'] != '-'])} 笔")
        s2.metric("当前筛选含税总额", f"¥{df_filtered['订单含税金额'].sum():,.2f}")
        s3.metric("当前筛选待收尾款", f"¥{df_filtered['待回尾款'].sum():,.2f}")
        
        st.dataframe(df_filtered, use_container_width=True, hide_index=True)
    else:
        st.info("云端数据库内暂无业务数据，请在右侧菜单录入新合同。")

# ==========================================
# 5. 页面 3: 业务数据维护中心 (全面支持 新增 与 修改)
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
                        with conn.session as s:
                            s.execute(
                                "INSERT INTO projects (id, name, client, target, stage, bid_date) VALUES (:id, :name, :client, :target, :stage, :bid_date);",
                                {"id": new_id, "name": p_name, "client": p_client, "target": p_target, "stage": p_stage, "bid_date": p_bid_date}
                            )
                            s.commit()
                        st.success(f"✔️ 项目【{p_name}】安全写入云端成功！")
                        st.rerun()

        elif sub_step == "🤝 中标订单录入":
            if not projects:
                st.warning("⚠️ 暂无任何前置项目，请先完成【项目前期录入】！")
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
                st.info(f"📊 **自动税率核算同步预览**：不含税总价: ¥{amt_no_tax:,.2f} | 含税销售额: ¥{amt_with_tax:,.2f}")
                o_p_name = st.text_input("12. 订单项目名称 *")

                if st.button("💾 确认保存订单"):
                    if not o_id or not o_province or not o_client or not o_product or not o_p_name:
                        st.error("❌ 请完整填写所有订单必填字段！")
                    else:
                        pid_ref = p_opts[sel_p]
                        with conn.session as s:
                            s.execute("UPDATE projects SET stage='已中标' WHERE id=:pid;", {"pid": pid_ref})
                            s.execute(
                                "INSERT INTO orders (id, project_ref, order_date, province, client, product, price_no_tax, tax_rate, quantity, amt_no_tax, amt_with_tax, order_p_name) VALUES (:id, :p_ref, :date, :prov, :cli, :prod, :price, :tax, :qty, :amt_no, :amt_with, :pname);",
                                {"id": o_id, "p_ref": pid_ref, "date": o_date, "prov": o_province, "cli": o_client, "prod": o_product, "price": price, "tax": tax_rate, "qty": qty, "amt_no": amt_no_tax, "amt_with": amt_with_tax, "pname": o_p_name}
                            )
                            s.commit()
                        st.success(f"✔️ 中标合同订单 {o_id} 成功同步至云端！")
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
                        if c_amt <= 0: st.error("❌ 金额必须大于0！")
                        else:
                            oid_ref = o_opts[sel_o]
                            with conn.session as s:
                                s.execute(
                                    "INSERT INTO collections (order_ref, amount, collection_date) VALUES (:o_ref, :amount, :c_date);",
                                    {"o_ref": oid_ref, "amount": c_amt, "c_date": c_date}
                                )
                                s.commit()
                            st.success(f"✔️ 订单 {oid_ref} 成功录入一笔回款！")
                            st.rerun()

    # ⚙️ 智能覆写维护模块
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

                # 数据无损回显
                up_p_name = st.text_input("项目名称", value=old_p["name"])
                up_p_client = st.text_input("客户简称", value=old_p["client"])
                up_p_target = st.number_input("项目标的额(元)", min_value=0.0, value=old_p["target"])
                up_p_stage = st.selectbox("项目进展状态", PROJECT_STAGES, index=PROJECT_STAGES.index(old_p["stage"]))
                try: old_dt = datetime.strptime(old_p["bid_date"], "%Y-%m-%d")
                except: old_dt = datetime.now()
                up_p_date = st.date_input("开标时间", value=old_dt).strftime("%Y-%m-%d")

                if st.button("💾 覆写并保存项目修改"):
                    with conn.session as s:
                        s.execute(
                            "UPDATE projects SET name=:name, client=:client, target=:target, stage=:stage, bid_date=:bid_date WHERE id=:id;",
                            {"name": up_p_name, "client": up_p_client, "target": up_p_target, "stage": up_p_stage, "bid_date": up_p_date, "id": pid_edit}
                        )
                        s.commit()
                    st.success("🎉 Supabase 云端项目修改保存成功！")
                    st.rerun()

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
                st.warning(f"💡 联动税率修正：调整后含税合同总价将重置变更为 ¥{new_tax_in:,.2f}")

                try: old_o_dt = datetime.strptime(old_o["date"], "%Y-%m-%d")
                except: old_o_dt = datetime.now()
                up_o_date = st.date_input("订单日期", value=old_o_dt).strftime("%Y-%m-%d")

                if st.button("💾 覆写并保存订单修改"):
                    with conn.session as s:
                        s.execute(
                            "UPDATE orders SET province=:prov, client=:cli, product=:prod, order_p_name=:pname, price_no_tax=:price, tax_rate=:tax, quantity=:qty, amt_no_tax=:amt_no, amt_with_tax=:amt_with, order_date=:date WHERE id=:id;",
                            {"prov": up_o_province, "cli": up_o_client, "prod": up_o_product, "pname": up_o_p_name, "price": up_price, "tax": up_tax_rate, "qty": up_qty, "amt_no": new_no_tax, "amt_with": new_tax_in, "date": up_o_date, "id": oid_edit}
                        )
                        s.commit()
                    st.success("🎉 订单财务与明细信息云端更新成功！")
                    st.rerun()
