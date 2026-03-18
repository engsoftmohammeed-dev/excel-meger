import streamlit as st
import pandas as pd
import io
import time

# ==========================================
# 1. إعدادات الإدارة والعميل (تعدل من هنا)
# ==========================================
ADMIN_USER = "admin"
ADMIN_PW = "admin123"
CLIENT_USER = "shop_759"
CLIENT_PW = "759"
IS_ACCOUNT_ACTIVE = True  # غيرها لـ False لقفل الموقع

st.set_page_config(page_title="نظام نيرمن المتطور", page_icon="📦", layout="wide")

# تخصيص CSS لتحسين البحث والجدول
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [aria-selected="true"] { background-color: #1f77b4 !important; color: white !important; }
    div[data-testid="stMetric"] { background-color: #f8f9fa; padding: 15px; border-radius: 15px; border-top: 5px solid #1f77b4; }
    /* تحسين خانة البحث */
    .search-box { border: 2px solid #1f77b4 !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. منطق دمج البيانات وسحبها من D و F
# ==========================================
def merge_logic(files):
    all_dfs = []
    for f in files:
        try:
            df_raw = pd.read_excel(f)
            # سحب نوع البضاعة من العمود D (3) أو F (5)
            prod_type = ""
            if df_raw.shape[1] >= 6:
                prod_type = df_raw.iloc[:, 5] if pd.notna(df_raw.iloc[0, 5]) else df_raw.iloc[:, 3]
            elif df_raw.shape[1] >= 4:
                prod_type = df_raw.iloc[:, 3]
            
            temp_df = pd.DataFrame()
            temp_df['الاسم'] = df_raw['الاسم'] if 'الاسم' in df_raw.columns else ""
            temp_df['الهاتف'] = df_raw['رقم الهاتف'] if 'رقم الهاتف' in df_raw.columns else ""
            temp_df['المحافظة'] = df_raw['المحافظه'] if 'المحافظه' in df_raw.columns else (df_raw['المحافظة'] if 'المحافظة' in df_raw.columns else "")
            
            area = ""
            for col in ['المنطقه واقرب نقطة داله', 'نقطه داله', 'المنطقه']:
                if col in df_raw.columns:
                    area = df_raw[col]
                    break
            temp_df['المنطقة'] = area
            temp_df['البضاعة'] = prod_type
            all_dfs.append(temp_df)
        except: continue
    
    if not all_dfs: return None
    
    combined = pd.concat(all_dfs, ignore_index=True)
    res = pd.DataFrame()
    res['اسم الزبون'] = combined['الاسم'].fillna("")
    res['هاتف الزبون'] = combined['الهاتف'].fillna("")
    res['هاتف الزبون 2'] = ""
    res['المحافظة'] = combined['المحافظة'].fillna("")
    res['المنطقة'] = combined['المنطقة'].fillna("")
    res['نوع البضاعة'] = combined['البضاعة'].fillna("")
    res['المبلغ الكلي'] = 0 
    res['العدد'] = 1
    res['الملاحظات'] = ""
    
    # تنظيف شامل لكل الجدول من الـ None
    res = res.applymap(lambda x: "" if pd.isna(x) or x == "None" or x == "nan" else x)
    return res

# ==========================================
# 3. واجهة المستخدم
# ==========================================
if 'auth' not in st.session_state: st.session_state.auth = False
if 'merged_res' not in st.session_state: st.session_state.merged_res = None

if not st.session_state.auth:
    st.title("🔐 تسجيل الدخول")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول", use_container_width=True, type="primary"):
        if (u == CLIENT_USER and p == CLIENT_PW) or (u == ADMIN_USER and p == ADMIN_PW):
            st.session_state.auth = True
            st.session_state.user = u
            st.rerun()
        else: st.error("خطأ في البيانات")

else:
    # فحص الاشتراك
    if st.session_state.user == CLIENT_USER and not IS_ACCOUNT_ACTIVE:
        st.error("🚫 عذراً، الحساب معطل. يرجى مراجعة الإدارة.")
    else:
        with st.sidebar:
            st.header("👔 نيرمن للتسوق")
            st.write(f"المستخدم: {st.session_state.user}")
            if st.button("🚪 تسجيل الخروج", use_container_width=True):
                st.session_state.auth = False
                st.session_state.merged_res = None
                st.rerun()

        tab1, tab2, tab3 = st.tabs(["📤 1. رفع البيانات", "📝 2. بحث وتعديل", "📥 3. تحميل الإكسل"])

        with tab1:
            st.subheader("ارفع ملفات TikTok")
            uploaded_files = st.file_uploader("ارفع الملفات هنا", type=['xlsx'], accept_multiple_files=True)
            if uploaded_files:
                if st.button("🔄 بدء الدمج التلقائي", type="primary", use_container_width=True):
                    with st.spinner('جاري التحميل...'):
                        st.session_state.merged_res = merge_logic(uploaded_files)
                    st.balloons()
                    st.toast('تم الدمج بنجاح!')

        with tab2:
            if st.session_state.merged_res is not None:
                # عرض الإحصائيات
                df_main = st.session_state.merged_res
                total_orders = len(df_main)
                # تحويل المبالغ لأرقام للحساب
                total_sum = pd.to_numeric(df_main['المبلغ الكلي'], errors='coerce').sum()
                
                c1, c2, c3 = st.columns(3)
                c1.metric("عدد الطلبات", f"{total_orders}")
                c2.metric("إجمالي المبالغ", f"{total_sum:,} د.ع")
                c3.metric("الحالة", "نشط ✅")

                st.divider()
                
                # --- خانة البحث الواضحة جداً ---
                st.subheader("🔍 ابحث عن أي اسم أو هاتف")
                search_term = st.text_input("اكتب الاسم أو الرقم هنا للفلترة:", placeholder="مثال: وليد")

                # فلترة البيانات حسب البحث
                if search_term:
                    mask = df_main.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
                    df_filtered = df_main[mask]
                else:
                    df_filtered = df_main

                st.info("💡 للتسعير: اضغط على الخانة واكتب. للحذف: حدد الصف من اليسار واضغط Delete من الكيبورد.")
                
                # --- الجدول التفاعلي (معدل للحذف والتعديل) ---
                edited_df = st.data_editor(
                    df_filtered,
                    use_container_width=True,
                    num_rows="dynamic", # يسمح بحذف وإضافة صفوف
                    key="data_editor_key"
                )
                
                # حفظ التعديلات أو الحذف في الذاكرة
                if search_term:
                    # تحديث البيانات الأصلية بما تم تعديله في البحث
                    st.session_state.merged_res.update(edited_df)
                else:
                    st.session_state.merged_res = edited_df

            else:
                st.info("يرجى رفع الملفات أولاً في التبويب الأول.")

        with tab3:
            if st.session_state.merged_res is not None:
                st.subheader("📥 تنزيل الملف النهائي")
                
                # إضافة رقم وصل نهائي قبل التحميل
                final_to_download = st.session_state.merged_res.copy()
                final_to_download.insert(0, 'رقم الوصل النهائي', range(1, len(final_to_download) + 1))
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    final_to_download.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 تحميل ملف الإكسل الموحد (xlsx)",
                    data=output.getvalue(),
                    file_name="nermin_final_orders.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )
            else:
                st.error("لا توجد بيانات جاهزة للتحميل.")
