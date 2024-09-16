import pandas as pd
import hashlib
from neo4j import GraphDatabase
from datetime import datetime
import os
import io
import csv

# Google API libraries
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload  # Importing the MediaIoBaseDownload class

# Neo4j connection settings
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "marcomapp"  # Change this to your actual password

# File paths
CSV_PATH = r'D:\##ITD2\#SWDEV-Projects\Marcom-Components\DATA\Notion-Exported'
LOG_FILE_PATH = r'D:\##ITD2\#SWDEV-Projects\Marcom-Components\SWDEV\LOGS\log-marcom-components_operations.csv'

# Google Drive API settings
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
CREDENTIALS_PATH = 'D:\##ITD2\client_secret_google-drive_marcom-components.json'  # Path to your credentials file

def authenticate_google_drive():
    """
    Authenticates and returns the Google Drive service instance.
    """
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def download_file_from_google_drive(service, file_id):
    """
    Downloads a file's content from Google Drive.
    """
    request = service.files().get_media(fileId=file_id)
    file_content = io.BytesIO()
    downloader = MediaIoBaseDownload(file_content, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    return file_content.getvalue().decode('utf-8')

def extract_file_id_from_url(url):
    """
    Extracts the file ID from a Google Drive link.
    """
    if 'id=' in url:
        return url.split('id=')[1].split('&')[0]
    return None

def prompt_for_file():
    """
    Prompts the user for the CSV file to process.
    """
    default_file_name = 'notion-2-excel_marcom-components_20240912-v5'
    while True:
        user_input = input(f"Do you want to process the file '{default_file_name}.csv'? [y]es/[x]exit/[e/new file name]: ").strip().lower()
        if user_input == 'x':
            print("Exiting the program...")
            exit(0)
        elif user_input == 'y':
            return f"{default_file_name}.csv"
        elif user_input.startswith('e/'):
            new_file_name = user_input[2:].strip()
            if os.path.exists(os.path.join(CSV_PATH, f"{new_file_name}.csv")):
                return f"{new_file_name}.csv"
            else:
                print(f"File '{new_file_name}.csv' not found in the directory. Please try again.")
        else:
            print("Invalid input. Please enter [y]es, [x]exit, or [e/new file name].")

def calculate_properties(row, service):
    """
    Calculates properties of the component based on the CSV data.
    """
    file_id = extract_file_id_from_url(row["Source"])
    comp_link = row["Source"]

    if file_id:
        comp_content = download_file_from_google_drive(service, file_id)
        comp_size = len(comp_content)
        comp_key = hashlib.sha256(comp_content.encode()).hexdigest()
        return comp_link, comp_content, comp_size, comp_key
    else:
        raise ValueError("Invalid Google Drive link format.")

def log_operation(result, comp_name, comp_key):
    """
    Logs the operation in the log file.
    """
    date_time_stamp = datetime.now()
    date_stamp = date_time_stamp.strftime("%Y-%m-%d")
    time_stamp = date_time_stamp.strftime("%H:%M")
    
    # Check if the log file exists and has the correct header
    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'w', newline='', encoding='utf-8') as log_file:
            writer = csv.writer(log_file)
            writer.writerow(['Operation Result', 'Component Name', 'Component Key', 'Date', 'Time'])

    # Append the log entry to the file
    with open(LOG_FILE_PATH, 'a', newline='', encoding='utf-8') as log_file:
        writer = csv.writer(log_file)
        writer.writerow([result, comp_name, comp_key, date_stamp, time_stamp])

def create_component(tx, properties):
    """
    Sends a create/merge request to Neo4j to add/update a component node.
    """
    query = """
    MERGE (c:Component {comp_key: $comp_key})
    SET c.comp_name = $comp_name,
        c.comp_domain = $comp_domain,
        c.comp_about = $comp_about,
        c.comp_context = $comp_context,
        c.comp_comment = $comp_comment,
        c.comp_link = $comp_link,
        c.comp_content = $comp_content,
        c.comp_size = $comp_size
    RETURN c
    """
    tx.run(query, properties)

def process_components(file_name, service):
    """
    Processes the components from the CSV file and sends requests to Neo4j.
    """
    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        df = pd.read_csv(os.path.join(CSV_PATH, file_name))

        for _, row in df.iterrows():
            try:
                comp_link, comp_content, comp_size, comp_key = calculate_properties(row, service)
                properties = {
                    "comp_name": row["Component Name"],
                    "comp_domain": row["Domain"],
                    "comp_about": row["About"],
                    "comp_context": row["Context"],
                    "comp_comment": "",  # Initially empty, can be modified later
                    "comp_link": comp_link,
                    "comp_content": comp_content,
                    "comp_size": comp_size,
                    "comp_key": comp_key
                }
                
                with driver.session() as session:
                    try:
                        session.write_transaction(create_component, properties)
                        log_operation('Added component', properties['comp_name'], properties['comp_key'])
                        print(f"Component '{properties['comp_name']}' processed and added to Neo4j.")
                    except Exception as e:
                        log_operation(f'Failed to add component: {str(e)}', properties['comp_name'], properties['comp_key'])
                        print(f"Failed to process component '{properties['comp_name']}': {e}")
            except Exception as e:
                print(f"Error processing file: {str(e)}")

    finally:
        driver.close()

if __name__ == "__main__":
    # Authenticate Google Drive
    drive_service = authenticate_google_drive()

    # Prompt for CSV file
    csv_file_name = prompt_for_file()
    process_components(csv_file_name, drive_service)
