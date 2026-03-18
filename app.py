import streamlit as st
import pandas as pd
import io

# =========================================================
# قاعدة بيانات المشتركين (هنا تخصص كل زبون)
# =========================================================
CLIENTS = {
    "admin": {
        "password": "123",
        "name": "إدارة المنصة الموحدة",
        "logo": "https://cdn-icons-png.flaticon.com/512/906/906343.png",
        "order_prefix": "ADMIN-",
        "theme_color": "#000000"
    },
    "shop_noor": {
        "password": "noor",
        "name": "محل نور للأزياء",
        "logo": "https://cdn-icons-png.flaticon.com/512/3081/3081559.png", # ضع رابط لوغو المحل هنا
        "order_prefix": "NR-",
        "theme_color": "#FF4B4B"
    },
    "iraq_store": {
        "password": "iraq",
        "name": "إيراق ستور للموبايلات",
        "logo": "https://cdn-icons-png.flaticon.com/512/2504/2504814.png",
        "order_prefix": "IQ-",
        "theme_color": "#1f77b4"
    }
}

# =========================================================
# وظائف النظام
# =========================================================

def process_and_merge(files, prod_name, prod_price, client_info):
    all_dfs = []
    for file in files:
        df = pd.read_excel(file)
        all_dfs.append(df)
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    final_cols = ['رقم الوصل', 'اسم الزبون', 'هاتف الزبون', 'هاتف الزبون 2', 
                  'المحافظة', 'المنطقة', 'المبلغ الكلي', 'نوع البضاعة', 'العدد', 'الملاحظات']
    
    res = pd.DataFrame(columns=final_cols)
    res['اسم الزبون'] = combined_df['الاسم'].str.strip() if 'الاسم' in combined_df.columns else ""
    res['هاتف الزبون'] = combined_df['رقم الهاتف'].astype(str).str.strip() if 'رقم الهاتف' in combined_df.columns else ""
    res['المحافظة'] = combined_df['المحافظه'] if 'المحافظه' in combined_df.columns else (combined_df['المحافظة'] if 'المحافظة' in combined_df.columns else "غير محدد")
    
    for col in ['المنطقه واقرب نقطة داله', 'نقطه داله', 'المنطقه']:
        if col in combined_df.columns:
            res['المنطقة'] = combined_df[col]
            break

    res['العدد'] = combined_df['العدد'] if 'العدد' in combined_df.columns else 1
    res['نوع البضاعة'] = prod_name
    res['المبلغ الكلي'] = prod_price
    
    # حذف التكرارات والوهمي
    res = res[~res['اسم الزبون'].str.contains('تست|تجربة|test', case=False, na=False)]
    res.drop_duplicates(subset=['اسم الزبون', 'هاتف الزبون'], keep='first', inplace=True)
    
    # توليد رقم الوصل مع الرمز الخاص بالزبون
    res.reset_index(drop=True, inplace=True)
    res['رقم الوصل'] = [f"{client_info['order_prefix']}{i+1001}" for i in res.index]
    
    return res

# =========================================================
# واجهة المستخدم (UI)
# =========================================================

if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.client_id = ""

if not st.session_state.auth:
    st.set_page_config(page_title="منصة إدارة الطلبات", layout="centered")
    st.image("https://cdn-icons-png.flaticon.com/512/2897/2897832.png", width=100)
    st.title("مرحباً بك في المنصة الموحدة")
    st.subheader("يرجى تسجيل الدخول للوصول إلى أدواتك")
    
    user_input = st.text_input("اسم المستخدم")
    pass_input = st.text_input("كلمة المرور", type="password")
    
    if st.button("دخول للمنصة", use_container_width=True, type="primary"):
        if user_input in CLIENTS and CLIENTS[user_input]['password'] == pass_input:
            st.session_state.auth = True
            st.session_state.client_id = user_input
            st.rerun()
        else:
            st.error("بيانات الدخول غير صحيحة")

else:
    # الحصول على معلومات الزبون الحالي
    client = CLIENTS[st.session_state.client_id]
    
    st.set_page_config(page_title=client['name'], layout="wide")
    
    # الهيدر المخصص للزبون
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        st.image(client['logo'], width=120)
    with col_title:
        st.title(client['name'])
        st.write(f"نظام دمج ومعالجة الطلبات - كود العميل: `{client['order_prefix']}`")

    with st.sidebar:
        st.image(client['logo'], width=100)
        st.write(f"المستخدم: **{st.session_state.client_id}**")
        st.divider()
        if st.button("تسجيل الخروج", use_container_width=True):
            st.session_state.auth = False
            st.rerun()

    # قسم العمل
    st.markdown(f"---")
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            prod = st.text_input("📦 نوع البضاعة الحالية")
        with c2:
            price = st.number_input("💰 السعر الكلي للقطعة", value=25000)

    files = st.file_uploader("ارفع ملفات الإكسل الخاصة بك", type=['xlsx'], accept_multiple_files=True)

    b1, b2 = st.columns(2)
    if b1.button("🔄 بدء المعالجة والدمج", use_container_width=True, type="primary"):
        if files:
            st.session_state.data = process_and_merge(files, prod, price, client)
            st.success(f"تم بنجاح! تم استخدام رمز الوصل: {client['order_prefix']}")
        else:
            st.error("يرجى رفع الملفات")
    
    if b2.button("🗑️ مسح الجلسة", use_container_width=True):
        st.session_state.data = None
        st.rerun()

    if 'data' in st.session_state and st.session_state.data is not None:
        df = st.session_state.data
        st.divider()
        
        # إحصائيات مخصصة
        s1, s2, s3 = st.columns(3)
        s1.metric("عدد الطلبات الحقيقية", len(df))
        s2.metric("إجمالي مبلغ الشحنة", f"{len(df)*price:,} د.ع")
        s3.metric("رمز التتبع", client['order_prefix'])

        st.dataframe(df, use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        st.download_button(
            label=f"📥 تحميل كشف {client['name']}",
            data=output.getvalue(),
            file_name=f"{client['name']}_orders.xlsx",
            use_container_width=True
        )
