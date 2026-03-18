import streamlit as st
import pandas as pd
import io

# ==========================================
# 1. إعدادات المنصة وقاعدة بيانات العملاء
# ==========================================
st.set_page_config(page_title="إدارة بيانات العملاء", layout="wide")

CLIENTS = {
    "admin": {"pw": "admin123", "name": "إدارة المنصة", "role": "super_admin"},
    "shop_759": {"pw": "759", "name": "نيرمن للتسوق", "logo": "🛒", "prefix": "NR-", "active": True},
}

# تخصيص المظهر (CSS) ليشبه الصور
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .metric-card {
        background-color: white; padding: 20px; border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;
    }
    .stButton>button { border-radius: 20px; width: 100%; }
    .main-header { color: #2c3e50; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. نظام الدخول والتحكم
# ==========================================
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = ""

if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/2897/2897832.png", width=80)
        st.header("تسجيل الدخول للمنصة")
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if u in CLIENTS and CLIENTS[u]['pw'] == p:
                st.session_state.auth = True
                st.session_state.user = u
                st.rerun()
            else: st.error("خطأ في البيانات")
else:
    user_id = st.session_state.user
    user_data = CLIENTS[user_id]

    # ==========================================
    # 3. داشبورد "الآدمن" (لتحكمك الشخصي بالعملاء)
    # ==========================================
    if user_data.get('role') == 'super_admin':
        st.sidebar.title("🛠️ لوحة التحكم")
        choice = st.sidebar.radio("التوجه", ["إدارة العملاء", "الإحصائيات العامة"])
        
        if choice == "إدارة العملاء":
            st.title("👥 إدارة حسابات العملاء")
            for cid, data in CLIENTS.items():
                if cid != 'admin':
                    col_a, col_b, col_c = st.columns([2,1,1])
                    col_a.write(f"**{data['name']}** (ID: {cid})")
                    status = "نشط ✅" if data['active'] else "متوقف ❌"
                    col_b.write(f"الحالة: {status}")
                    if col_c.button(f"تعديل الحالة {cid}"):
                        CLIENTS[cid]['active'] = not CLIENTS[cid]['active']
                        st.rerun()

    # ==========================================
    # 4. داشبورد "العميل" (مثل نيرمن للتسوق)
    # ==========================================
    else:
        # السايد بار
        with st.sidebar:
            st.markdown(f"## {user_data['logo']} {user_data['name']}")
            st.write(f"إدارة بيانات العملاء من TikTok")
            st.divider()
            if st.button("🚪 تسجيل الخروج"):
                st.session_state.auth = False
                st.rerun()

        # الجزء العلوي (الإحصائيات)
        st.markdown(f"<h1 class='main-header'>{user_data['name']}</h1>", unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        with m1: st.markdown("<div class='metric-card'><h3>إجمالي البيانات</h3><h2>759</h2></div>", unsafe_allow_html=True)
        with m2: st.markdown("<div class='metric-card'><h3>عملاء مكررين</h3><h2>12</h2></div>", unsafe_allow_html=True)
        with m3: st.markdown("<div class='metric-card'><h3>جاهز للتصدير</h3><h2>747</h2></div>", unsafe_allow_html=True)

        # التبويبات (Tabs) مثل الصورة
        tab1, tab2, tab3 = st.tabs(["📤 رفع البيانات", "📋 عرض البيانات", "📦 التصدير"])

        with tab1:
            st.subheader("Excel رفع ملف")
            uploaded_file = st.file_uploader("اسحب وأفلت الملف هنا", type=['xlsx', 'xls'])
            if uploaded_file:
                st.success("تم رفع الملف بنجاح")

        with tab2:
            st.subheader("📋 قائمة بيانات العملاء")
            # بيانات تجريبية للعرض
            data = {
                "الاسم": ["اريد هورن", "وليد الحلبوسي", "حسن ناصر"],
                "المحافظة": ["حلة طهمازية", "بغداد", "ديالي"],
                "رقم الهاتف": ["07804056226", "07710302202", "07710476496"],
                "نوع المنتج": ["هورن بوش", "هورن بوش", "هورن بوش"],
                "نقطة دالة": ["طريق عوني", "الطارمية", "ديالي حويش"]
            }
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            
            c1, c2, c3 = st.columns(3)
            c1.button("طباعة الكل 🖨️")
            c2.button("حذف المحدد 🗑️")
            c3.button("تعديل السعر 💰")

        with tab3:
            st.subheader("📦 تصدير النتائج النهائية")
            st.info("سيتم تصدير البيانات وفق الفورمة الموحدة")
            st.button("تحميل الملف النهائي (Excel) 📥")
