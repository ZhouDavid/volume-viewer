from typing import List, Dict
# from databricks.sdk import WorkspaceClient  # Uncomment and configure for real use

# dbx = WorkspaceClient()  # Uncomment and configure for real use

def list_catalogs() -> List[str]:
    """
    List all available Unity Catalog catalogs.
    Returns a list of catalog names.
    """
    # Example stub, replace with real SDK call
    # return [c.name for c in dbx.catalogs.list()]
    return ["jianyu_catalog", "main"]

def list_schemas(catalog_name: str) -> List[str]:
    """
    List all schemas in a given catalog.
    Returns a list of schema names.
    """
    # Example stub, replace with real SDK call
    # return [s.name for s in dbx.schemas.list(catalog_name=catalog_name)]
    return ["default", "test_schema"]

def list_volumes(catalog_name: str, schema_name: str, limit: int = 20) -> List[Dict]:
    """
    List up to `limit` Unity Catalog volumes in the given catalog and schema.
    Returns a list of volume metadata dicts.
    """
    # Example stub, replace with real SDK call
    # return [{"name": v.name, ...} for v in dbx.volumes.list(catalog_name=catalog_name, schema_name=schema_name)]
    return [
        {"name": "jianyu-vol1", "catalog_name": catalog_name, "schema_name": schema_name},
        {"name": "jianyu-vol2", "catalog_name": catalog_name, "schema_name": schema_name},
    ]

def list_files_in_volume(catalog_name: str, schema_name: str, volume_name: str, path: str = "/") -> List[Dict]:
    """
    List files and folders in a given volume and path.
    Returns a list of file/folder metadata dicts.
    """
    # Example stub, replace with real SDK call
    # volume_path = f"/Volumes/{catalog_name}/{schema_name}/{volume_name}{path}"
    # return [{...} for item in dbx.files.list_directory_contents(volume_path)]
    return [
        {"path": f"/Volumes/{catalog_name}/{schema_name}/{volume_name}/file1.txt", "is_dir": False, "file_size": 123, "modification_time": "2024-07-01"},
        {"path": f"/Volumes/{catalog_name}/{schema_name}/{volume_name}/folder1", "is_dir": True, "file_size": None, "modification_time": "2024-07-01"},
    ]

def get_file_content(file_path: str) -> bytes | None:
    """
    Download and return the content of a file given its full absolute path (e.g., '/Volumes/catalog/schema/volume/file.txt').
    Returns the file content as bytes, or None if download fails.
    """
    # Example stub, replace with real SDK call
    # resp = dbx.files.download(file_path)
    # return resp.contents.read()
    if file_path.endswith(".txt"):
        return b"This is a sample file content."
    return None 