# this is for testing purposes, SDK authencitation is preferred 
## mimi.qunell@databricks.com has SDK option

import requests
import streamlit as st
from PIL import Image, ExifTags
import base64
import io
import json
from streamlit_pdf_viewer import pdf_viewer

# Set the Databricks API host and personal access token
host = ''
token = ''

# Set the volume path
volume_path = '/Volumes/mikekahn-demo/mikekahn/files/'

# Set the API endpoint to list directory contents
list_endpoint = f'{host}api/2.0/fs/directories{volume_path}'

# Set file type categories
image_types = ['png', 'jpg', 'jpeg', 'gif', 'bmp']
text_types = ['txt', 'text', 'csv', 'json', 'xml']
html_types = ['html', 'htm']
pdf_types = ['pdf']
supported_types = image_types + text_types + html_types + pdf_types

# Set headers for API requests
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Configure Streamlit layout
st.set_page_config(layout="wide")


# Function to download a file from the Databricks volume
def download_file(file_path):
    """
    Downloads a file from the Databricks volume using its file path.

    :param file_path: The path to the file in the Databricks volume
    :return: The content of the downloaded file as bytes, or None if an error occurs
    """
    if file_path.startswith('/'):
        file_path = file_path[1:]  # Remove leading slash if present

    # Define the download API endpoint
    download_endpoint = f'{host}api/2.0/fs/files/{file_path}'

    # Send GET request to download the file
    response = requests.get(download_endpoint, headers=headers, stream=True)

    # Return file content if the request is successful
    if response.status_code == 200:
        return response.content
    else:
        return None


# Function to upload a file to the Databricks volume
def upload_file(file_path, file_data):
    """
    Uploads a file to the Databricks volume.

    :param file_path: Path in the Databricks volume where the file will be uploaded
    :param file_data: File data in bytes
    """
    upload_endpoint = f'{host}api/2.0/fs/files/{file_path}'

    response = requests.put(upload_endpoint, headers=headers, data=file_data)
    return response.status_code == 200


# Function to determine the file type based on its extension
def get_file_type(file_name):
    """
    Identifies the file type based on its extension.

    :param file_name: Name of the file
    :return: A string representing the file type ('image', 'text', 'html', 'pdf', 'unknown')
    """
    file_extension = file_name.split('.')[-1].lower()
    if file_extension in image_types:
        return 'image'
    elif file_extension in text_types:
        return 'text'
    elif file_extension in html_types:
        return 'html'
    elif file_extension in pdf_types:
        return 'pdf'
    else:
        return 'unknown'


# Function to correct image orientation using EXIF metadata
def correct_image_orientation(image):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = image._getexif()
        if exif is not None:
            orientation = exif.get(orientation)
            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)
    except Exception:
        pass
    return image


# Main application function
def main():
    # Define two-column layout
    col1, col2 = st.columns([0.3, 0.7])

    # Initialize session state for file listing
    if "file_list" not in st.session_state:
        st.session_state.file_list = []

    # Function to refresh file list
    def refresh_file_list():
        response = requests.get(list_endpoint, headers=headers)
        if response.status_code == 200:
            st.session_state.file_list = [
                file['path'] for file in response.json().get('contents', [])
            ]
        else:
            st.error(f"Error fetching file list: {response.status_code} - {response.text}")

    # File Selector Section
    with col1:
        st.title("Databricks Volumes Helper")
        st.markdown("This app allows you to view and download files from a Databricks volume")
        st.subheader("File Selector")

        # Refresh file list on first load or on manual refresh
        if not st.session_state.file_list:
            refresh_file_list()

        # Display the file list
        selected_file = st.radio("Select a file to display:", [""] + st.session_state.file_list, key="file_selector")

        # File upload section
        st.markdown("---")  # Divider
        uploaded_file = st.file_uploader("Upload local file:")
        if uploaded_file:
            file_path = volume_path + uploaded_file.name
            if upload_file(file_path, uploaded_file.read()):
                st.success(f"File '{uploaded_file.name}' uploaded successfully!")
                refresh_file_list()  # Refresh file list after successful upload
            else:
                st.error(f"Failed to upload file '{uploaded_file.name}'.")

        # Refresh button
        if st.button("Refresh File Listing", key="refresh"):
            refresh_file_list()

    # File Viewer Section
    with col2:
        st.header("")
        st.markdown("")
        st.markdown("")
        st.subheader("File Viewer")
        st.caption("Files supported: .png, .jpg, .jpeg, .gif, .bmp, .txt, .csv, .json, .xml, .pdf, .html")

        # Handle the selected file
        if selected_file:
            if selected_file == "":
                st.write("No file selected.")
            elif selected_file.endswith('/'):
                st.error("Sub-directory browsing is not available.")
            else:
                file_name = selected_file.split('/')[-1]  # Extract the file name
                file_bytes = download_file(selected_file)

                if file_bytes:
                    file_type = get_file_type(file_name)

                    # Display the file preview based on its type
                    if file_type == 'image':
                        image = Image.open(io.BytesIO(file_bytes))
                        corrected_image = correct_image_orientation(image)
                        st.image(corrected_image, caption=file_name, use_column_width=True)
                    elif file_type == 'text':
                        st.text_area(label="File Content", value=file_bytes.decode('utf-8'), height=300)
                    elif file_type == 'html':
                        render_as = st.radio("Render as:", ["html", "raw text"], key="html_render")
                        if render_as == "html":
                            st.components.v1.html(file_bytes.decode('utf-8'), height=600, scrolling=True)
                        else:
                            st.text_area(label="Raw HTML Content", value=file_bytes.decode('utf-8'), height=300)
                    elif file_type == 'pdf':
                        pdf_viewer(file_bytes, height=600)
                    else:
                        st.error("Unsupported file type.")

                    # Download button
                    st.download_button(
                        label=f"Download {file_name}",
                        data=file_bytes,
                        file_name=file_name,
                        mime='application/octet-stream'
                    )


if __name__ == '__main__':
    main()


#to fix - not currently able to display current textType's (['txt','text','csv','json','xml']), need to fix and other files
#to fix - move download and cancel buttons to top of col2 - change cancel to [x] button like a window and fix the cancel/refresh code
#todo - update format of file listing to use st.radio style for streamlit in sidebar col1 
#todo - add refresh file listing for newly uploaded files to volume
#todo - add select local file to upload files to volume using st.file_uploader and streamlit.components.v1 
#todo - clean up code into sections and fix indentations
