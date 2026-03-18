import streamlit as st
import pandas as pd
import io

# ==========================================
# 1. قاعدة بيانات المشتركين (تعدل من هنا)
# ==========================================
CLIENTS = {
    "admin": {
        "pw": "admin123", "name": "إدارة المنصة", "role": "super_admin",
        "logo": "https://cdn-icons-png.flaticon.com/512/906/906343.png",
        "color": "#000000", "prefix": "ADM-"
    },
    "shop_759": {
        "pw": "759", "name": "نيرمن للتسوق", "role": "user",
        "logo": "https://cdn-icons-png.flaticon.com/512/3081/3081559.png", 
        "color": "#FF4B4B", "prefix": "NR-", "active": True
    }
}

# ==========================================
# 2. إعدادات المظهر (CSS) ليعطي شكل الصور
# ==========================================
def apply_custom_style(color):
    st.markdown(f"""
        <style>
        .stApp {{ background-color: #f4f7f6; }}
        [data-testid="stSidebar"] {{ background-color: white; border-right: 2px solid {color}; }}
        .stat-card {{
            background-color: white; padding: 15px; border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;
            border-top: 4px solid {color};
        }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 30px; }}
        .stButton>button {{ border-radius: 20px !important; }}
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. منطق معالجة ودمج البيانات (القلب النابض)
# ==========================================
def process_excel_logic(files, prod_name, prod_price, prefix):
    all_dfs = []
    for f in files:
        try:
            df = pd.read_excel(f)
            all_dfs.append(df)
        except: continue
    
    if not all_dfs: return None
    
    raw_df = pd.concat(all_dfs, ignore_index=True)
    
    # تحضير الأعمدة الموحدة
    final_cols = ['رقم الوصل', 'اسم الزبون', 'هاتف الزبون', 'هاتف الزبون 2', 
                  'المحافظة', 'المنطقة', 'المبلغ الكلي', 'نوع البضاعة', 'العدد', 'الملاحظات']
    
    clean_df = pd.DataFrame(columns=final_cols)
    
    # رسم البيانات (Mapping)
    clean_df['اسم الزبون'] = raw_df['الاسم'].str.strip() if 'الاسم' in raw_df.columns else ""
    clean_df['هاتف الزبون'] = raw_df['رقم الهاتف'].astype(str).str.strip() if 'رقم الهاتف' in raw_df.columns else ""
    clean_df['المحافظة'] = raw_df['المحافظه'] if 'المحافظه' in raw_df.columns else (raw_df['المحافظة'] if 'المحافظة' in raw_df.columns else "غير محدد")
    
    # دمج أعمدة المنطقة المختلفة
    for col in ['المنطقه واقرب نقطة داله', 'نقطه داله', 'المنطقه']:
        if col in raw_df.columns:
            clean_df['المنطقة'] = raw_df[col]
            break

    # تصفية الأسماء الوهمية (تست، تجربة، test)
    clean_df = clean_df[~clean_df['اسم الزبون'].str.contains('تست|تجربة|test|Test', na=False)]
    
    # حذف التكرارات (الاسم + الهاتف)
    duplicates_count = len(clean_df)
    clean_df.drop_duplicates(subset=['اسم الزبون', 'هاتف الزبون'], keep='first', inplace=True)
    duplicates_count -= len(clean_df)
    
    # إكمال البيانات المتبقية
    clean_df['نوع البضاعة'] = prod_name
    clean_df['المبلغ الكلي'] = prod_price
    clean_df['العدد'] = raw_df['العدد'] if 'العدد' in raw_df.columns else 1
    clean_df['هاتف الزبون 2'] = ""
    clean_df['الملاحظات'] = ""
    
    # توليد رقم الوصل بالرمز الخاص
    clean_df.reset_index(drop=True, inplace=True)
    clean_df['رقم الوصل'] = [f"{prefix}{i+1001}" for i in clean_df.index]
    
    return clean_df, duplicates_count

# ==========================================
# 4. واجهة المستخدم (UI)
# ==========================================
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.set_page_config(page_title="تسجيل دخول المنصة", layout="centered")
    st.image("https://cdn-icons-png.flaticon.com/512/2897/2897832.png", width=100)
    st.title("📦 تسجيل الدخول للمنصة")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول", use_container_width=True, type="primary"):
        if u in CLIENTS and CLIENTS[u]['pw'] == p:
            st.session_state.auth = True
            st.session_state.user_id = u
            st.rerun()
        else: st.error("خطأ في البيانات")

else:
    user = CLIENTS[st.session_state.user_id]
    apply_custom_style(user['color'])

    # القائمة الجانبية
    with st.sidebar:
        st.image(user['logo'], width=100)
        st.header(user['name'])
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state.auth = False
            st.rerun()
        st.divider()
        if user.get('role') == 'super_admin':
            st.subheader("🛠️ لوحة الإدارة")
            st.write("إدارة المشتركين")

    # واجهة العميل (نيرمن للتسوق مثالاً)
    st.title(f"لوحة تحكم {user['name']}")
    
    # البطاقات العلوي
    total = len(st.session_state.merged_res) if 'merged_res' in st.session_state and st.session_state.merged_res is not None else 0
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"<div class='stat-card'><div style='color:#666'>إجمالي البيانات</div><div style='font-size:30px; font-weight:bold; color:{user['color']}'>{total}</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='stat-card'><div style='color:#666'>مكررات محذوفة</div><div style='font-size:30px; font-weight:bold; color:orange'>{st.session_state.get('dup_count', 0)}</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='stat-card'><div style='color:#666'>جاهز للتصدير</div><div style='font-size:30px; font-weight:bold; color:green'>{total}</div></div>", unsafe_allow_html=True)

    # التبويبات
    st.write("<br>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📥 رفع البيانات", "📋 عرض البيانات", "📦 التصدير"])

    with t1:
        st.subheader("Excel رفع ملف")
        with st.container():
            col_a, col_b = st.columns(2)
            with col_a: p_name = st.text_input("نوع البضاعة")
            with col_b: p_price = st.number_input("السعر", value=25000)
        
        uploaded_files = st.file_uploader("قم بسحب وإفلات ملفات الإكسل هنا", type=['xlsx'], accept_multiple_files=True)
        
        if st.button("🔄 بدء المعالجة", use_container_width=True, type="primary"):
            if uploaded_files:
                res, d_count = process_excel_logic(uploaded_files, p_name, p_price, user['prefix'])
                st.session_state.merged_res = res
                st.session_state.dup_count = d_count
                st.success("تمت المعالجة بنجاح")
            else: st.warning("يرجى رفع الملفات")

    with t2:
        if 'merged_res' in st.session_state and st.session_state.merged_res is not None:
            st.dataframe(st.session_state.merged_res, use_container_width=True)
            if st.button("🗑️ مسح كل البيانات المرفوعة"):
                st.session_state.merged_res = None
                st.rerun()
        else: st.info("لا توجد بيانات لعرضها")

    with t3:
        if 'merged_res' in st.session_state and st.session_state.merged_res is not None:
            st.subheader("تصدير ملف الإكسل النهائي")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                st.session_state.merged_res.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 تحميل الملف الموحد",
                data=output.getvalue(),
                file_name=f"orders_{user['name']}.xlsx",
                use_container_width=True
            )
        else: st.error("ارفع الملفات أولاً")
