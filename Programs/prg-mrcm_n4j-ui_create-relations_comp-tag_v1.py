import os
import csv
import spacy
from neo4j import GraphDatabase
from datetime import datetime

# Initialize the NLP model (ensure spaCy's English model is installed)
nlp = spacy.load("en_core_web_sm")

# Neo4j connection settings
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "marcomapp"

# Log file path
LOG_FILE_PATH = r'D:\##ITD2\#SWDEV-Projects\Marcom-DB\log-marcom_comp-relation-tag_operations.csv'

# Explicit set for filter words
FILTER_WORDS = {'a', 'an', 'the', 'my', 'i'}

def extract_tags_from_text(text):
    """
    Extracts meaningful tags from the text using NLP.
    This uses Named Entity Recognition (NER) and keyword extraction.
    """
    doc = nlp(text)
    
    # Collect named entities as tags
    original_tags = []
    filtered_tags = []
    
    # Process named entities
    for ent in doc.ents:
        if ent.label_ in {'ORG', 'GPE', 'PERSON', 'PRODUCT', 'DATE', 'MONEY'}:
            original_tags.append(ent.text)
            filtered_tags.append(ent.text.lower())  # Convert to lowercase for consistency

    # Process noun chunks for additional keyword extraction
    for chunk in doc.noun_chunks:
        # Split the chunk text into words
        words = chunk.text.split()
        # Remove filter words only if they appear at the beginning of the chunk
        if words[0].lower() in FILTER_WORDS:
            filtered_chunk = ' '.join(words[1:])  # Remove the first word
        else:
            filtered_chunk = ' '.join(words)  # Keep all words as is

        # Convert the filtered chunk to lowercase for consistent processing
        original_tags.append(chunk.text)
        filtered_tags.append(filtered_chunk.lower())

    # Prepare tags for logging: Pair each original tag with its filtered version
    tag_pairs = list(zip(original_tags, filtered_tags))
    
    return filtered_tags  # Return the list of filtered tags

def log_operation(result, tag_name, comp_name, relations_count=None):
    """
    Logs the operation to the CSV file.
    """
    # Get the current date and time
    date_time_stamp = datetime.now()
    date_stamp = date_time_stamp.strftime("%Y-%m-%d")
    time_stamp = date_time_stamp.strftime("%H:%M")

    # Check if the log file exists, and if not, create it with a header
    file_exists = os.path.isfile(LOG_FILE_PATH)
    
    # Append to the log file during a run
    with open(LOG_FILE_PATH, 'a' if file_exists else 'w', newline='', encoding='utf-8') as log_file:
        writer = csv.writer(log_file)
        if not file_exists:
            writer.writerow(['Operation Result', 'Tag Name', 'Component Name', 'Date', 'Time', 'Relations Count'])  # Write header only once
        writer.writerow([result, tag_name, comp_name, date_stamp, time_stamp, relations_count if relations_count is not None else ''])

def fetch_components_from_neo4j(driver):
    """
    Fetch all Component nodes from Neo4j.
    """
    query = "MATCH (c:Component) RETURN c.comp_name AS name, c.comp_domain AS domain, c.comp_about AS about, c.comp_context AS context, c.comp_size AS size, c.comp_content AS content, c.comp_key AS key"
    with driver.session() as session:
        result = session.run(query)
        return result.data()

def create_relationships(driver, comp_name, comp_key, filtered_tags):
    """
    Create or merge relationships between Component and Tag nodes in Neo4j.
    """
    relationships_created = 0  # Counter for the number of relationships created

    with driver.session() as session:
        for tag_name in filtered_tags:
            # Check if Tag exists (case-insensitive)
            check_query = "MATCH (t:Tag) WHERE toLower(t.tag_name) = $tag_name RETURN t"
            tag_exists = session.run(check_query, tag_name=tag_name).single()

            if tag_exists:
                # Create/merge the relationships
                merge_query1 = """
                MATCH (c:Component {comp_key: $comp_key}), (t:Tag {tag_name: $tag_name})
                MERGE (c)-[:HAS_TAG]->(t)
                """
                merge_query2 = """
                MATCH (c:Component {comp_key: $comp_key}), (t:Tag {tag_name: $tag_name})
                MERGE (t)-[:TAG_OF]->(c)
                """
                session.run(merge_query1, comp_key=comp_key, tag_name=tag_name)
                session.run(merge_query2, comp_key=comp_key, tag_name=tag_name)
                print(f"Related tag '{tag_name}' with Component '{comp_name}'.")
                log_operation('related tag', tag_name, comp_name)
                relationships_created += 1  # Increment the counter
            else:
                print(f"Skipped tag '{tag_name}' for Component '{comp_name}' as it does not exist.")
                log_operation('skipped tag', tag_name, comp_name)

    # Print and log the number of relationships created for the current component
    print(f"Total relationships created for Component '{comp_name}': {relationships_created}")
    log_operation('summary', 'N/A', comp_name, relations_count=relationships_created)

def prompt_user_for_processing(comp_data, process_all):
    """
    Prompt the user with Component properties and ask whether to process.
    """
    if process_all:
        return 'y'
    
    print(f"\nComponent: {comp_data['name']}")
    print(f"Domain: {comp_data['domain']}")
    print(f"About: {comp_data['about']}")
    print(f"Context: {comp_data['context']}")
    print(f"Size: {comp_data['size']} characters\n")
    user_input = input("[a]ll to process all, [y]es to process this Component, [s]kip to next, [x] to exit: ").strip().lower()
    return user_input

def process_components(driver):
    """
    Process components to create relationships with tags.
    """
    components = fetch_components_from_neo4j(driver)
    process_all = False  # Flag to check if 'All' option is selected
    
    for comp_data in components:
        user_input = prompt_user_for_processing(comp_data, process_all)
        
        if user_input == 'x':
            print("Exiting the program...")
            return
        elif user_input == 's':
            print("Skipping this component...\n")
            continue
        elif user_input == 'a':
            print("Processing all components without further prompts...\n")
            process_all = True
            user_input = 'y'  # Set to 'yes' to process the current component
        if user_input == 'y':
            filtered_tags = extract_tags_from_text(comp_data['content'])
            create_relationships(driver, comp_data['name'], comp_data['key'], filtered_tags)
        else:
            print("Invalid input. Please enter [a], [y], [s], or [x].")

if __name__ == "__main__":
    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        process_components(driver)
    finally:
        driver.close()
