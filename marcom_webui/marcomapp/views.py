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
    applied_filters = {}

    # Check if the request is a search request (i.e., triggered by the 'Search' button)
    search_triggered = request.GET.get('search_triggered', None)

    if search_triggered:
        # Search is triggered, process the filters and fetch components
        domain = request.GET.getlist('comp_domain')
        about = request.GET.getlist('comp_about')
        context = request.GET.getlist('comp_context')
        size = request.GET.get('comp_size')

        # Start constructing the Cypher query
        query = "MATCH (c:Component) "
        conditions = []

        # Add conditions based on selected filters
        if domain:
            conditions.append(f"c.comp_domain IN {domain}")
            applied_filters['Domain'] = ', '.join(domain)

        if about:
            conditions.append(f"c.comp_about IN {about}")
            applied_filters['About'] = ', '.join(about)

        if context:
            conditions.append(f"c.comp_context IN {context}")
            applied_filters['Context'] = ', '.join(context)

        if size:
            if size == "bullet":
                conditions.append("c.comp_size <= 50")
                applied_filters['Size'] = "Bullet (<50)"
            elif size == "summary":
                conditions.append("c.comp_size <= 500")
                applied_filters['Size'] = "Summary (<500)"
            elif size == "description":
                conditions.append("c.comp_size <= 1000")
                applied_filters['Size'] = "Description (<1000)"
            elif size == "overview":
                conditions.append("c.comp_size <= 3000")
                applied_filters['Size'] = "Overview (<3000)"

        # If conditions exist, append them to the query
        if conditions:
            query += "WHERE " + " AND ".join(conditions)

        # Complete the query
        query += " RETURN c.comp_name AS name, c.comp_domain AS domain, c.comp_about AS about, c.comp_context AS context, c.comp_size AS size, c.comp_content AS content"

        # Execute the query
        with driver.session() as session:
            components = session.run(query).data()

    # No search is triggered, and no components are fetched.
    else:
        applied_filters['Status'] = "No search triggered. Please select filters and search."

    # Render the template with the results and applied filters
    return render(request, 'marcomapp/index.html', {'components': components, 'applied_filters': applied_filters})

def view_component(request, comp_key):
    """
    View to display the content of a specific component.
    """
    with driver.session() as session:
        # Fetch the component content using the comp_key
        query = "MATCH (c:Component {comp_key: $comp_key}) RETURN c.comp_content AS content"
        result = session.run(query, comp_key=comp_key).single()
        
        if result:
            content = result["content"]
        else:
            content = "Component not found."

    return render(request, 'marcomapp/view_component.html', {'content': content})
