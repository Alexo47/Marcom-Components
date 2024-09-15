# Marcom-DB

Marcom-DB is a project aimed at managing and querying components related to marketing communications. The project involves interacting with a Neo4j database to dynamically create relationships between different components and tags, and providing a user interface for searching and filtering these components.

## Project Structure

- **Programs/**: This folder contains all the main Python scripts for the project.

  - **prg-neo4j_marcom-components_v0.py**: Manages the creation and population of `Component` nodes in the Neo4j database.
  - **prg-neo4j_marcom-tags.py**: Manages the creation and population of `Tag` nodes in the Neo4j database.
  - **prg-mrcm_n4j-ui_create-relations_comp-tag_v0.py**: Creates relationships between `Component` and `Tag` nodes dynamically using NLP-based tag extraction.
  - **prg-mrcm_n4j-ui_db-queries_v0.py**: A console-based UI for querying the Neo4j database with various filters.
  - **prg-mrcm_n4j-ui_db-queries_v1.py**: An extended version that allows multiple constraints in component selection.
  - **util_nlp-filtering_improvement.py**: A utility program for improving NLP filtering by removing unnecessary words and fine-tuning tag extraction.
  - **fixinc-legacy-toDelete/**: Contains legacy code and files to be reviewed or deleted.

- **.gitignore**: Specifies which files and folders should be ignored by Git.

## Project Setup

### Prerequisites

1. **Python 3.8+**: Ensure you have Python installed.
2. **Neo4j 5.23.0 / Enterprise**: Make sure Neo4j is installed and running on your local machine with the following settings:

   - **User**: `neo4j`
   - **Password**: `marcomapp`
   - **Bolt Port**: `7687`
   - **HTTP Port**: `7474`
   - **HTTPS Port**: `7473`

3. **Required Python Packages**:
   - `spacy`: For natural language processing.
   - `neo4j`: For interacting with the Neo4j database.
   - Install these packages using:
   ```bash
   pip install spacy neo4j
   python -m spacy download en_core_web_sm
   ```
