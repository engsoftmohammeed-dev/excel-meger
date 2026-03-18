import streamlit as st
import pandas as pd
import io

# ==========================================
# 1. إعدادات الإدارة والعميل
# ==========================================
ADMIN_USER = "admin"
ADMIN_PW = "admin123"
CLIENT_USER = "shop_759"
CLIENT_PW = "759"
IS_ACCOUNT_ACTIVE = True 

st.set_page_config(page_title="نظام نيرمن - النسخة الذكية", page_icon="🚀", layout="wide")

# ==========================================
# 2. وظيفة البحث الذكي عن الأعمدة (Smart Column Finder)
# ==========================================
def find_smart_column(df, keywords):
    """يبحث عن العمود الذي يحتوي على كلمات دليلة معينة"""
    for col in df.columns:
        if any(key in str(col).lower() for key in keywords):
            return col
    return None

def merge_logic(files):
    all_dfs = []
    for f in files:
        try:
            df_raw = pd.read_excel(f)
            
            # --- 1. البحث الذكي عن الهاتف ---
            phone_keys = ['هاتف', 'موبايل', 'جوال', 'phone', 'mobile', 'tel']
            phone_col = find_smart_column(df_raw, phone_keys)
            
            # --- 2. البحث الذكي عن الاسم ---
            name_keys = ['الاسم', 'name', 'full name', 'الزبون']
            name_col = find_smart_column(df_raw, name_keys)
            
            # --- 3. البحث الذكي عن المحافظة ---
            prov_keys = ['محافظه', 'محافظة', 'province', 'city', 'المدينة']
            prov_col = find_smart_column(df_raw, prov_keys)
            
            # --- 4. البحث الذكي عن المنطقة ---
            area_keys = ['منطقه', 'منطقة', 'نقطه داله', 'داله', 'area', 'address', 'عنوان']
            area_col = find_smart_column(df_raw, area_keys)

            # --- 5. سحب نوع البضاعة (حسب موقع العمود D أو F كخيار أخير) ---
            prod_type = ""
            if df_raw.shape[1] >= 6:
                # يفضل العمود السادس (F) ثم الرابع (D)
                prod_type = df_raw.iloc[:, 5] if pd.notna(df_raw.iloc[0, 5]) else df_raw.iloc[:, 3]
            elif df_raw.shape[1] >= 4:
                prod_type = df_raw.iloc[:, 3]
            
            # بناء الجدول المؤقت
            temp_df = pd.DataFrame()
            temp_df['اسم الزبون'] = df_raw[name_col] if name_col else ""
            temp_df['هاتف الزبون'] = df_raw[phone_col] if phone_col else ""
            temp_df['هاتف الزبون 2'] = ""
            temp_df['المحافظة'] = df_raw[prov_col] if prov_col else ""
            temp_df['المنطقة'] = df_raw[area_col] if area_col else ""
            temp_df['نوع البضاعة'] = prod_type
            temp_df['المبلغ الكلي'] = 0
            temp_df['العدد'] = 1
            temp_df['الملاحظات'] = ""
            
            all_dfs.append(temp_df)
        except Exception as e:
            st.error(f"خطأ في معالجة ملف {f.name}: {e}")
            continue
    
    if not all_dfs: return None
    
    combined = pd.concat(all_dfs, ignore_index=True)
    combined.reset_index(drop=True, inplace=True)
    combined.insert(0, 'رقم الوصل', combined.index + 1)
    
    # تنظيف شامل لكل الجدول من الـ None والـ nan
    combined = combined.applymap(lambda x: "" if pd.isna(x) or str(x).lower() in ["none", "nan", "null"] else x)
    return combined

# ==========================================
# 3. واجهة المستخدم
# ==========================================
if 'auth' not in st.session_state: st.session_state.auth = False
if 'merged_res' not in st.session_state: st.session_state.merged_res = None

if not st.session_state.auth:
    st.title("🔐 تسجيل الدخول للمنصة")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول", use_container_width=True, type="primary"):
        if (u == CLIENT_USER and p == CLIENT_PW) or (u == ADMIN_USER and p == ADMIN_PW):
            st.session_state.auth = True
            st.session_state.user = u
            st.rerun()
        else: st.error("❌ بيانات الدخول خطأ")
else:
    if st.session_state.user == CLIENT_USER and not IS_ACCOUNT_ACTIVE:
        st.error("🚫 الحساب معطل. يرجى مراجعة الإدارة.")
    else:
        with st.sidebar:
            st.header("⚙️ نيرمن للتسوق")
            st.write(f"المستخدم: {st.session_state.user}")
            if st.button("🚪 تسجيل الخروج"):
                st.session_state.auth = False
                st.session_state.merged_res = None
                st.rerun()

        st.title("📦 نظام سحب البيانات الذكي")
        
        t1, t2, t3 = st.tabs(["📤 1. رفع ومعالجة", "🔍 2. بحث وتعديل", "📥 3. تحميل الإكسل"])

        with t1:
            st.subheader("ارفع ملفات الإعلانات")
            uploaded_files = st.file_uploader("يمكنك رفع عدة ملفات معا", type=['xlsx'], accept_multiple_files=True)
            if uploaded_files:
                if st.button("🚀 سحب البيانات الآن", type="primary", use_container_width=True):
                    with st.spinner('جاري البحث عن أرقام الهواتف والأسماء...'):
                        st.session_state.merged_res = merge_logic(uploaded_files)
                    st.balloons()
                    st.success("✅ تم سحب البيانات بنجاح! اذهب لتبويب 'بحث وتعديل' لرؤية النتائج.")

        with t2:
            if st.session_state.merged_res is not None:
                df = st.session_state.merged_res
                
                # إحصائيات سريعة
                c1, c2 = st.columns(2)
                c1.metric("عدد الطلبات", len(df))
                total_m = pd.to_numeric(df['المبلغ الكلي'], errors='coerce').sum()
                c2.metric("إجمالي المبالغ", f"{total_m:,} د.ع")
                
                st.divider()
                search = st.text_input("🔎 ابحث عن أي شيء (اسم، هاتف، محافظة...):")
                
                to_show = df
                if search:
                    to_show = to_show[to_show.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

                st.info("💡 يمكنك تعديل الأسعار أو مسح الأسماء مباشرة من الجدول.")
                edited_df = st.data_editor(to_show, use_container_width=True, num_rows="dynamic")
                
                # حفظ التعديلات
                if search:
                    st.session_state.merged_res.update(edited_df)
                else:
                    st.session_state.merged_res = edited_df
            else:
                st.info("البيانات ستظهر هنا بعد ضغط زر 'سحب البيانات' في التبويب الأول.")

        with t3:
            if st.session_state.merged_res is not None:
                st.subheader("📥 تنزيل الملف النهائي")
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    st.session_state.merged_res.to_excel(writer, index=False)
                st.download_button("📥 تحميل الإكسل الموحد (xlsx)", output.getvalue(), file_name="final_orders.xlsx", use_container_width=True, type="primary")
            else:
                st.error("لا توجد بيانات للتحميل.")
