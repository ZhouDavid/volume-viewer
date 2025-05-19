from flask import Flask, render_template, request
from dbx_volume_helper import list_catalogs, list_schemas, list_volumes, list_files_in_volume, get_file_content
import base64

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    def_catalog = "jianyu_catalog"
    def_schema = "default"
    root_path = "/"

    selected_catalog = request.form.get('catalog', def_catalog)
    selected_schema = request.form.get('schema', def_schema)
    selected_volume = request.form.get('volume')
    selected_file = request.form.get('file')
    current_path = request.form.get('current_path', root_path)

    # Handle folder navigation
    go_up = request.form.get('go_up')
    if go_up == "1":
        # Go up one level
        if current_path != root_path:
            current_path = '/'.join(current_path.rstrip('/').split('/')[:-1]) or root_path

    # If a folder is clicked, update the path
    clicked_folder = request.form.get('clicked_folder')
    if clicked_folder:
        current_path = clicked_folder

    # Populate dropdowns
    catalogs = list_catalogs()
    schemas = list_schemas(selected_catalog) if selected_catalog else []
    volumes = list_volumes(selected_catalog, selected_schema) if selected_catalog and selected_schema else []
    volume_names = [v['name'] for v in volumes]

    # Auto-select the first available volume if none is selected
    if not selected_volume and volume_names:
        selected_volume = volume_names[0]

    # List files in the current path
    file_cards = []
    if selected_catalog and selected_schema and selected_volume:
        file_cards = list_files_in_volume(selected_catalog, selected_schema, selected_volume, current_path)

    # File preview
    file_content = None
    file_type = None
    if selected_file:
        content = get_file_content(selected_file)
        if content:
            if selected_file.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
                file_type = "image"
                file_content = content
            elif selected_file.lower().endswith((".txt", ".csv", ".json", ".xml", ".html")):
                file_type = "text"
                file_content = content.decode("utf-8", errors="replace")
            elif selected_file.lower().endswith(".pdf"):
                file_type = "pdf"
            else:
                file_type = "unsupported"
        else:
            file_type = "error"

    return render_template(
        'index.html',
        catalogs=catalogs,
        selected_catalog=selected_catalog,
        schemas=schemas,
        selected_schema=selected_schema,
        volume_names=volume_names,
        selected_volume=selected_volume,
        file_cards=file_cards,
        selected_file=selected_file,
        file_type=file_type,
        file_content=file_content,
        current_path=current_path,
        root_path=root_path
    )

@app.template_filter('b64encode')
def b64encode_filter(data):
    if data is None:
        return ''
    return base64.b64encode(data).decode('utf-8')

if __name__ == '__main__':
    app.run(debug=True)
