import streamlit as st
import pandas as pd
import io

# ==========================================
# 1. إعدادات الإدارة والاشتراك
# ==========================================
ADMIN_USER = "admin"
ADMIN_PW = "admin123"
CLIENT_USER = "shop_759"
CLIENT_PW = "759"
IS_ACCOUNT_ACTIVE = True 

st.set_page_config(page_title="منصة نيرمن للتسوق", layout="wide")

# تنسيق CSS للأزرار وخانة البحث
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .stDataFrame { background-color: white; border-radius: 10px; }
    div[data-testid="stExpander"] { background-color: white; border-radius: 10px; }
    .search-label { font-size: 18px; font-weight: bold; color: #1f77b4; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. منطق المعالجة (بدون حذف مكرر)
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
    res['اسم الزبون'] = combined['الاسم'].fillna("") if 'الاسم' in combined.columns else ""
    res['هاتف الزبون'] = combined['رقم الهاتف'].fillna("") if 'رقم الهاتف' in combined.columns else ""
    res['المحافظة'] = combined['المحافظه'].fillna("") if 'المحافظه' in combined.columns else (combined['المحافظة'].fillna("") if 'المحافظة' in combined.columns else "")
    
    for col in ['المنطقه واقرب نقطة داله', 'نقطه داله', 'المنطقه']:
        if col in combined.columns:
            res['المنطقة'] = combined[col].fillna("")
            break

    res['نوع البضاعة'] = prod_name
    res['المبلغ الكلي'] = prod_price
    res['العدد'] = combined['العدد'].fillna(1) if 'العدد' in combined.columns else 1
    res = res.fillna("") # تنظيف أي None موجود
    
    res.reset_index(drop=True, inplace=True)
    res['رقم الوصل'] = res.index + 1
    return res

# ==========================================
# 3. واجهة المستخدم
# ==========================================
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 تسجيل الدخول للمنصة")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول", use_container_width=True, type="primary"):
        if (u == CLIENT_USER and p == CLIENT_PW) or (u == ADMIN_USER and p == ADMIN_PW):
            st.session_state.auth = True
            st.session_state.user = u
            st.rerun()
        else: st.error("خطأ في البيانات")

else:
    if st.session_state.user == CLIENT_USER and not IS_ACCOUNT_ACTIVE:
        st.error("🚫 الحساب معطل حالياً. يرجى التواصل مع الإدارة.")
    else:
        with st.sidebar:
            st.header("⚙️ القائمة")
            st.write(f"المستخدم: {st.session_state.user}")
            if st.button("تسجيل الخروج"):
                st.session_state.auth = False
                st.session_state.merged_res = None
                st.rerun()

        st.title(f"📊 لوحة تحكم {CLIENTS[CLIENT_USER]['name'] if st.session_state.user != ADMIN_USER else 'المدير'}")
        
        tab1, tab2, tab3 = st.tabs(["📤 رفع البيانات", "📋 عرض وبحث البيانات", "📦 التصدير والتحميل"])

        with tab1:
            st.subheader("Excel رفع ملف")
            c1, c2 = st.columns(2)
            p_name = c1.text_input("نوع البضاعة", value="عام")
            p_price = c2.number_input("السعر", value=25000)
            uploaded_files = st.file_uploader("ارفع الملفات هنا", type=['xlsx'], accept_multiple_files=True)
            if uploaded_files:
                st.session_state.merged_res = merge_logic(uploaded_files, p_name, p_price)
                st.success("✅ تم استلام الملفات بنجاح!")

        with tab2:
            if 'merged_res' in st.session_state and st.session_state.merged_res is not None:
                df = st.session_state.merged_res
                
                # --- خانة البحث الواضحة ---
                st.markdown("<p class='search-label'>🔍 ابحث عن اسم أو رقم هاتف:</p>", unsafe_allow_html=True)
                search_query = st.text_input("", placeholder="اكتب هنا للبحث...", label_visibility="collapsed")
                
                if search_query:
                    filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
                else:
                    filtered_df = df

                # --- خانة التحديد (Data Editor) ---
                st.subheader("📋 قائمة العملاء (يمكنك التعديل أو التحديد من هنا)")
                edited_df = st.data_editor(
                    filtered_df,
                    use_container_width=True,
                    num_rows="dynamic",
                    column_config={"رقم الوصل": st.column_config.NumberColumn(disabled=True)}
                )
                st.session_state.merged_res = edited_df # حفظ التعديلات
            else:
                st.info("البيانات ستظهر هنا بعد رفع الملفات.")

        with tab3:
            if 'merged_res' in st.session_state and st.session_state.merged_res is not None:
                st.subheader("📦 تحميل الملف الموحد بصيغة Excel")
                st.write("اضغط على الزر أدناه لتحميل الملف جاهزاً لشركة التوصيل:")
                
                # تحويل البيانات إلى Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    st.session_state.merged_res.to_excel(writer, index=False)
                
                # زر تنزيل واضح وكبير
                st.download_button(
                    label="📥 تحميل ملف الإكسل الموحد (xlsx)",
                    data=output.getvalue(),
                    file_name="final_orders.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )
                
                if st.button("🗑️ مسح كل البيانات الحالية"):
                    st.session_state.merged_res = None
                    st.rerun()
            else:
                st.error("لا توجد بيانات جاهزة للتحميل.")
