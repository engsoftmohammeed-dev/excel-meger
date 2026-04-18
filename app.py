import streamlit as st
import pandas as pd
import io
import re

# =========================================================
# ⚙️ إعدادات الإدارة (تحكم بالعميل من هنا)
# =========================================================
CLIENT_USERNAME = "shop_759"
CLIENT_PASSWORD = "759"
SYSTEM_ACTIVE = True  # غيرها إلى False لغلق الحساب

# دالة تفكيك الجملة
def parse_lead_info(text):
    text = str(text)
    parts = text.split()
    province = parts[0] if len(parts) > 0 else "غير محدد"
    quantity = 1
    if "عدد" in text:
        try:
            qty_match = re.search(r'عدد\s*(\d+)', text)
            if qty_match: quantity = int(qty_match.group(1))
        except: pass
    area = ""
    if "عدد" in text:
        try: area = text.split(province)[-1].split("عدد")[0].strip()
        except: area = ""
    else: area = " ".join(parts[1:]) if len(parts) > 1 else ""
    return province, area, quantity

# دالة المعالجة
def process_data(files, prod_name, prod_price):
    all_dfs = [pd.read_excel(f) for f in files]
    combined_df = pd.concat(all_dfs, ignore_index=True)
    final_cols = ['اسم الزبون', 'هاتف الزبون', 'هاتف الزبون 2', 'المحافظة', 'المنطقة', 'المبلغ الكلي', 'نوع البضاعة والعدد المطلوب', 'العدد', 'الملاحظات']
    res = pd.DataFrame(columns=final_cols)
    name_col = next((c for c in combined_df.columns if "name" in str(c).lower()), combined_df.columns[-1])
    res['اسم الزبون'] = combined_df[name_col].fillna("بدون اسم").str.strip()
    phone_col = next((c for c in combined_df.columns if "هاتف" in str(c) or "phone" in str(c).lower()), combined_df.columns[-2])
    res['هاتف الزبون'] = combined_df[phone_col].astype(str).str.strip()
    mixed_col = next((c for c in combined_df.columns if "المحافظة" in str(c)), combined_df.columns[-3])
    parsed_data = combined_df[mixed_col].apply(parse_lead_info)
    res['المحافظة'] = [x[0] for x in parsed_data]
    res['المنطقة'] = [x[1] for x in parsed_data]
    res['العدد'] = [x[2] for x in parsed_data]
    res['المبلغ الكلي'] = prod_price
    res['نوع البضاعة والعدد المطلوب'] = res['العدد'].apply(lambda x: f"{prod_name} عدد {x}")
    res['هاتف الزبون 2'] = ""; res['الملاحظات'] = ""
    res = res[~res['اسم الزبون'].str.contains('تست|تجربة|test', case=False, na=False)]
    res.drop_duplicates(subset=['هاتف الزبون'], keep='first', inplace=True)
    return res[final_structure] if 'final_structure' in locals() else res

# واجهة المستخدم
st.set_page_config(page_title="سيستم دمج الليدات", layout="wide")
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔐 تسجيل الدخول")
    u = st.text_input("اسم المستخدم"); p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if u == CLIENT_USERNAME and p == CLIENT_PASSWORD:
            if SYSTEM_ACTIVE: st.session_state.auth = True; st.rerun()
            else: st.error("🚫 الحساب معطل.")
        else: st.error("❌ بيانات خطأ")
else:
    st.title("📦 نظام تجميع ومعالجة الطلبات الموحد")
    with st.expander("🛠️ إعدادات الشحنة", expanded=True):
        c1, c2 = st.columns(2)
        product = c1.text_input("نوع البضاعة"); price = c2.number_input("السعر للقطعة", value=25000)
    files = st.file_uploader("ارفع ملفات الإكسل", type=['xlsx'], accept_multiple_files=True)
    if st.button("🔄 بدء المعالجة", use_container_width=True, type="primary"):
        if files:
            st.session_state.data = process_data(files, product, price)
            st.success("تمت المعالجة بنجاح!")
    if 'data' in st.session_state and st.session_state.data is not None:
        st.dataframe(st.session_state.data, use_container_width=True)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            st.session_state.data.to_excel(writer, index=False)
        st.download_button("📥 تحميل ملف الإكسل النهائي", output.getvalue(), file_name="final_orders.xlsx", use_container_width=True)
