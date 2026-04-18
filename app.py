import streamlit as st
import pandas as pd
import io
import re

# ==========================================
# 1. إعدادات الدخول
# ==========================================
st.set_page_config(page_title="سيستم دمج الليدات الاحترافي", layout="wide")

if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 تسجيل الدخول")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if u == "shop_759" and p == "759":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("خطأ في البيانات")
    st.stop()

# ==========================================
# 2. دالة تفكيك النص (المحافظة والمنطقة والعدد)
# ==========================================
def parse_lead_info(text):
    text = str(text).strip()
    parts = text.split()
    province = parts[0] if len(parts) > 0 else "غير محدد"
    
    quantity = 1
    qty_match = re.search(r'عدد\s*(\d+)', text)
    if qty_match:
        quantity = int(qty_match.group(1))
    
    area = "المركز"
    try:
        # البحث عن النص بين المحافظة وكلمة عدد
        match = re.search(fr'{re.escape(province)}\s*(.*?)\s*عدد', text)
        if match:
            area = match.group(1).strip()
        else:
            area = " ".join(parts[1:]) if len(parts) > 1 else "المركز"
    except: pass
    
    return province, area, quantity

# ==========================================
# 3. واجهة العمل الرئيسية
# ==========================================
st.title("📦 محول ملفات الليدات إلى وصولات")

# رفع الملفات أولاً لكي نعرف أسماء الأعمدة
uploaded_files = st.file_uploader("ارفع ملفات الإكسل (xlsx)", type=['xlsx'], accept_multiple_files=True)

if uploaded_files:
    # قراءة أول ملف فقط لمعرفة أسماء الأعمدة
    temp_df = pd.read_excel(uploaded_files[0])
    all_columns = temp_df.columns.tolist()

    st.info("💡 يرجى تحديد الأعمدة الصحيحة من ملفك المرفوع:")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        name_col = st.selectbox("اختر عمود (اسم الزبون):", all_columns, index=len(all_columns)-1)
    with col2:
        phone_col = st.selectbox("اختر عمود (رقم الهاتف):", all_columns, index=len(all_columns)-2)
    with col3:
        mixed_col = st.selectbox("اختر عمود (المحافظة والمنطقة):", all_columns, index=0)

    st.divider()
    
    with st.expander("🛠️ إعدادات البضاعة والسعر", expanded=True):
        ca, cb = st.columns(2)
        p_name = ca.text_input("نوع البضاعة", value="اكتب اسم المنتج")
        p_price = cb.number_input("السعر الثابت للقطعة", value=25000)

    if st.button("🚀 بدء المعالجة والدمج فوراً", use_container_width=True, type="primary"):
        all_rows = []
        for f in uploaded_files:
            df = pd.read_excel(f)
            for _, row in df.iterrows():
                prov, area, qty = parse_lead_info(row[mixed_col])
                all_rows.append({
                    'اسم الزبون': str(row[name_col]).strip(),
                    'هاتف الزبون': str(row[phone_col]).strip(),
                    'هاتف الزبون 2': "",
                    'المحافظة': prov,
                    'المنطقة': area,
                    'المبلغ الكلي': p_price,
                    'نوع البضاعة والعدد المطلوب': f"{p_name} عدد {qty}",
                    'العدد': qty,
                    'الملاحظات': ""
                })
        
        final_df = pd.DataFrame(all_rows)
        
        # حذف التكرارات والوهمي
        final_df.drop_duplicates(subset=['هاتف الزبون'], keep='first', inplace=True)
        final_df = final_df[~final_df['اسم الزبون'].str.contains('تست|تجربة|test', case=False, na=False)]
        
        st.success(f"✅ تم دمج {len(final_df)} طلب حقيقي بنجاح!")
        st.dataframe(final_df, use_container_width=True)
        
        # التحميل
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            final_df.to_excel(writer, index=False)
        st.download_button("📥 تحميل ملف الإكسل النهائي", buffer.getvalue(), file_name="final_orders.xlsx", use_container_width=True)
