import streamlit as st
import pandas as pd
import io
import re

# ==========================================
# الإعدادات
# ==========================================
CLIENT_USERNAME = "shop_759"
CLIENT_PASSWORD = "759"
SYSTEM_ACTIVE = True

# ==========================================
# 🧠 دالة تفكيك النص الاحترافية (تمنع خطأ "عدد")
# ==========================================
def parse_lead_info(text):
    text = str(text).strip()
    if not text or text == 'nan':
        return "غير محدد", "غير محدد", 1
    
    parts = text.split()
    # المحافظة هي أول كلمة دائماً
    province = parts[0] if len(parts) > 0 else "غير محدد"
    
    # استخراج العدد (الرقم الذي يتبع كلمة عدد)
    quantity = 1
    qty_match = re.search(r'عدد\s*(\d+)', text)
    if qty_match:
        quantity = int(qty_match.group(1))
    
    # استخراج المنطقة (الكلام الموجود بين اسم المحافظة وكلمة عدد)
    area = ""
    try:
        # يبحث عن النص المحصور بين (أول كلمة) وكلمة (عدد)
        area_match = re.search(fr'{re.escape(province)}\s*(.*?)\s*عدد', text)
        if area_match:
            area = area_match.group(1).strip()
        else:
            # إذا لم يجد كلمة عدد، يأخذ كل ما بعد المحافظة
            area = " ".join(parts[1:])
    except:
        area = "غير محدد"
        
    return province, area, quantity

# ==========================================
# 🚀 دالة المعالجة وتصحيح أسماء الأعمدة
# ==========================================
def process_data(files, prod_name, prod_price):
    all_dfs = []
    for file in files:
        df = pd.read_excel(file)
        all_dfs.append(df)
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # الفلترة: استبعاد أي عمود يحتوي على (ad_name, campaign, form_id) عند البحث عن اسم الزبون
    excluded_cols = ['ad_name', 'ad_id', 'lead_id', 'campaign', 'form', 'created', 'adgroup']
    
    # 1. البحث عن اسم الزبون الحقيقي (يتجنب اسم الإعلان)
    name_col = next((c for c in combined_df.columns if any(x in str(c).lower() for x in ['full name', 'الاسم الكامل', 'اسم الزبون'])), None)
    if not name_col:
        # إذا لم يجد عمود باسم صريح، يأخذ أول عمود غير مستبعد من القائمة أعلاه
        name_col = next((c for c in combined_df.columns if not any(ex in str(c).lower() for ex in excluded_cols)), combined_df.columns[-1])
    
    # 2. البحث عن عمود الهاتف
    phone_col = next((c for c in combined_df.columns if any(x in str(c) for x in ['هاتف', 'phone', 'موبايل'])), combined_df.columns[-1])
    
    # 3. البحث عن العمود المختلط (المحافظة والمنطقة)
    mixed_col = next((c for c in combined_df.columns if 'المحافظة' in str(c)), combined_df.columns[0])
    
    # بناء الجدول النهائي
    final_cols = ['اسم الزبون', 'هاتف الزبون', 'هاتف الزبون 2', 'المحافظة', 'المنطقة', 'المبلغ الكلي', 'نوع البضاعة والعدد المطلوب', 'العدد', 'الملاحظات']
    res = pd.DataFrame(columns=final_cols)
    
    res['اسم الزبون'] = combined_df[name_col].fillna("بدون اسم").astype(str).str.strip()
    res['هاتف الزبون'] = combined_df[phone_col].astype(str).str.strip()
    
    # تفكيك العمود المختلط
    parsed_data = combined_df[mixed_col].apply(parse_lead_info)
    res['المحافظة'] = [x[0] for x in parsed_data]
    res['المنطقة'] = [x[1] for x in parsed_data]
    res['العدد'] = [x[2] for x in parsed_data]
    
    # تعبئة الباقي
    res['المبلغ الكلي'] = prod_price
    res['نوع البضاعة والعدد المطلوب'] = res['العدد'].apply(lambda x: f"{prod_name} عدد {x}")
    res['هاتف الزبون 2'] = ""
    res['الملاحظات'] = ""
    
    # حذف التكرارات والأسماء الوهمية
    res = res[~res['اسم الزبون'].str.contains('تست|تجربة|test|' + re.escape(prod_name), case=False, na=False)]
    res.drop_duplicates(subset=['هاتف الزبون'], keep='first', inplace=True)
    
    res.reset_index(drop=True, inplace=True)
    return res[final_cols]

# ==========================================
# 🖥️ واجهة العرض
# ==========================================
st.set_page_config(page_title="سيستم الوصولات الذكي", layout="wide")

if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 دخول النظام")
    u = st.text_input("اليوزر"); p = st.text_input("الباسورد", type="password")
    if st.button("دخول"):
        if u == CLIENT_USERNAME and p == CLIENT_PASSWORD and SYSTEM_ACTIVE:
            st.session_state.auth = True; st.rerun()
        else: st.error("بيانات خطأ أو حساب معطل")
else:
    st.title("📦 تجميع طلبات تيك توك وفيسبوك")
    with st.expander("🛠️ إعدادات البضاعة", expanded=True):
        c1, c2 = st.columns(2)
        product = c1.text_input("اسم المنتج (مثال: درنفيس فحص)", value="منتج جديد")
        price = c2.number_input("سعر القطعة", value=25000)

    files = st.file_uploader("ارفع ملفات الإكسل", type=['xlsx'], accept_multiple_files=True)

    if st.button("🔄 بدء المعالجة", use_container_width=True, type="primary"):
        if files:
            st.session_state.data = process_data(files, product, price)
            st.success("تم التجميع بنجاح!")
    
    if 'data' in st.session_state and st.session_state.data is not None:
        st.dataframe(st.session_state.data, use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            st.session_state.data.to_excel(writer, index=False)
        st.download_button("📥 تحميل الإكسل النهائي الموحد", output.getvalue(), file_name="final_orders.xlsx", use_container_width=True)
