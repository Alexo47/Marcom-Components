import re
from neo4j import GraphDatabase

# Neo4j connection settings
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "marcomapp"

def validate_criteria(criteria):
    """
    Validates the user's input criteria for constructing the Cypher queries.
    """
    # Regex pattern to match valid criteria inputs
    pattern = r"^[\(\)\s'&|a-zA-Z0-9]+$"
    # Check if the input matches the allowed characters and operators
    return bool(re.match(pattern, criteria))

def extract_tags_from_criteria(criteria):
    """
    Extracts individual tags and logical operators from the user-provided criteria.
    """
    # Use regex to split criteria by spaces while retaining logical operators
    tokens = re.findall(r"[()&|]|'[^']+'", criteria)
    return tokens

def fetch_property_values(driver, prop):
    """
    Fetches unique values for a given property from the Component nodes in Neo4j.
    """
    query = f"MATCH (c:Component) RETURN DISTINCT c.{prop} AS value"
    with driver.session() as session:
        results = session.run(query)
        return [record["value"] for record in results]

def prompt_user_for_property(prop_name, values):
    """
    Prompts the user to select a filter for a specific property.
    """
    print(f"Property: '{prop_name}'")
    for i, value in enumerate(values, start=1):
        print(f"[{i}] - {value}")

    while True:
        user_input = input("Enter your choice (e.g., /s to skip, /x to exit, /n for selection): ").strip()
        if user_input == '/x':
            print("Exiting the program...")
            exit()
        elif user_input == '/s':
            return None
        elif user_input.startswith('/') and user_input[1:].isdigit():
            choice = int(user_input[1:])
            if 1 <= choice <= len(values):
                return values[choice - 1]
        print("Invalid input. Please enter a valid choice.")

def generate_cypher_query(constraints, criteria):
    """
    Generates the Cypher query based on user input constraints and tag criteria.
    """
    match_conditions = " AND ".join([f"c.{prop} = '{value}'" for prop, value in constraints.items() if value])
    if criteria:
        tag_conditions = criteria.replace("&", " AND ").replace("|", " OR ")
        query = f"""
        MATCH (c:Component)-[:HAS_TAG]->(t:Tag)
        WHERE {match_conditions} AND t.tag_name CONTAINS {tag_conditions}
        RETURN c.comp_name AS ComponentName, 
               c.comp_domain AS Domain, 
               c.comp_about AS About, 
               c.comp_context AS Context, 
               c.comp_size AS Size,
               c.comp_content AS Content,
               t.tag_name AS Tag
        """
    else:
        query = f"""
        MATCH (c:Component)
        WHERE {match_conditions}
        RETURN c.comp_name AS ComponentName, 
               c.comp_domain AS Domain, 
               c.comp_about AS About, 
               c.comp_context AS Context, 
               c.comp_size AS Size,
               c.comp_content AS Content
        """
    return query

def execute_cypher_query(driver, query):
    """
    Executes the Cypher query on Neo4j and retrieves the results.
    """
    with driver.session() as session:
        results = session.run(query)
        return {record["ComponentName"]: record for record in results}

def print_results(results):
    """
    Prints the results of the query in a formatted way.
    """
    print("Results:")
    for component, result in results.items():
        print(f"Component Name: {result['ComponentName']}")
        print(f"Domain: {result['Domain']}")
        print(f"About: {result['About']}")
        print(f"Context: {result['Context']}")
        print(f"Size: {result['Size']}")
        print(f"Tag: {result.get('Tag', 'N/A')}\n")
        print(('#X' * 15) + f" <{result['ComponentName']}> content: " + ('#X' * 15))
        print(f"\n {result['Content']}")
        print('\n' + ('=X' * 15) + f" <{result['ComponentName']}> end of record" + ('=X' * 15) + '\n')

def print_constraints_summary(constraints, tag_criteria):
    """
    Prints a summary of the constraints applied in the component search.
    """
    print(f"\n" + ('/' * 30) + " Filters Applied " + ('/' * 33))
    for prop, value in constraints.items():
        if value:
            print(f"{prop}: {value}")
        else:
            print(f"{prop}: No filter applied")
    
    # Print tag constraints summary
    if tag_criteria:
        print(f"Tags: {tag_criteria}")
    else:
        print("Tags: No filter applied")

    print(('/' * 80) + f"\n")

def main():
    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    print("Welcome to the Marcom Neo4j Database Query Tool (v1)")

    # Part One: Set Constraints for Component Selection
    constraints = {}
    properties = ['comp_domain', 'comp_about', 'comp_context']

    for prop in properties:
        values = fetch_property_values(driver, prop)
        choice = prompt_user_for_property(prop, values)
        constraints[prop] = choice

    # Part Two: Set Tag Constraints
    print("Now set constraints for tags.")
    while True:
        user_input = input("Enter your query (/q/'criteria', /s to skip tag filter) or exit (/x): ").strip()

        if user_input.lower() == '/x':
            print("Exiting the program...")
            break
        elif user_input.lower() == '/s':
            # No tag filter
            criteria = None
            # Print summary of filters applied
            print_constraints_summary(constraints, criteria)
            # Generate Cypher query from constraints without tag criteria
            cypher_query = generate_cypher_query(constraints, criteria)
            # Execute the query
            results = execute_cypher_query(driver, cypher_query)
            # Print the results
            print_results(results)
            break
        elif user_input.startswith("/q/"):
            criteria = user_input[3:].strip()
            if validate_criteria(criteria):
                # Print summary of filters applied
                print_constraints_summary(constraints, criteria)
                # Generate Cypher query from constraints and criteria
                cypher_query = generate_cypher_query(constraints, criteria)
                # Execute the query
                results = execute_cypher_query(driver, cypher_query)
                # Print the results
                print_results(results)
            else:
                print("Invalid criteria format. Please enter a valid criteria.")
        else:
            print("Invalid input. Please enter '/x' to exit, '/s' to skip tag filter, or '/q/' to enter a query criteria.")

    driver.close()

if __name__ == "__main__":
    main()
