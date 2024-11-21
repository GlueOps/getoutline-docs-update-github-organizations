import requests
import os
import glueops.setup_logging

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logger = glueops.setup_logging.configure(level=LOG_LEVEL)

class GitHubClient:
    def __init__(self, github_token, github_api_url):
        self.github_token = github_token
        self.github_api_url = github_api_url

    def get_organizations(self):
        logger.debug("Fetching organizations from GitHub API.")
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
        }
        organizations = []
        url = f"{self.github_api_url}/user/orgs"

        try:
            while url:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                organizations.extend(response.json())
                logger.debug(f"Fetched {len(response.json())} organizations.")

                # Check for pagination
                links = response.headers.get('Link')
                if links:
                    next_link = None
                    for link in links.split(','):
                        if 'rel="next"' in link:
                            next_link = link[link.find('<') + 1:link.find('>')]
                            break
                    url = next_link
                else:
                    url = None

            logger.debug("All organizations fetched successfully.")
            return organizations
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching organizations: {e}")
            raise


    def generate_markdown(github_orgs):
        logger.debug("Generating markdown for organizations.")
        markdown_content = "> This page is automatically generated. Any manual changes will be lost. See: https://github.com/GlueOps/getoutline-docs-update-github \n\n"
        markdown_content = "# Full list of GitHub Organizations\n\n"
        markdown_content += "| Organization Name | Description |\n"
        markdown_content += "|-------------------|-------------|\n"
        
        for org in github_orgs:
            name = org['login']
            url = f"https://github.com/{org['login']}"
            description = org.get('description', 'No description available.')
            markdown_content += f"| [{name}]({url}) | {description} |\n"
        
        logger.debug("Markdown generation completed.")
        return markdown_content


    def get_repositories(self, org_login):
        logger.debug(f"Fetching repositories for organization: {org_login}")
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
        }
        repositories = []
        url = f"{self.github_api_url}/orgs/{org_login}/repos"

        try:
            while url:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                repositories.extend(response.json())
                logger.debug(f"Fetched {len(response.json())} repositories for organization: {org_login}")

                # Check for pagination
                links = response.headers.get('Link')
                if links:
                    next_link = None
                    for link in links.split(','):
                        if 'rel="next"' in link:
                            next_link = link[link.find('<') + 1:link.find('>')]
                            break
                    url = next_link
                else:
                    url = None

            return repositories
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching repositories for organization {org_login}: {e}")
            raise

    def get_repository_topics(self, org_login, repo_name):
        logger.debug(f"Fetching topics for repository: {org_login}/{repo_name}")
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.mercy-preview+json',
        }
        url = f"{self.github_api_url}/repos/{org_login}/{repo_name}/topics"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            topics = response.json().get('names', [])
            logger.debug(f"Fetched topics for repository: {org_login}/{repo_name}")
            return topics
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching topics for repository {org_login}/{repo_name}: {e}")
            raise

    def generate_markdown_for_org(self, org_login):
        logger.debug(f"Generating markdown for organization: {org_login}")
        markdown_content = f"# Repositories for {org_login}\n\n"
        markdown_content += "| Repository | Description | Topics |\n"
        markdown_content += "|------------|-------------|--------|\n"
        
        org_repos = self.get_repositories(org_login)
        for repo in org_repos:
            repo_name = repo['name']
            repo_description = repo.get('description', 'No description available.')
            repo_topics = self.get_repository_topics(org_login, repo_name)
            topics_str = ', '.join(repo_topics)
            markdown_content += f"| [{repo_name}](https://github.com/{org_login}/{repo_name}) | {repo_description} | {topics_str} |\n"
        
        logger.debug(f"Markdown generation completed for organization: {org_login}")
        return markdown_content