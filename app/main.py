import requests
import os
import glueops.setup_logging
import glueops.getoutline
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from github import GitHubClient

GITHUB_API_URL = "https://api.github.com"
GETOUTLINE_API_URL = "https://app.getoutline.com"

# Environment Variables
REQUIRED_ENV_VARS = [
    "GITHUB_TOKEN",
    "GETOUTLINE_DOCUMENT_ID",
    "GETOUTLINE_API_TOKEN",
]
OPTIONAL_ENV_VARS = {
    "VERSION": "unknown",
    "COMMIT_SHA": "unknown",
    "BUILD_TIMESTAMP": "unknown",
}

def get_env_variable(var_name: str, default=None):
    """
    Retrieve environment variable or return default if not set.

    :param var_name: Name of the environment variable.
    :param default: Default value if the environment variable is not set.
    :return: Value of the environment variable or default.
    :raises EnvironmentError: If a required environment variable is not set.
    """
    value = os.getenv(var_name, default)
    if var_name in REQUIRED_ENV_VARS and value is None:
        logger.error(f"Environment variable '{var_name}' is not set.")
        raise EnvironmentError(f"Environment variable '{var_name}' is required but not set.")
    logger.debug(f"Environment variable '{var_name}' retrieved.")
    return value

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logger = glueops.setup_logging.configure(level=LOG_LEVEL)
logger.info(f"Logger initialized with level: {LOG_LEVEL}")
logger.info({
    "version": os.getenv("VERSION", "unknown"),
    "commit_sha": os.getenv("COMMIT_SHA", "unknown"),
    "build_timestamp": os.getenv("BUILD_TIMESTAMP", "unknown")
})

try:
    GITHUB_TOKEN = get_env_variable('GITHUB_TOKEN')
    GETOUTLINE_DOCUMENT_ID = get_env_variable('GETOUTLINE_DOCUMENT_ID')
    GETOUTLINE_API_TOKEN = get_env_variable('GETOUTLINE_API_TOKEN')
    VERSION = get_env_variable('VERSION', OPTIONAL_ENV_VARS['VERSION'])
    COMMIT_SHA = get_env_variable('COMMIT_SHA', OPTIONAL_ENV_VARS['COMMIT_SHA'])
    BUILD_TIMESTAMP = get_env_variable('BUILD_TIMESTAMP', OPTIONAL_ENV_VARS['BUILD_TIMESTAMP'])
    logger.info("All required environment variables retrieved successfully.")
except EnvironmentError as env_err:
    logger.critical(f"Environment setup failed: {env_err}")
    raise

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=60, max=120), retry=retry_if_exception_type(requests.exceptions.RequestException))
def retry_create_document(client, parent_id, title, text):
    """
    Retry creating a document in Outline.

    :param client: GetOutlineClient instance.
    :param parent_id: Parent document ID.
    :param title: Title of the new document.
    :param text: Content of the new document.
    :return: Result of the create_document method.
    """
    return client.create_document(parent_id, title, text)

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=60, max=120), retry=retry_if_exception_type(requests.exceptions.RequestException))
def retry_update_document(client, text):
    """
    Retry updating a document in Outline.

    :param client: GetOutlineClient instance.
    :param text: New content for the document.
    :return: Result of the update_document method.
    """
    return client.update_document(text)

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=60, max=120), retry=retry_if_exception_type(requests.exceptions.RequestException))
def retry_generate_markdown_for_org(client, github_org_name):
    """
    Retry generating markdown content for a GitHub organization.

    :param client: GitHubClient instance.
    :param github_org_name: Name of the GitHub organization.
    :return: Markdown content as a string.
    """
    return client.generate_markdown_for_org(github_org_name)

def main():
    """
    Main function to update GitHub organizations documentation in Outline.
    """
    logger.info("Starting GitHub Doc Updates.")
    GetOutlineClient = glueops.getoutline.GetOutlineClient(GETOUTLINE_API_URL, GETOUTLINE_DOCUMENT_ID, GETOUTLINE_API_TOKEN)
    github_client = GitHubClient(GITHUB_TOKEN, GITHUB_API_URL)
    organizations = github_client.get_organizations()
    if organizations:
        logger.info(f"Updating document letting folks know we are updating the list of organizations.")
        retry_update_document(GetOutlineClient, "# UPDATING..... \n\n #          check back shortly.....\n\n\n")
        parent_id = GetOutlineClient.get_document_uuid()
        children = GetOutlineClient.get_children_documents_to_delete(parent_id)
        for id in children:
            GetOutlineClient.delete_document(id)
        for org in organizations:
            org_specific_markdown_content = retry_generate_markdown_for_org(github_client, org["login"])
            retry_create_document(GetOutlineClient, parent_id, org["login"], org_specific_markdown_content)
        markdown = GitHubClient.generate_markdown(organizations)
        retry_update_document(GetOutlineClient, markdown)

        logger.info("Finished GitHub Doc Updates.")
    else:
        logger.warning("No organizations found.")
        
if __name__ == "__main__":
    main()