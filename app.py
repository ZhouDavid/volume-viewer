import streamlit as st
from dbx_volume_helper import list_catalogs, list_schemas, list_volumes, list_files_in_volume, get_file_content
from streamlit_card import card

# --- Custom CSS for grid, cards, and preview panel ---
def inject_custom_css():
    st.markdown("""
    <style>
    .uc-header {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
    }
    .uc-header img {
        height: 32px;
        margin-right: 16px;
    }
    .uc-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0;
    }
    .uc-subtitle {
        color: #888;
        margin-bottom: 32px;
        font-size: 1.1rem;
    }
    .uc-preview-panel {
        background: #f7f7f8;
        border-radius: 12px;
        padding: 48px 32px;
        text-align: center;
        margin-top: 12px;
    }
    .uc-preview-title {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .uc-preview-caption {
        color: #888;
        font-size: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
def render_header():
    st.markdown(
        '''<div class="uc-header">
            <img src="https://databricks.com/wp-content/uploads/2019/12/db-nav-logo.png">
            <span class="uc-title">UC volume viewer</span>
        </div>
        <div class="uc-subtitle">This app allows you to view, upload, and download files from a Databricks volume</div>''',
        unsafe_allow_html=True,
    )

# --- Catalog, Schema, Volume Selectors ---
def render_selectors():
    c1, c2, c3 = st.columns(3)
    catalogs = list_catalogs()
    def_catalog = "jianyu_catalog"
    def_schema = "default"
    with c1:
        selected_catalog = st.selectbox("Catalog", catalogs, index=catalogs.index(def_catalog) if def_catalog in catalogs else 0) if catalogs else None
    schemas = list_schemas(selected_catalog) if selected_catalog else []
    with c2:
        selected_schema = st.selectbox("Schema", schemas, index=schemas.index(def_schema) if def_schema in schemas else 0) if schemas else None
    vols = list_volumes(selected_catalog, selected_schema) if selected_catalog and selected_schema else []
    volume_names = [v['name'] for v in vols]
    with c3:
        selected_volume = st.selectbox("Volume", volume_names) if volume_names else None
    return selected_catalog, selected_schema, selected_volume

# --- File List (Radio) ---
def render_file_list(selected_catalog, selected_schema, selected_volume):
    file_cards = []
    if selected_volume:
        file_cards = list_files_in_volume(selected_catalog, selected_schema, selected_volume, "/")
    if file_cards:
        file_options = [f["path"] for f in file_cards]
        selected_file = st.radio(
            label="Select a file to preview:",
            options=file_options,
            format_func=lambda x: x.split("/")[-1],
            key="file_radio"
        )
    else:
        selected_file = None
    return selected_file

# --- File Preview ---
def render_file_preview(file_path):
    st.markdown('<div style="font-size: 1.25rem; font-weight: 600; margin-bottom: 18px;">File preview</div>', unsafe_allow_html=True)
    if file_path:
        content = get_file_content(file_path)
        if content:
            if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
                st.image(content)
            elif file_path.lower().endswith((".txt", ".csv", ".json", ".xml", ".html")):
                st.text(content.decode("utf-8", errors="replace"))
            elif file_path.lower().endswith(".pdf"):
                st.markdown("PDF preview not implemented.")
            else:
                st.markdown("File type not supported for preview.")
        else:
            st.markdown("Failed to load file content.")
    else:
        st.markdown(
            '''<div class="uc-preview-panel">
                <div class="uc-preview-title">Select a file to preview</div>
                <div class="uc-preview-caption">Files supported: .png, .jpg, .jpeg, .gif, .bmp, .txt, .csv, .json, .xml, .pdf, .html</div>
            </div>''',
            unsafe_allow_html=True,
        )

# --- Main App ---
def main():
    st.set_page_config(layout="wide")
    inject_custom_css()
    render_header()
    selected_catalog, selected_schema, selected_volume = render_selectors()
    st.markdown('<hr style="margin: 32px 0 24px 0; border: none; border-top: 1px solid #eee;">', unsafe_allow_html=True)
    left_col, right_col = st.columns([1.25, 2])
    with left_col:
        selected_file = render_file_list(selected_catalog, selected_schema, selected_volume)
    with right_col:
        render_file_preview(selected_file)

if __name__ == "__main__":
    main()
