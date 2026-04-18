import streamlit as st
import pandas as pd
import io
import re

# ==========================================
# 1. إعدادات الوصول والتحكم
# ==========================================
USER_CREDENTIALS = {"shop_759": "759"}
IS_SYSTEM_ACTIVE = True  # غيرها لـ False لتعطيل الحساب

def process_lead_string(text):
    """تفكيك جملة: المحافظة المنطقة عدد X بسعر Y"""
    text = str(text).strip()
    parts = text.split()
    
    # 1. المحافظة (أول كلمة)
    province = parts[0] if len(parts) > 0 else "غير محدد"
    
    # 2. العدد (الرقم بعد كلمة عدد)
    quantity = 1
    qty_search = re.search(r'عدد\s*(\d+)', text)
    if qty_search:
        quantity = int(qty_search.group(1))
    
    # 3. المنطقة (ما بين المحافظة وكلمة عدد)
    area = "غير محدد"
    try:
        # قص النص بين أول كلمة وكلمة عدد
        pattern = f"{re.escape(province)}(.*?)عدد"
        match = re.search(pattern, text)
        if match:
            area = match.group(1).strip()
        else:
            # إذا لم يجد كلمة عدد، يأخذ كل ما بعد المحافظة
            area = " ".join(parts[1:]) if len(parts) > 1 else "المركز"
    except:
        pass
    
    return province, area, quantity

def start_merging(files, p_name, p_price):
    all_data = []
    for f in files:
        df = pd.read_excel(f)
        
        # --- تحديد الأعمدة ذكياً ---
        col_phone = ""
        col_name = ""
        col_mixed = ""
        
        for col in df.columns:
            col_str = str(col).lower()
            # البحث عن عمود الهاتف (يحتوي على أرقام طويلة)
            if any(x in col_str for x in ['phone', 'هاتف', 'موبايل', 'number']):
                col_phone = col
            # البحث عن عمود المحافظة/العنوان (الذي يحتوي على النص المختلط)
            if any(x in col_str for x in ['المحافظة', 'المقدار', 'العنوان']):
                col_mixed = col
            # البحث عن اسم الزبون (نص طويل يستبعد أسماء الإعلانات)
            if any(x in col_str for x in ['name', 'الاسم']) and not any(x in col_str for x in ['ad_', 'campaign', 'form']):
                col_name = col

        # معالجة كل صف في الملف المرفوع
        for _, row in df.iterrows():
            province, area, qty = process_lead_string(row[col_mixed])
            
            all_data.append({
                'اسم الزبون': str(row[col_name]).strip() if col_name else "بدون اسم",
                'هاتف الزبون': str(row[col_phone]).strip() if col_phone else "0",
                'هاتف الزبون 2': "",
                'المحافظة': province,
                'المنطقة': area,
                'المبلغ الكلي': p_price,
                'نوع البضاعة والعدد المطلوب': f"{p_name} عدد {qty}",
                'العدد': qty,
                'الملاحظات': ""
            })

    # تحويل القائمة لجدول
    final_df = pd.DataFrame(all_data)
    
    # تنظيف البيانات
    # 1. حذف التكرارات بناءً على الهاتف
    final_df.drop_duplicates(subset=['هاتف الزبون'], keep='first', inplace=True)
    # 2. حذف الأسماء الوهمية
    exclude = ['تست', 'تجربة', 'test', 'Test']
    final_df = final_df[~final_df['اسم الزبون'].str.contains('|'.join(exclude), na=False)]
    
    return final_df

# ==========================================
# 2. واجهة المستخدم (Streamlit)
# ==========================================
st.set_page_config(page_title="نظام الوصولات الذكي", layout="wide")

if 'login' not in st.session_state: st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 تسجيل دخول المنصة")
    user = st.text_input("اسم المستخدم")
    passw = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if user in USER_CREDENTIALS and USER_CREDENTIALS[user] == passw:
            if IS_SYSTEM_ACTIVE:
                st.session_state.login = True
                st.rerun()
            else: st.error("🚫 الحساب معطل حالياً")
        else: st.error("❌ خطأ في البيانات")
else:
    st.title("📊 تجميع ومعالجة طلبات الليدات")
    
    with st.expander("🛠️ إعدادات البضاعة الحالية", expanded=True):
        c1, c2 = st.columns(2)
        p_name = c1.text_input("اسم المنتج (مثلاً: سيت صلاة)")
        p_price = c2.number_input("سعر القطعة الواحد", value=25000)

    uploaded_files = st.file_uploader("ارفع ملفات الإكسل", type=['xlsx'], accept_multiple_files=True)

    if st.button("🚀 معالجة ودمج الآن", use_container_width=True, type="primary"):
        if uploaded_files:
            result = start_merging(uploaded_files, p_name, p_price)
            st.session_state.final_result = result
            st.success("تمت المعالجة بنجاح!")
        else: st.error("ارفع ملفات أولاً")

    if 'final_result' in st.session_state:
        df = st.session_state.final_result
        st.divider()
        st.dataframe(df, use_container_width=True)
        
        # تصدير للإكسل
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 تحميل الكشف النهائي الموحد", buffer.getvalue(), file_name="kashf_final.xlsx", use_container_width=True)
