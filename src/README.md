# volume-helper

A file browser utility for Databricks Volumes. 
The volumes files browser in our console does not present a native way to quickly examine documents and images, it only displays files. This app allows users to browse a volume, view images, PDFs, and also upload files through a web browser. 


Enables org and domain users that do not have Databricks console access to collaborate view upload and download files. 
It potentially opens up collaboration with files and Databricks volumes to a wider user group beyond console users.

Architecture:

![image](https://github.com/user-attachments/assets/0151c6d9-7410-42f4-8338-d2e518b5dbbf)


Example use cases:

- Users across organizations can share files for integration with model development or for analysis

 - Org business users can upload large data exports (CSVs, JSON, XML) to data teams directly into Databricks volumes. Data teams can ingest files and return with a Databricks apps with visualizations embedded for an improved workflow without the need to learn the Databricks console.

- Future workflows can be created to integrate this tool into a self service workflow for visualizations or NLP genie interfaces"


## Setup

Clone this repository or download and upload the files to your Databricks Workspace.

Within the Databricks console, visit Compute ->Apps. Under choose how to start, select Custom. Click next.
Give your app a name and click create.

After your App is deployed you will need to point it the volume-helper files.
After the compute for your app has started you will need to create a deployment. Click Deploy within the Apps page.

You will be prompted to create a deployment
![image](https://github.com/user-attachments/assets/7e0b8494-7b5e-4297-b6b4-1076e50b79a5)

Select the folder that has your app, click select to proceed. Click Deploy to build and deploy your app.
![image](https://github.com/user-attachments/assets/6a226b34-3826-4ef6-983b-4b453ab8b6e2)

## App resource dependencies

By specifying the UC Volume resource type and resource mapping, the service principal associated with your app will be able to either read or read and write to your volume.
After your app is deployed click Edit.

Within the edit app menu, modify the resource type, volume location, and permissions. If you have not already created a volume and put some files there, now is the time to do that.
![image](https://github.com/user-attachments/assets/1b08d734-459f-41a8-8c45-94399765700c)

## Create a personal access token (PAT)

Within the workspace settings, visit User -> Developer and generate a new token. You will copy the token and put it in your app's code.
![image](https://github.com/user-attachments/assets/69b92ca7-5d3d-4dde-aeec-e0dbe7d9eb00)


![image](https://github.com/user-attachments/assets/0859f766-44d0-4e62-9509-0055f412d73c)

## Update code and deploy

Within your app.py file, update the host from your workspace URL and the token from the PAT previously generated
![image](https://github.com/user-attachments/assets/fa79e03c-31b6-45a0-95e9-f83a53485f81)

Now, deploy your application and test the running url. Enjoy the Volume helper app!

