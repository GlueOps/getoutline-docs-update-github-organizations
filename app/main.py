import requests
import os
import glueops.setup_logging



GITHUB_API_URL = "https://api.github.com"
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
    """Retrieve environment variable or return default if not set."""
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

def get_organizations():
    logger.debug("Fetching organizations from GitHub API.")
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
    }
    try:
        response = requests.get(f"{GITHUB_API_URL}/user/orgs", headers=headers)
        response.raise_for_status()
        logger.debug("Organizations fetched successfully.")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching organizations: {e}")
        return []

def generate_markdown(orgs):
    logger.debug("Generating markdown for organizations.")
    markdown_content = "# GitHub Organizations\n\n"
    markdown_content += "| Organization Name | Description |\n"
    markdown_content += "|-------------------|-------------|\n"
    
    for org in orgs:
        name = org['login']
        url = f"https://github.com/{org['login']}"
        description = org.get('description', 'No description available.')
        markdown_content += f"| [{name}]({url}) | {description} |\n"
    
    logger.debug("Markdown generation completed.")
    return markdown_content

def update_document(markdown_text):
    logger.debug("Updating document on Outline.")
    url = "https://app.getoutline.com/api/documents.update"
    payload = {
        "id": GETOUTLINE_DOCUMENT_ID,
        "text": markdown_text
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GETOUTLINE_API_TOKEN}"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"Document update response code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating document: {e}")

def main():
    logger.info("Starting.")
    organizations = get_organizations()
    if organizations:
        markdown = generate_markdown(organizations)
        update_document(markdown)
    else:
        logger.warning("No organizations found.")
    logger.info("Finished.")

if __name__ == "__main__":
    main()