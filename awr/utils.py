import os
import requests
from dotenv import load_dotenv
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AWRClient:
    def __init__(self):
        self.api_key = os.getenv('AWR_API_KEY')
        self.api_url_v2 = os.getenv('AWR_API_URL_V2')
        self.api_limit = int(os.getenv('AWR_API_LIMIT', 2000))
        
        # Log configuration for debugging
        logger.debug(f"API Key length: {len(self.api_key) if self.api_key else 'None'}")
        logger.debug(f"API URL: {self.api_url_v2}")
    
    def get_projects(self):
        """
        Get all projects from AWR API
        https://app.advancedwebranking.com/docs/developer-api-v2.html#get-projects-v2
        
        Working URL format:
        https://api.awrcloud.com/v2/get.php?action=projects&token=API_KEY
        """
        # Use the direct URL method
        url = f"{self.api_url_v2}?action=projects&token={self.api_key}"
        
        headers = {
            'Accept': 'application/json',
        }
        
        try:
            logger.debug(f"Making API request with direct URL: {url}")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                try:
                    # Print the raw response for debugging
                    logger.debug(f"Raw response: {response.text[:200]}")
                    
                    data = response.json()
                    
                    # The AWR API might not return response_code in successful responses
                    # Check if we have a projects array, which indicates success
                    if 'projects' in data and isinstance(data['projects'], list):
                        logger.debug(f"Found {len(data['projects'])} projects")
                        # Add response code if missing for consistent handling
                        if 'response_code' not in data:
                            data['response_code'] = 0  # Mark as success
                        return data
                    
                    # Check for API-specific error codes if present
                    elif 'response_code' in data and data['response_code'] != 0:
                        error_msg = f"{data.get('message', 'Unknown API error')} (Code: {data.get('response_code')})"
                        logger.error(f"API error: {error_msg}")
                        return {"error": error_msg, "projects": []}
                    
                    # Unknown structure but seems valid JSON
                    else:
                        logger.warning(f"Unexpected API response structure: {data}")
                        # Try to extract projects if they exist in a different format
                        if any(key.lower().startswith('project') for key in data.keys()):
                            for key in data.keys():
                                if key.lower().startswith('project'):
                                    logger.debug(f"Found potential projects under key: {key}")
                                    return {"response_code": 0, "projects": data[key]}
                        
                        # Otherwise return the raw data
                        return data
                        
                except ValueError as e:
                    error_msg = f"Could not parse JSON from API response: {str(e)}"
                    logger.error(error_msg)
                    logger.error(f"Raw response: {response.text[:500]}")
                    return {"error": error_msg, "projects": []}
            else:
                error_msg = f"API returned status code {response.status_code}"
                logger.error(error_msg)
                return {"error": error_msg, "projects": []}
                
        except Exception as e:
            error_msg = f"Exception during API request: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "projects": []}
            
    def get_project_details(self, project_id):
        """
        Get details for a specific project
        https://app.advancedwebranking.com/docs/developer-api-v2.html#get-details-v2
        
        The API requires project name, not ID, so we need to:
        1. Get the project name from ID using the projects endpoint
        2. Use the project name to make a details request
        """
        try:
            # Step 1: Get project name from ID
            projects_url = f"{self.api_url_v2}?action=projects&token={self.api_key}"
            
            logger.debug(f"Getting project list to find name for ID: {project_id}")
            projects_response = requests.get(projects_url, headers={'Accept': 'application/json'})
            
            if projects_response.status_code != 200:
                return {"error": f"Failed to get project list: {projects_response.status_code}"}
            
            projects_data = projects_response.json()
            
            # Find the project with matching ID
            project_name = None
            project_info = None
            
            if 'projects' in projects_data:
                for project in projects_data['projects']:
                    if str(project.get('id')) == str(project_id):
                        project_name = project.get('name')
                        project_info = project
                        break
            
            if not project_name:
                logger.error(f"Could not find project with ID: {project_id}")
                return {"error": f"Project with ID {project_id} not found"}
            
            logger.debug(f"Found project name: {project_name} for ID: {project_id}")
            
            # Step 2: Get project details using project name
            # URL encode the project name for the API
            import urllib.parse
            encoded_project_name = urllib.parse.quote(project_name)
            
            details_url = f"{self.api_url_v2}?action=details&project={encoded_project_name}&token={self.api_key}"
            
            logger.debug(f"Getting project details with name: {project_name}")
            details_response = requests.get(details_url, headers={'Accept': 'application/json'})
            
            if details_response.status_code != 200:
                return {"error": f"Failed to get project details: {details_response.status_code}"}
            
            try:
                # Print the raw response for debugging
                logger.debug(f"Raw project details response: {details_response.text[:200]}")
                
                details_data = details_response.json()
                
                # Check for API-specific error codes
                if 'response_code' in details_data:
                    if details_data['response_code'] == 15:
                        error_msg = "The project you specified does not exist"
                        logger.error(error_msg)
                        return {"error": error_msg}
                    elif details_data['response_code'] == 11:
                        error_msg = "The API token is invalid"
                        logger.error(error_msg)
                        return {"error": error_msg}
                    elif details_data['response_code'] != 0:
                        error_msg = f"{details_data.get('message', 'Unknown API error')} (Code: {details_data.get('response_code')})"
                        logger.error(f"Project details API error: {error_msg}")
                        return {"error": error_msg}
                
                # Combine project info and details
                result = {
                    'id': project_id,
                    'name': project_name,
                }
                
                # Add other project info fields
                if project_info:
                    for key, value in project_info.items():
                        if key not in result:
                            result[key] = value
                
                # Add details data
                result['details'] = details_data
                
                return result
                
            except ValueError as e:
                error_msg = f"Could not parse JSON from project details response: {str(e)}"
                logger.error(error_msg)
                logger.error(f"Raw response content: {details_response.text[:500]}")
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"Exception during project details request: {str(e)}"
            logger.error(error_msg)
            return {"error": str(e)}