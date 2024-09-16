import pandas as pd
from neo4j import GraphDatabase
from datetime import datetime
import os
import csv

# Neo4j connection settings
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "marcomapp"  # Change this to your actual password

# File paths
CSV_PATH = r'D:\##ITD2\#SWDEV-Projects\Marcom-Components\DATA'
LOG_FILE_PATH = r'D:\##ITD2\#SWDEV-Projects\Marcom-Components\SWDEV\LOGS\log-marco_tags-operations.csv'

def prompt_for_file():
    """
    Prompts the user for the CSV file to process.
    """
    default_file_name = 'db_marcom-taxonomy_revAD'
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

def log_operation(result, tag_name):
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
            writer.writerow(['Operation Result', 'Tag Name', 'Date', 'Time'])

    # Append the log entry to the file
    with open(LOG_FILE_PATH, 'a', newline='', encoding='utf-8') as log_file:
        writer = csv.writer(log_file)
        writer.writerow([result, tag_name, date_stamp, time_stamp])

def create_tag_constraint(tx):
    """
    Creates a unique constraint on the 'tag-name' property of the 'Tags' Node.
    """

    constraint_query = "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Tag) REQUIRE t.tag_name IS UNIQUE"
    tx.run(constraint_query)

def create_or_merge_tag(tx, tag_name):
    """
    Sends a create/merge request to Neo4j to add/update a tag node.
    """
    query = """
    MERGE (t:Tag {tag_name: $tag_name})
    RETURN t
    """
    result = tx.run(query, tag_name=tag_name)
    return result.single()

def process_tags(file_name):
    """
    Processes the tags from the CSV file and sends requests to Neo4j.
    """
    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            # Create unique constraint on tag-name
            session.write_transaction(create_tag_constraint)

        df = pd.read_csv(os.path.join(CSV_PATH, file_name))

        with driver.session() as session:
            for _, row in df.iterrows():
                tag_name = row['Tag'].strip()
                try:
                    result = session.write_transaction(create_or_merge_tag, tag_name)
                    if result:
                        log_operation('Added tag', tag_name)
                        print(f"Tag '{tag_name}' processed and added to Neo4j.")
                    else:
                        log_operation('Failed to add tag', tag_name)
                        print(f"Failed to process tag '{tag_name}'.")
                except Exception as e:
                    log_operation(f'Error: {str(e)}', tag_name)
                    print(f"Error processing tag '{tag_name}': {e}")

    finally:
        driver.close()

if __name__ == "__main__":
    # Prompt for CSV file
    csv_file_name = prompt_for_file()
    process_tags(csv_file_name)
