"""
Backend helper functions for Databricks Unity Catalog volume operations using the Databricks Python SDK.
"""

from databricks.sdk import WorkspaceClient
from typing import List, Dict, Optional
from PIL import Image
import io
import base64
import time
from simple_cache import TTLCache

# Initialize the Databricks SDK client (assumes environment variables or config file for auth)

dbx = WorkspaceClient()
# In-memory caches
_catalogs_cache = TTLCache(ttl_seconds=60)
_schemas_cache = TTLCache(ttl_seconds=60)
_volumes_cache = TTLCache(ttl_seconds=60)
_image_thumbnail_cache = TTLCache(ttl_seconds=300)
_file_content_cache = TTLCache(ttl_seconds=300)

def list_volumes(catalog_name: str, schema_name: str, limit: int = 20) -> List[Dict]:
    """
    List up to `limit` Unity Catalog volumes in the given catalog and schema.
    Returns a list of volume metadata dicts.
    """
    key = (catalog_name, schema_name)
    cached = _volumes_cache.get(key)
    if cached is not None:
        return cached
    volumes = []
    try:
        for v in dbx.volumes.list(catalog_name=catalog_name, schema_name=schema_name):
            volumes.append({
                'name': v.name,
                'catalog_name': v.catalog_name,
                'schema_name': v.schema_name,
                'comment': getattr(v, 'comment', None),
                'storage_location': getattr(v, 'storage_location', None),
                'volume_type': getattr(v, 'volume_type', None),
            })
            if len(volumes) >= limit:
                break
        _volumes_cache.set(key, volumes)
    except Exception as e:
        print(f"Error listing volumes for {catalog_name}.{schema_name}: {e}")
    return volumes

def list_files_in_volume(catalog_name: str, schema_name: str, volume_name: str, path: str = "/") -> List[Dict]:
    """
    List files and folders in a given volume and path.
    Args:
        catalog_name: The catalog name (e.g., 'main')
        schema_name: The schema name (e.g., 'default')
        volume_name: The volume name (e.g., 'my-volume')
        path: The path within the volume (default is root '/')
    Returns a list of file/folder metadata dicts.
    """
    files = []
    volume_path = f"/Volumes/{catalog_name}/{schema_name}/{volume_name}{path}" if path.startswith("/") else f"/Volumes/{catalog_name}/{schema_name}/{volume_name}/{path}"
    try:
        for item in dbx.files.list_directory_contents(volume_path):
            is_dir = getattr(item, 'is_directory', False)
            # Try to get modification time from several possible attribute names
            mtime = getattr(item, 'modification_time', None)
            if mtime is None:
                mtime = getattr(item, 'last_modified', None)
            if mtime is None:
                mtime = getattr(item, 'mtime', None)
            files.append({
                'path': item.path,
                'is_dir': is_dir,
                'file_size': getattr(item, 'file_size', None),
                'modification_time': mtime,
            })
    except Exception as e:
        print(f"Error listing files in {volume_path}: {e}")
    return files

def upload_file_to_volume(volume_full_name: str, dest_path: str, file_bytes: bytes) -> bool:
    """
    Upload a file to a given volume and path.
    Args:
        volume_full_name: The full name of the volume (e.g., 'catalog.schema.volume')
        dest_path: The destination path within the volume (e.g., '/myfolder/myfile.txt')
        file_bytes: The file content as bytes
    Returns True if upload succeeded, False otherwise.
    """
    try:
        # dest_path should be the full path, e.g., /Volumes/catalog/schema/volume/...
        if not dest_path.startswith("/Volumes/"):
            # Parse volume_full_name
            catalog, schema, volume = volume_full_name.split(".")
            dest_path = f"/Volumes/{catalog}/{schema}/{volume}{dest_path if dest_path.startswith('/') else '/' + dest_path}"
        print(f"[UPLOAD] Final dest_path: {dest_path}")
        dbx.files.upload(dest_path, file_bytes, overwrite=True)
        print(f"[UPLOAD] Upload to {dest_path} succeeded.")
        return True
    except Exception as e:
        print(f"[UPLOAD] Error uploading file to {dest_path}: {e}")
        return False

def get_file_content_cached(file_path: str) -> bytes | None:
    cached = _file_content_cache.get(file_path)
    if cached is not None:
        return cached
    try:
        resp = dbx.files.download(file_path)
        content = resp.contents.read()
        _file_content_cache.set(file_path, content)
        return content
    except Exception as e:
        print(f"Error downloading file {file_path}: {e}")
        return None

def list_catalogs() -> list[str]:
    """
    List all available Unity Catalog catalogs.
    Returns a list of catalog names.
    """
    cached = _catalogs_cache.get('catalogs')
    if cached is not None:
        return cached
    try:
        catalogs = [c.name for c in dbx.catalogs.list()]
        _catalogs_cache.set('catalogs', catalogs)
        return catalogs
    except Exception as e:
        print(f"Error listing catalogs: {e}")
        return []

def list_schemas(catalog_name: str) -> list[str]:
    """
    List all schemas in a given catalog.
    Returns a list of schema names.
    """
    cached = _schemas_cache.get(catalog_name)
    if cached is not None:
        return cached
    try:
        schemas = [s.name for s in dbx.schemas.list(catalog_name=catalog_name)]
        _schemas_cache.set(catalog_name, schemas)
        return schemas
    except Exception as e:
        print(f"Error listing schemas for catalog {catalog_name}: {e}")
        return []

def get_image_thumbnail(file_bytes: bytes, size=(48, 48), cache_key: str = None) -> str:
    """
    Generate a base64-encoded PNG thumbnail for the given image bytes, with optional caching by file path.
    """
    if cache_key:
        cached = _image_thumbnail_cache.get(cache_key)
        if cached is not None:
            return cached
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img.thumbnail(size)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            b64_thumb = base64.b64encode(buf.getvalue()).decode('utf-8')
            if cache_key:
                _image_thumbnail_cache.set(cache_key, b64_thumb)
            return b64_thumb
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return ''

def delete_file_from_volume(file_path: str, is_directory: bool = False) -> bool:
    """
    Delete a file or directory from a volume.
    Args:
        file_path: The full path of the file/directory to delete (e.g., '/Volumes/catalog/schema/volume/path/to/file.txt')
        is_directory: Whether the path is a directory
    Returns True if deletion succeeded, False otherwise.
    """
    try:
        print(f"[DELETE] Deleting {'directory' if is_directory else 'file'}: {file_path}")
        
        if is_directory:
            # For directories, we need to delete contents first
            try:
                # List all contents of the directory
                contents = dbx.files.list_directory_contents(file_path)
                for item in contents:
                    item_path = item.path
                    if getattr(item, 'is_directory', False):
                        # Recursively delete subdirectories
                        delete_file_from_volume(item_path, True)
                    else:
                        # Delete files
                        delete_file_from_volume(item_path, False)
                
                # Now delete the empty directory
                dbx.files.delete_directory(file_path)
                print(f"[DELETE] Successfully deleted directory: {file_path}")
            except Exception as e:
                print(f"[DELETE] Error deleting directory {file_path}: {e}")
                return False
        else:
            # For files, just delete directly
            dbx.files.delete(file_path)
            print(f"[DELETE] Successfully deleted file: {file_path}")
        
        # Clear caches for this file/directory
        _file_content_cache.set(file_path, None)
        _image_thumbnail_cache.set(file_path, None)
        
        return True
    except Exception as e:
        print(f"[DELETE] Error deleting {'directory' if is_directory else 'file'} {file_path}: {e}")
        return False

def create_folder_in_volume(catalog_name: str, schema_name: str, volume_name: str, folder_path: str) -> bool:
    """
    Create a new folder in a volume.
    Args:
        catalog_name: The catalog name (e.g., 'main')
        schema_name: The schema name (e.g., 'default')
        volume_name: The volume name (e.g., 'my-volume')
        folder_path: The path where to create the folder (e.g., '/myfolder/newfolder')
    Returns True if folder creation succeeded, False otherwise.
    """
    try:
        # Construct the full path
        full_path = f"/Volumes/{catalog_name}/{schema_name}/{volume_name}{folder_path if folder_path.startswith('/') else '/' + folder_path}"
        print(f"[CREATE FOLDER] Creating folder: {full_path}")
        
        # Create the directory using the dedicated method
        dbx.files.create_directory(full_path)
        print(f"[CREATE FOLDER] Successfully created folder: {full_path}")
        return True
    except Exception as e:
        print(f"[CREATE FOLDER] Error creating folder {full_path}: {e}")
        return False

if __name__ == "__main__":
    # Test listing files in a volume
    catalog = "main"
    schema = "default" 
    volume = "__databricks_ingestion_gateway_staging_data-9a9c881e-af42-46d1-8479-32bddd73c6c5"
    volume_path = "/"
    print(f"\nListing files in volume {catalog}.{schema}.{volume}:")
    files = list_files_in_volume(catalog, schema, volume, volume_path)
    for file in files:
        print(f"{'[DIR]' if file['is_dir'] else '[FILE]'} {file['path']}")


