import streamlit as st
import pandas as pd
import io

# ==========================================
# 1. إعدادات الدخول والاشتراك
# ==========================================
ADMIN_USER = "admin"
ADMIN_PW = "admin123"
CLIENT_USER = "shop_759"
CLIENT_PW = "759"
IS_ACCOUNT_ACTIVE = True 

st.set_page_config(page_title="نظام نيرمن المتطور", layout="wide")

# تخصيص الواجهة لتكون سلسة
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { border-radius: 10px 10px 0 0; padding: 10px 20px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. منطق دمج وسحب البيانات الذكي
# ==========================================
def merge_logic(files):
    all_dfs = []
    for f in files:
        try:
            # قراءة الملف بدون أسماء أعمدة أولاً لتحديد الحقول بمواقعها (D, F)
            df_raw = pd.read_excel(f)
            
            # محاولة سحب نوع البضاعة من العمود D (رقم 3) أو F (رقم 5)
            prod_type = ""
            if df_raw.shape[1] >= 6: # إذا كان الملف فيه 6 أعمدة أو أكثر
                prod_type = df_raw.iloc[:, 5] if pd.notna(df_raw.iloc[0, 5]) else df_raw.iloc[:, 3]
            elif df_raw.shape[1] >= 4:
                prod_type = df_raw.iloc[:, 3]
            
            # بناء الهيكل الموحد
            temp_df = pd.DataFrame()
            temp_df['الاسم_الخام'] = df_raw['الاسم'] if 'الاسم' in df_raw.columns else ""
            temp_df['الهاتف_الخام'] = df_raw['رقم الهاتف'] if 'رقم الهاتف' in df_raw.columns else ""
            temp_df['المحافظة_الخام'] = df_raw['المحافظه'] if 'المحافظه' in df_raw.columns else (df_raw['المحافظة'] if 'المحافظة' in df_raw.columns else "")
            
            # سحب المنطقة
            area = ""
            for col in ['المنطقه واقرب نقطة داله', 'نقطه داله', 'المنطقه']:
                if col in df_raw.columns:
                    area = df_raw[col]
                    break
            temp_df['المنطقة_الخام'] = area
            temp_df['نوع_البضاعة_الخام'] = prod_type
            
            all_dfs.append(temp_df)
        except Exception as e:
            st.error(f"خطأ في ملف {f.name}: {e}")
            continue
    
    if not all_dfs: return None
    
    combined = pd.concat(all_dfs, ignore_index=True)
    
    # بناء الجدول النهائي المرتب
    res = pd.DataFrame()
    res['رقم الوصل'] = range(1, len(combined) + 1)
    res['اسم الزبون'] = combined['الاسم_الخام'].fillna("")
    res['هاتف الزبون'] = combined['الهاتف_الخام'].fillna("")
    res['هاتف الزبون 2'] = ""
    res['المحافظة'] = combined['المحافظة_الخام'].fillna("")
    res['المنطقة'] = combined['المنطقة_الخام'].fillna("")
    res['نوع البضاعة'] = combined['نوع_البضاعة_الخام'].fillna("")
    res['المبلغ الكلي'] = 0 # السعر يبدأ بصفر كما طلبت
    res['العدد'] = 1
    res['الملاحظات'] = ""
    
    return res

# ==========================================
# 3. إدارة الجلسة (Session State)
# ==========================================
if 'auth' not in st.session_state: st.session_state.auth = False
if 'merged_res' not in st.session_state: st.session_state.merged_res = None

# ==========================================
# 4. واجهة المستخدم
# ==========================================
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
        st.error("🚫 الحساب معطل. يرجى التواصل مع الإدارة.")
        if st.button("خروج"):
            st.session_state.auth = False
            st.rerun()
    else:
        # شريط جانبي ثابت لا يخرجك من الموقع
        with st.sidebar:
            st.header("👤 حسابك")
            st.write(f"المستخدم: {st.session_state.user}")
            if st.button("🚪 تسجيل الخروج"):
                st.session_state.auth = False
                st.session_state.merged_res = None
                st.rerun()

        st.title("📦 سيستم معالجة الطلبات الموحد")
        
        # التبويبات - التنقل بينها سلس جداً
        tab1, tab2, tab3 = st.tabs(["📤 1. رفع الملفات", "📝 2. تسعير وبحث", "📥 3. تحميل الإكسل"])

        with tab1:
            st.subheader("ارفع ملفات TikTok الإعلانية")
            uploaded_files = st.file_uploader("يمكنك رفع عدة ملفات معاً", type=['xlsx'], accept_multiple_files=True)
            if uploaded_files:
                if st.button("🚀 دمج الملفات وسحب البيانات"):
                    st.session_state.merged_res = merge_logic(uploaded_files)
                    st.success("✅ تم الدمج وسحب نوع البضاعة من (D/F) بنجاح!")

        with tab2:
            if st.session_state.merged_res is not None:
                st.subheader("📝 جدول البيانات (اضغط على خانة السعر لتعديلها)")
                
                # خانة البحث
                search = st.text_input("🔍 بحث سريع (اسم أو هاتف)...")
                df_to_edit = st.session_state.merged_res
                
                if search:
                    df_to_edit = df_to_edit[df_to_edit.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

                # محرر البيانات التفاعلي (مثل الإكسل)
                edited_df = st.data_editor(
                    df_to_edit,
                    use_container_width=True,
                    num_rows="dynamic",
                    column_config={
                        "المبلغ الكلي": st.column_config.NumberColumn("السعر 💰", format="%d"),
                        "رقم الوصل": st.column_config.Column(disabled=True)
                    }
                )
                # حفظ التعديلات فوراً في الجلسة
                st.session_state.merged_res.update(edited_df)
                
                st.write(f"💡 مجموع الطلبات في هذا الجدول: {len(edited_df)}")
            else:
                st.info("ارفع الملفات أولاً لتتمكن من تسعيرها هنا.")

        with tab3:
            if st.session_state.merged_res is not None:
                st.subheader("📥 تحميل الملف النهائي")
                st.write("سيحتوي الملف على كافة تعديلات الأسعار التي قمت بها.")
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    st.session_state.merged_res.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 تحميل ملف الإكسل الموحد (xlsx)",
                    data=output.getvalue(),
                    file_name="cleaned_orders.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )
            else:
                st.error("لا توجد بيانات للتحميل.")
