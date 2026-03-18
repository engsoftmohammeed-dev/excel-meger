import streamlit as st
import pandas as pd
import io

# ==========================================
# 1. إعدادات الإدارة والاشتراك (تعدلها من هنا)
# ==========================================
ADMIN_USER = "admin"
ADMIN_PW = "admin123"

CLIENT_USER = "shop_759"
CLIENT_PW = "759"

# هذي القيمة تغيرها من هنا لتعطيل الحساب (True = شغال / False = طافي)
IS_ACCOUNT_ACTIVE = True 

# ==========================================
# 2. المظهر (CSS)
# ==========================================
st.set_page_config(page_title="سيستم دمج الإكسل", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .stat-card {
        background-color: white; padding: 15px; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;
        border-top: 4px solid #1f77b4;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 30px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. منطق الدمج (بدون فلاتر - حسب الطلب)
# ==========================================
def merge_logic(files, prod_name, prod_price):
    all_dfs = []
    for f in files:
        try:
            df = pd.read_excel(f)
            all_dfs.append(df)
        except: continue
    
    if not all_dfs: return None
    
    combined = pd.concat(all_dfs, ignore_index=True)
    final_cols = ['رقم الوصل', 'اسم الزبون', 'هاتف الزبون', 'هاتف الزبون 2', 
                  'المحافظة', 'المنطقة', 'المبلغ الكلي', 'نوع البضاعة', 'العدد', 'الملاحظات']
    
    res = pd.DataFrame(columns=final_cols)
    res['اسم الزبون'] = combined['الاسم'] if 'الاسم' in combined.columns else ""
    res['هاتف الزبون'] = combined['رقم الهاتف'] if 'رقم الهاتف' in combined.columns else ""
    res['المحافظة'] = combined['المحافظه'] if 'المحافظه' in combined.columns else (combined['المحافظة'] if 'المحافظة' in combined.columns else "")
    
    # دمج أعمدة المنطقة
    for col in ['المنطقه واقرب نقطة داله', 'نقطه داله', 'المنطقه']:
        if col in combined.columns:
            res['المنطقة'] = combined[col]
            break

    res['نوع البضاعة'] = prod_name
    res['المبلغ الكلي'] = prod_price
    res['العدد'] = combined['العدد'] if 'العدد' in combined.columns else 1
    
    # ترقيم تلقائي
    res.reset_index(drop=True, inplace=True)
    res['رقم الوصل'] = res.index + 1
    
    return res

# ==========================================
# 4. واجهة المستخدم
# ==========================================
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 تسجيل الدخول")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول", use_container_width=True):
        if (u == CLIENT_USER and p == CLIENT_PW) or (u == ADMIN_USER and p == ADMIN_PW):
            st.session_state.auth = True
            st.session_state.user = u
            st.rerun()
        else: st.error("خطأ في البيانات")

else:
    # تحقق من حالة الاشتراك (إيقاف/تشغيل)
    if st.session_state.user == CLIENT_USER and not IS_ACCOUNT_ACTIVE:
        st.error("🚫 عذراً، هذا الحساب معطل حالياً بسبب انتهاء الاشتراك. يرجى التواصل مع الإدارة.")
        if st.button("خروج"):
            st.session_state.auth = False
            st.rerun()
    else:
        # واجهة العمل
        with st.sidebar:
            st.header("⚙️ القائمة")
            st.write(f"المستخدم: {st.session_state.user}")
            if st.button("تسجيل الخروج"):
                st.session_state.auth = False
                st.rerun()
            st.divider()
            if st.session_state.user == ADMIN_USER:
                st.subheader("🛠️ إدارة النظام")
                st.write("الاشتراك مفعل حالياً" if IS_ACCOUNT_ACTIVE else "الاشتراك معطل")

        st.title(f"لوحة تحكم نيرمن للتسوق")
        
        tab1, tab2, tab3 = st.tabs(["📥 رفع البيانات", "📋 عرض البيانات", "📦 التصدير"])

        with tab1:
            st.subheader("Excel رفع ملف")
            c1, c2 = st.columns(2)
            p_name = c1.text_input("نوع البضاعة", value="عام")
            p_price = c2.number_input("السعر", value=25000)
            
            uploaded_files = st.file_uploader("ارفع الملفات هنا", type=['xlsx'], accept_multiple_files=True)
            
            if uploaded_files:
                st.session_state.merged_res = merge_logic(uploaded_files, p_name, p_price)
                st.success("✅ تم استلام الملفات ومعالجتها تلقائياً!")

        with tab2:
            if 'merged_res' in st.session_state and st.session_state.merged_res is not None:
                df = st.session_state.merged_res
                # إحصائيات علوية
                col_m1, col_m2 = st.columns(2)
                col_m1.markdown(f"<div class='stat-card'>إجمالي الطلبات<br><b>{len(df)}</b></div>", unsafe_allow_html=True)
                col_m2.markdown(f"<div class='stat-card'>المبلغ الكلي<br><b>{len(df)*p_price:,}</b></div>", unsafe_allow_html=True)
                
                st.write("<br>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("البيانات ستظهر هنا بعد رفع الملفات.")

        with tab3:
            if 'merged_res' in st.session_state and st.session_state.merged_res is not None:
                st.subheader("تصدير الملف الموحد")
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    st.session_state.merged_res.to_excel(writer, index=False)
                st.download_button("📥 تحميل الإكسل النهائي", output.getvalue(), file_name="merged.xlsx", use_container_width=True, type="primary")
