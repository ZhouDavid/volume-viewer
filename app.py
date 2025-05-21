from flask import Flask, render_template, request, send_file, redirect, url_for, flash, jsonify
from dbx_volume_helper import list_catalogs, list_schemas, list_volumes, list_files_in_volume, get_file_content_cached, get_image_thumbnail, upload_file_to_volume, delete_file_from_volume, create_folder_in_volume
import base64
import datetime
import io
from functools import lru_cache
import time

app = Flask(__name__)
app.secret_key = "replace-this-with-a-random-secret-key"

# Cache file listings for 5 seconds
@lru_cache(maxsize=100)
def get_cached_file_listing(catalog, schema, volume, path, timestamp):
    return list_files_in_volume(catalog, schema, volume, path)

# Cache thumbnails for 1 hour
@lru_cache(maxsize=1000)
def get_cached_thumbnail(content_hash, cache_key):
    return get_image_thumbnail(content_hash, cache_key)

@app.route('/', methods=['GET', 'POST'])
def index():
    root_path = "/"
    # Remove hardcoded defaults
    selected_catalog = request.args.get('catalog') or request.form.get('catalog')
    selected_schema = request.args.get('schema') or request.form.get('schema')
    selected_volume = request.args.get('volume') or request.form.get('volume')
    selected_file = request.args.get('file') or request.form.get('file')
    current_path = request.args.get('current_path') or request.form.get('current_path', root_path)

    # If the user changed the catalog, reset path and dependent selections
    if 'catalog' in request.form:
        prev_catalog = request.form.get('prev_catalog')
        if prev_catalog and prev_catalog != selected_catalog:
            current_path = root_path
            # Get schemas for new catalog
            schemas = list_schemas(selected_catalog)
            selected_schema = schemas[0] if schemas else None
            # Get volumes for new catalog and schema
            volumes = list_volumes(selected_catalog, selected_schema) if selected_schema else []
            volume_names = [v['name'] for v in volumes]
            selected_volume = volume_names[0] if volume_names else None
            selected_file = None

    # Handle folder navigation
    go_up = request.form.get('go_up')
    if go_up == "1":
        # Get the current path from the form, not from the URL
        current_path = request.form.get('current_path', root_path)
        print(f"[NAVIGATION DEBUG] Current path from form: {current_path}")
        
        # Go up one level
        if current_path != root_path:
            print(f"[NAVIGATION DEBUG] Current path before going up: {current_path}")
            # Remove trailing slash and split the path
            path_parts = current_path.rstrip('/').split('/')
            print(f"[NAVIGATION DEBUG] Path parts: {path_parts}")
            if len(path_parts) > 1:
                # Remove the last component to go up one level
                path_parts.pop()  # Remove the last component
                # Reconstruct the path, ensuring it starts with a slash and has a trailing slash
                current_path = '/' + '/'.join(filter(None, path_parts))
                if not current_path:
                    current_path = '/'
                elif current_path != '/':
                    current_path += '/'
                print(f"[NAVIGATION DEBUG] New path after going up: {current_path}")
            else:
                current_path = root_path
                print(f"[NAVIGATION DEBUG] Going to root: {current_path}")

    # If a folder is clicked, update the path
    clicked_folder = request.form.get('clicked_folder')
    if clicked_folder:
        # Ensure the path starts with a slash and has a trailing slash for directories
        current_path = '/' + clicked_folder.lstrip('/')
        if not current_path.endswith('/'):
            current_path += '/'
        print(f"[NAVIGATION] Clicked folder: {current_path}")

    # Populate dropdowns
    catalogs = list_catalogs()
    if not selected_catalog and catalogs:
        selected_catalog = catalogs[0]
    schemas = list_schemas(selected_catalog) if selected_catalog else []
    if not selected_schema and schemas:
        selected_schema = schemas[0]
    volumes = list_volumes(selected_catalog, selected_schema) if selected_catalog and selected_schema else []
    volume_names = [v['name'] for v in volumes]
    if not selected_volume and volume_names:
        selected_volume = volume_names[0]

    # List files in the current path with caching
    file_cards = []
    if selected_catalog and selected_schema and selected_volume:
        # Use cached file listing with a timestamp to invalidate cache every 5 seconds
        timestamp = int(time.time() / 5)
        file_cards = get_cached_file_listing(selected_catalog, selected_schema, selected_volume, current_path, timestamp)
        
        # Only generate thumbnails for visible images
        for f in file_cards:
            if not f.get('is_dir') and f['path'].lower().endswith(('.png', '.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                content = get_file_content_cached(f['path'])
                if content:
                    print(f"[THUMBNAIL DEBUG] type(content): {type(content)}, first 20 bytes: {content[:20]}")
                    if isinstance(content, str):
                        content = content.encode('utf-8')
                    f['preview'] = get_image_thumbnail(content, size=(48, 48), cache_key=f['path'])
                else:
                    f['preview'] = ''
            else:
                f['preview'] = ''

    # File preview
    file_content = None
    file_type = None
    if selected_file:
        content = get_file_content_cached(selected_file)
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

    # Handle file upload
    if request.method == 'POST':
        print(f"[UPLOAD DEBUG] request.files: {request.files}")
        print(f"[UPLOAD DEBUG] request.form: {request.form}")
        if 'upload_file' in request.files:
            upload_file = request.files['upload_file']
            upload_path = request.form.get('upload_path', '/')
            # Always get these from the form for upload POST
            selected_catalog = request.form.get('catalog') or selected_catalog
            selected_schema = request.form.get('schema') or selected_schema
            selected_volume = request.form.get('volume') or selected_volume
            if upload_file and selected_catalog and selected_schema and selected_volume:
                volume_full_name = f"{selected_catalog}.{selected_schema}.{selected_volume}"
                dest_path = upload_path.rstrip('/') + '/' + upload_file.filename
                file_bytes = upload_file.read()
                print(f"[UPLOAD] Uploading to: {volume_full_name}, dest_path: {dest_path}, bytes: {len(file_bytes)}")
                success = upload_file_to_volume(volume_full_name, dest_path, file_bytes)
                print(f"[UPLOAD] Upload success: {success}")
                if not success:
                    flash('Upload failed!', 'error')
                else:
                    flash('Upload succeeded!', 'success')
                return redirect(url_for('index', catalog=selected_catalog, schema=selected_schema, volume=selected_volume, current_path=upload_path))

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
        root_path=root_path,
        prev_volume=selected_volume,
        prev_catalog=selected_catalog
    )

@app.route('/download')
def download():
    file_path = request.args.get('file')
    if not file_path:
        return 'No file specified', 400
        
    # Check if it's a directory
    if file_path.endswith('/'):
        return 'Cannot download a directory', 400
        
    content = get_file_content_cached(file_path)
    if content is None:
        return 'File not found or failed to load', 404
    filename = file_path.rstrip('/').split('/')[-1]
    return send_file(io.BytesIO(content), as_attachment=True, download_name=filename)

@app.route('/api/file-preview')
def file_preview():
    file_path = request.args.get('file')
    if not file_path:
        return {'error': 'No file specified'}, 400
        
    content = get_file_content_cached(file_path)
    if content is None:
        return {'error': 'File not found or failed to load'}, 404
        
    filename = file_path.rstrip('/').split('/')[-1]
    modification_time = None
    
    # Get modification time from file_cards if available
    catalog = request.args.get('catalog')
    schema = request.args.get('schema')
    volume = request.args.get('volume')
    current_path = request.args.get('current_path', '/')
    
    if catalog and schema and volume:
        file_cards = list_files_in_volume(catalog, schema, volume, current_path)
        for f in file_cards:
            if f['path'] == file_path:
                modification_time = f.get('modification_time')
                break
    
    if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
        file_type = "image"
        file_content = base64.b64encode(content).decode('utf-8')
    elif file_path.lower().endswith((".txt", ".csv", ".json", ".xml", ".html")):
        file_type = "text"
        file_content = content.decode("utf-8", errors="replace")
    elif file_path.lower().endswith(".pdf"):
        file_type = "pdf"
        file_content = None
    else:
        file_type = "unsupported"
        file_content = None
    
    return {
        'filename': filename,
        'modification_time': format_datetime(modification_time) if modification_time else 'N/A',
        'file_type': file_type,
        'file_content': file_content
    }

@app.route('/delete', methods=['POST'])
def delete_file():
    file_path = request.form.get('file_path')
    is_directory = request.form.get('is_directory') == 'true'
    
    print(f"[DELETE] Received request - file_path: {file_path}, is_directory: {is_directory}")
    
    if not file_path:
        print("[DELETE] Error: No file path provided")
        return jsonify({'error': 'No file path provided'}), 400
    
    success = delete_file_from_volume(file_path, is_directory)
    if success:
        print(f"[DELETE] Successfully deleted {'directory' if is_directory else 'file'}: {file_path}")
        return jsonify({'message': f"{'Directory' if is_directory else 'File'} deleted successfully"})
    else:
        print(f"[DELETE] Failed to delete {'directory' if is_directory else 'file'}: {file_path}")
        return jsonify({'error': f"Failed to delete {'directory' if is_directory else 'file'}"}), 500

@app.route('/api/create-folder', methods=['POST'])
def create_folder():
    folder_name = request.form.get('folder_name')
    catalog = request.form.get('catalog')
    schema = request.form.get('schema')
    volume = request.form.get('volume')
    current_path = request.form.get('current_path', '/')
    
    if not all([folder_name, catalog, schema, volume]):
        return {'error': 'Missing required parameters'}, 400
        
    # Construct the folder path
    folder_path = f"{current_path.rstrip('/')}/{folder_name}"
    
    success = create_folder_in_volume(catalog, schema, volume, folder_path)
    if not success:
        return {'error': 'Failed to create folder'}, 500
        
    return {'success': True}

@app.template_filter('b64encode')
def b64encode_filter(data):
    if data is None:
        return ''
    return base64.b64encode(data).decode('utf-8')

@app.template_filter('format_datetime')
def format_datetime(value):
    if value is None or value == '':
        return ''
    try:
        # If it's a number (timestamp)
        if isinstance(value, (int, float)):
            ts = float(value)
            if ts > 1e12:  # likely milliseconds
                ts = ts / 1000.0
            return datetime.datetime.fromtimestamp(ts).strftime('%b %d, %Y')
        # If it's a string, try to parse as ISO or as a number
        if isinstance(value, str):
            # Try ISO format first
            try:
                return datetime.datetime.fromisoformat(value).strftime('%b %d, %Y')
            except Exception:
                pass
            # Try as a stringified Unix timestamp
            try:
                ts = float(value)
                if ts > 1e12:  # likely milliseconds
                    ts = ts / 1000.0
                return datetime.datetime.fromtimestamp(ts).strftime('%b %d, %Y')
            except Exception:
                pass
        return str(value)
    except Exception:
        return str(value)

if __name__ == '__main__':
    app.run(debug=True)
