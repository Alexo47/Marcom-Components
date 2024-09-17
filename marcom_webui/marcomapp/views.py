from django.shortcuts import render
from neo4j import GraphDatabase

# Define Neo4j connection details
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "marcomapp"

# Initialize Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def index(request):
    """
    Render the index page and handle search requests only when the user clicks the 'Search' button.
    """
    components = []  # Initialize an empty list to store the results

    print("Index view called.")  # Debugging line

    # Check if the request is a search request (i.e., triggered by the 'Search' button)
    if 'search' in request.GET:  # 'search' is the name of the search button in the HTML form
        print("Search button clicked.")  # Debugging line
        domain = request.GET.get('comp_domain')
        about = request.GET.get('comp_about')
        context = request.GET.get('comp_context')
        size = request.GET.get('comp_size')

        print(f"Search parameters - Domain: {domain}, About: {about}, Context: {context}, Size: {size}")  # Debugging line

        # Start constructing the Cypher query
        query = "MATCH (c:Component) "
        conditions = []

        # Add conditions based on selected filters
        if domain:
            conditions.append(f"c.comp_domain = '{domain}'")
        if about:
            conditions.append(f"c.comp_about = '{about}'")
        if context:
            conditions.append(f"c.comp_context = '{context}'")
        if size:
            if size == "bullet":
                conditions.append("c.comp_size <= 50")
            elif size == "summary":
                conditions.append("c.comp_size <= 500")
            elif size == "description":
                conditions.append("c.comp_size <= 1000")
            elif size == "overview":
                conditions.append("c.comp_size <= 3000")

        # If conditions exist, append them to the query
        if conditions:
            query += "WHERE " + " AND ".join(conditions)

        # Complete the query
        query += " RETURN c.comp_name AS name, c.comp_domain AS domain, c.comp_about AS about, c.comp_context AS context, c.comp_size AS size, c.comp_key AS key"

        print(f"Cypher query: {query}")  # Debugging line

        try:
            # Execute the query
            with driver.session() as session:
                components = session.run(query).data()
                print(f"Query results: {components}")  # Debugging line
        except Exception as e:
            print(f"Error executing query: {e}")

    # Render the template with the results
    return render(request, 'marcomapp/index.html', {'components': components})

def view_component(request, comp_key):
    """
    View to display the content of a specific component.
    """
    content = "Component not found."  # Default message if component is not found

    try:
        with driver.session() as session:
            # Fetch the component content using the comp_key
            query = "MATCH (c:Component {comp_key: $comp_key}) RETURN c.comp_content AS content"
            result = session.run(query, comp_key=comp_key).single()
            
            if result and result.get("content"):
                content = result["content"]

    except Exception as e:
        print(f"Error fetching component content: {e}")

    return render(request, 'marcomapp/view_component.html', {'content': content})
