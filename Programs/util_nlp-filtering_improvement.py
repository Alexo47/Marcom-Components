import pandas as pd
from neo4j import GraphDatabase
import os
import spacy
import csv  # Import the csv module

# Initialize the NLP model (ensure spaCy's English model is installed)
nlp = spacy.load("en_core_web_sm")

# Neo4j connection settings
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "marcomapp"

# Log file path
LOG_FILE_PATH = r'D:\##ITD2\#SWDEV-Projects\Marcom-DB\DATA\log_nlp-filtering_tags.csv'

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
            filtered_tags.append(ent.text)  # No filtering applied to named entities

    # Process noun chunks for additional keyword extraction
    for chunk in doc.noun_chunks:
        # Split the chunk text into words
        words = chunk.text.split()
        # Remove filter words only if they appear at the beginning of the chunk
        if words[0].lower() in FILTER_WORDS:
            filtered_chunk = ' '.join(words[1:])  # Remove the first word
        else:
            filtered_chunk = ' '.join(words)  # Keep all words as is

        # Add both the original and filtered tags to their respective lists
        original_tags.append(chunk.text)
        filtered_tags.append(filtered_chunk)

    # Prepare tags for logging: Pair each original tag with its filtered version
    tag_pairs = list(zip(original_tags, filtered_tags))
    log_tags_to_csv(tag_pairs)
    
    return tag_pairs  # Return the list of tag pairs

def log_tags_to_csv(tag_pairs):
    """
    Logs the original and filtered tags to the CSV file.
    """
    # Check if the log file exists, and if not, create it with a header
    file_exists = os.path.isfile(LOG_FILE_PATH)
    
    # Append to the log file during a run
    with open(LOG_FILE_PATH, 'a' if file_exists else 'w', newline='', encoding='utf-8') as log_file:
        writer = csv.writer(log_file)
        if not file_exists:
            writer.writerow(['Original Tag', 'Filtered Tag'])  # Write header only once
        for original_tag, filtered_tag in tag_pairs:
            writer.writerow([original_tag, filtered_tag])

def fetch_components_from_neo4j(driver):
    """
    Fetch all Component nodes from Neo4j.
    """
    query = "MATCH (c:Component) RETURN c.comp_name AS name, c.comp_domain AS domain, c.comp_about AS about, c.comp_context AS context, c.comp_size AS size, c.comp_content AS content, c.comp_key AS key"
    with driver.session() as session:
        result = session.run(query)
        return result.data()

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
    user_input = input("[y]es to process, [x] to exit, [s]kip to next, [A]ll: ").strip().lower()
    return user_input

def process_components(driver):
    """
    Process components for NLP filtering improvement.
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
        elif user_input == 'y':
            tag_pairs = extract_tags_from_text(comp_data['content'])
            print(f"\nExtracted Tags for Component '{comp_data['name']}':")
            for original_tag, filtered_tag in tag_pairs:
                print(f"[{original_tag}, {filtered_tag}]")
        else:
            print("Invalid input. Please enter [y], [x], [s], or [A].")

if __name__ == "__main__":
    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        process_components(driver)
    finally:
        driver.close()
