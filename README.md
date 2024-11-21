# getoutline-docs-update-github

Generates dynamic documentation of all our GitHub Organizations and their descriptions and updates GetOutline.com with these details. This makes it easier for discovery and search within getoutline.com

## Prerequisites

- Python (See version in Dockerfile))
- Docker (optional, for containerized deployment)

## Running the app

2. 
    ```sh
    pipenv install -r requirements.txt
    source .env
    python app/main.py
    ```

## Configuration

The application requires three environment variables to be set. You can create a `.env` file in the root directory of the project with the following content:

```env
export GITHUB_TOKEN=<Uses a PAT> #Assumes that all orgs a user is part of is an ORG that we own.
export GETOUTLINE_DOCUMENT_ID=<This is usually at the end of the document in the URL of the document you want to update>
export GETOUTLINE_API_TOKEN=<Token is tied to a user account in GETOUTLINE>
```
