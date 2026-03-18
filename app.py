import streamlit as st
import pandas as pd
import io
from typing import Dict, List, Optional
import hashlib

# =============================================================================
# CONFIGURATION - CHANGE THESE CREDENTIALS
# =============================================================================
USERNAME = "admin"
PASSWORD = "12345"

# =============================================================================
# SECURITY FUNCTIONS
# =============================================================================
def hash_password(password: str) -> str:
    """Hash password for secure storage/comparison"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(username: str, password: str) -> bool:
    """Verify username and password"""
    return username == USERNAME and hash_password(password) == hash_password(PASSWORD)

# =============================================================================
# SESSION STATE MANAGEMENT
# =============================================================================
def initialize_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    if 'merged_df' not in st.session_state:
        st.session_state.merged_df = None

# =============================================================================
# LOGIN PAGE
# =============================================================================
def login_page():
    st.title("🔐 Excel Merger - Login")
    st.markdown("---")
    
    with st.form("login_form"):
        st.subheader("📝 Login Credentials")
        username = st.text_input("👤 Username", placeholder="Enter username")
        password = st.text_input("🔑 Password", type="password", placeholder="Enter password")
        submit_button = st.form_submit_button("🚀 Login", use_container_width=True)
        
        if submit_button:
            if check_credentials(username, password):
                st.session_state.authenticated = True
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials! Please try again.")
                st.session_state.authenticated = False

# =============================================================================
# MAIN APP PAGE
# =============================================================================
def main_app():
    st.title("🔗 Excel Merger Tool")
    st.markdown("---")
    
    # Sidebar with logout
    with st.sidebar:
        st.markdown("## 👋 Welcome!")
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.markdown("---")
        st.info("**Status:** ✅ Logged in")
    
    # File upload section
    st.header("📁 Upload Excel Files")
    uploaded_files = st.file_uploader(
        "Choose Excel files",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        help="Upload multiple Excel files to merge"
    )
    
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
        st.success(f"✅ Loaded {len(uploaded_files)} file(s)")
        
        if st.button("🔄 Process & Merge Files", use_container_width=True, type="primary"):
            try:
                merged_df = merge_excel_files(uploaded_files)
                st.session_state.merged_df = merged_df
                st.success("✅ Files merged successfully!")
                
                # Display preview
                st.header("📊 Preview")
                st.dataframe(merged_df.head(10), use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Error processing files: {str(e)}")
    
    # Download section
    if st.session_state.merged_df is not None:
        st.header("💾 Download Merged File")
        csv_buffer = io.BytesIO()
        st.session_state.merged_df.to_excel(csv_buffer, index=False, engine='openpyxl')
        csv_buffer.seek(0)
        
        st.download_button(
            label="⬇️ Download Merged Excel",
            data=csv_buffer.getvalue(),
            file_name="merged_receipts.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# =============================================================================
# EXCEL MERGING LOGIC
# =============================================================================
def merge_excel_files(files: List[io.BytesIO]) -> pd.DataFrame:
    """Merge multiple Excel files with column mapping"""
    
    all_dataframes = []
    
    for file in files:
        # Read all sheets and find the one with relevant columns
        try:
            xl_file = pd.ExcelFile(file)
            df = None
            
            # Try to find the best sheet
            for sheet_name in xl_file.sheet_names:
                temp_df = pd.read_excel(file, sheet_name=sheet_name)
                if any(col in temp_df.columns for col in ['الاسم', 'رقم الهاتف', 'المحافظه']):
                    df = temp_df
                    break
            
            if df is None:
                # Fallback to first sheet
                df = pd.read_excel(file, sheet_name=0)
            
            all_dataframes.append(df)
            
        except Exception as e:
            st.warning(f"Could not process file: {str(e)}")
            continue
    
    if not all_dataframes:
        raise ValueError("No valid Excel files found")
    
    # Concatenate all dataframes
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    
    # Column mapping
    column_mapping = {
        'الاسم': 'اسم الزبون',
        'رقم الهاتف': 'هاتف الزبون',
        'المحافظه': 'المحافظة'
    }
    
    # Map columns
    mapped_df = combined_df.rename(columns=column_mapping)
    
    # Handle المنطقة column - check multiple possible sources
    region_sources = ['المنطقه واقرب نقطة داله', 'نقطه داله', 'المنطقه']
    region_col = None
    
    for source_col in region_sources:
        if source_col in combined_df.columns:
            mapped_df['المنطقة'] = combined_df[source_col]
            region_col = source_col
            break
    
    if region_col is None:
        mapped_df['المنطقة'] = ''  # Empty if no region column found
    
    # Create final dataframe with exact required columns
    required_columns = [
        'رقم الوصل', 'اسم الزبون', 'هاتف الزبون', 'هاتف الزبون 2', 
        'المحافظة', 'المنطقة', 'المبلغ الكلي', 'نوع البضاعة', 
        'العدد', 'الملاحظات'
    ]
    
    final_df = pd.DataFrame(columns=required_columns)
    
    # Add available data
    for col in required_columns:
        if col in mapped_df.columns:
            final_df[col] = mapped_df[col]
        elif col == 'العدد':
            final_df[col] = 1  # Default value
        else:
            final_df[col] = ''  # Empty for missing columns
    
    # Ensure proper column order
    final_df = final_df[required_columns]
    
    return final_df

# =============================================================================
# MAIN APPLICATION FLOW
# =============================================================================
def main():
    st.set_page_config(
        page_title="Excel Merger Tool",
        page_icon="🔗",
        layout="wide"
    )
    
    # Custom CSS for professional look
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    </style>
    """, unsafe_allow_html=True)
    
    initialize_session_state()
    
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
