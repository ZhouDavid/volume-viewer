import streamlit as st
from dbx_volume_helper import list_catalogs, list_schemas, list_volumes, list_files_in_volume, get_file_content
from streamlit_card import card

# --- Page setup ---
st.set_page_config(layout="wide")

# --- Custom CSS for grid, cards, and preview panel ---
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
.uc-volume-input {
    display: flex;
    align-items: center;
    background: #f7f7f8;
    border-radius: 6px;
    padding: 8px 12px;
    border: 1px solid #e0e0e0;
    margin-bottom: 32px;
}
.uc-volume-input input {
    border: none;
    background: transparent;
    outline: none;
    font-size: 1rem;
    width: 100%;
    margin-left: 8px;
}
.uc-file-toolbar {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-bottom: 16px;
}
.uc-file-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}
.uc-card {
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 18px 18px 12px 18px;
    display: flex;
    align-items: flex-start;
    gap: 14px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    cursor: pointer;
    transition: border 0.2s;
}
.uc-card:hover {
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}
.uc-card.selected {
    border: 2px solid #2966d2;
}
.uc-card-icon {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.uc-card-content {
    display: flex;
    flex-direction: column;
}
.uc-card-title {
    font-weight: 500;
    font-size: 1.08rem;
}
.uc-card-date {
    color: #888;
    font-size: 0.95rem;
    margin-top: 2px;
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
st.markdown(
    '''<div class="uc-header">
        <img src="https://databricks.com/wp-content/uploads/2019/12/db-nav-logo.png">
        <span class="uc-title">UC volume viewer</span>
    </div>
    <div class="uc-subtitle">This app allows you to view, upload, and download files from a Databricks volume</div>''',
    unsafe_allow_html=True,
)

# --- Catalog, Schema, Volume Selectors at the top in 3 columns ---
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

st.markdown('<hr style="margin: 32px 0 24px 0; border: none; border-top: 1px solid #eee;">', unsafe_allow_html=True)

# --- Main Layout ---
left_col, right_col = st.columns([1.25, 2])

with left_col:
    st.markdown('<div style="font-size: 1.25rem; font-weight: 600; margin-bottom: 18px;">Root</div>', unsafe_allow_html=True)
    st.markdown('<div class="uc-file-toolbar">'
                '<button title="Refresh" style="background: none; border: none; cursor: pointer; font-size: 1.3rem;">&#x21bb;</button>'
                '<button title="Upload" style="background: none; border: none; cursor: pointer; font-size: 1.3rem;">&#x2b06;</button>'
                '</div>', unsafe_allow_html=True)

    icons = {
        "folder": '<svg width="28" height="28" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="9" width="22" height="12" rx="2" fill="#E6F0FA"/><path d="M3 9V7.5A2.5 2.5 0 0 1 5.5 5h4.086a2.5 2.5 0 0 1 1.768.732l1.414 1.414A2.5 2.5 0 0 0 15.536 9H23a2 2 0 0 1 2 2v1" stroke="#2966d2" stroke-width="1.5"/></svg>',
        "image": '<svg width="28" height="28" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="5" width="22" height="18" rx="2" fill="#FFF7E6"/><circle cx="9" cy="11" r="2" fill="#F7B500"/><path d="M3 19l5-5a2 2 0 0 1 2.828 0l4.172 4.172a2 2 0 0 0 2.828 0L25 11" stroke="#F7B500" stroke-width="1.5"/></svg>',
        "pdf": '<svg width="28" height="28" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="5" width="22" height="18" rx="2" fill="#FDEEEF"/><rect x="7" y="9" width="14" height="10" rx="1" fill="#F76B8A"/><text x="14" y="18" text-anchor="middle" font-size="7" fill="#fff" font-family="Arial">PDF</text></svg>',
        "default": '<svg width="28" height="28" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="5" width="22" height="18" rx="2" fill="#F7F7F8"/><rect x="7" y="9" width="14" height="10" rx="1" fill="#B0B8C1"/></svg>',
    }

    file_cards = []
    if selected_volume:
        file_cards = list_files_in_volume(selected_catalog, selected_schema, selected_volume, "/")

    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None

    num_cols = 2
    cols = st.columns(num_cols)
    for idx, f in enumerate(file_cards):
        col = cols[idx % num_cols]
        with col:
            icon = icons["folder"] if f["is_dir"] else icons.get(f["path"].split(".")[-1], icons["default"])
            image_url = "https://img.icons8.com/ios-filled/50/000000/folder-invoices--v1.png" if f["is_dir"] else "https://img.icons8.com/ios-filled/50/000000/file.png"
            is_selected = st.session_state.selected_file == f["path"]
            selected_class = "selected" if is_selected else ""
            st.markdown(f'''
            <form method="post">
                <input type="hidden" name="selected_file" value="{f['path']}" />
                <button type="submit" style="all: unset; width: 100%;">
                    <div class="uc-card {selected_class}">
                        <div class="uc-card-icon"><img src="{image_url}" width="28"></div>
                        <div class="uc-card-content">
                            <div class="uc-card-title">{f['path'].split('/')[-1]}</div>
                            <div class="uc-card-date">Size: {f.get('file_size', '-')}, Dir: {f['is_dir']}</div>
                        </div>
                    </div>
                </button>
            </form>
            ''', unsafe_allow_html=True)
            st.session_state.selected_file = f["path"]
            container.markdown(f'''
            <div class="uc-card {selected_class}">
                <div class="uc-card-icon"><img src="{image_url}" width="28"></div>
                <div class="uc-card-content">
                    <div class="uc-card-title">{f['path'].split('/')[-1]}</div>
                    <div class="uc-card-date">Size: {f.get('file_size', '-')}, Dir: {f['is_dir']}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            # Handle click (removed)

with right_col:
    st.markdown('<div style="font-size: 1.25rem; font-weight: 600; margin-bottom: 18px;">File preview</div>', unsafe_allow_html=True)
    file_path = st.session_state.get('selected_file')
    if selected_volume and file_path:
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
