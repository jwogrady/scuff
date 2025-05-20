import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AWRClient:
    def __init__(self):
        self.api_key = os.getenv('awr-api-key')
        self.api_url_v2 = os.getenv('awr-api-url-v2').split('#')[0].strip()
        self.api_limit = int(os.getenv('awr-api-limit', 2000))
    
    def get_projects(self):
        """
        Get all projects from AWR API
        https://app.advancedwebranking.com/docs/developer-api-v2.html#get-projects-v2
        """
        params = {
            'action': 'projects',
            'key': self.api_key,
        }
        
        response = requests.get(self.api_url_v2, params=params)
        return response.json()
    
    def get_project_details(self, project_id):
        """
        Get details for a specific project
        https://app.advancedwebranking.com/docs/developer-api-v2.html#get-project-details-v2
        """
        params = {
            'action': 'project-details',
            'key': self.api_key,
            'project_id': project_id,
        }
        
        response = requests.get(self.api_url_v2, params=params)
        return response.json()