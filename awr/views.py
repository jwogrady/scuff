from django.shortcuts import render
from django.http import JsonResponse
from .utils import AWRClient
import logging

logger = logging.getLogger(__name__)

def projects_list(request):
    """
    Display list of AWR projects
    
    This view fetches projects from the AWR API and renders them in a table,
    with proper error handling.
    """
    client = AWRClient()
    projects_data = client.get_projects()
    
    # Log full API response for debugging
    logger.debug(f"Projects data type: {type(projects_data)}")
    logger.debug(f"Projects data keys: {projects_data.keys() if isinstance(projects_data, dict) else 'Not a dict'}")
    
    # For API view, just return the JSON response
    if request.headers.get('Content-Type') == 'application/json':
        return JsonResponse(projects_data)
    
    # Initialize context
    context = {'raw_response': projects_data}
    
    # Check if there's an explicit error in the response
    if isinstance(projects_data, dict) and 'error' in projects_data:
        context['error'] = projects_data['error']
        context['projects'] = {'projects': []}
    
    # Handle successful response with projects
    elif isinstance(projects_data, dict) and 'projects' in projects_data:
        context['projects'] = projects_data
        
        # Display success message if projects were found
        if projects_data.get('projects') and len(projects_data['projects']) > 0:
            context['success_message'] = f"Successfully retrieved {len(projects_data['projects'])} projects."
        else:
            # No error but also no projects
            context['info_message'] = "No projects found in your AWR account. The API connection was successful, but there are no projects to display."
    
    # If the response is valid but doesn't match expected structure
    else:
        context['projects'] = {'projects': []}
        context['error'] = "Unexpected API response format. See debug information for details."
        context['debug_info'] = str(projects_data)[:500]
    
    # For HTML view, render a template
    return render(request, 'awr/projects_list.html', context)

def project_detail(request, project_id):
    """Display details for a specific AWR project"""
    client = AWRClient()
    project_data = client.get_project_details(project_id)
    
    logger.debug(f"Project detail data type: {type(project_data)}")
    if isinstance(project_data, dict):
        logger.debug(f"Project detail keys: {project_data.keys()}")
    
    context = {
        'project_id': project_id,
        'raw_response': project_data
    }
    
    # Check if there's an error in the response
    if 'error' in project_data:
        context['error'] = project_data['error']
    else:
        # We have project data
        context['project'] = project_data
        
        # Extract sections from details if they exist
        if 'details' in project_data:
            details = project_data['details']
            for section in ['websites', 'keywords', 'searchengines', 'locations']:
                if section in details:
                    context[section] = details[section]
        
        context['success_message'] = "Project details retrieved successfully."
    
    return render(request, 'awr/project_detail.html', context)

def api_diagnostic(request):
    """Diagnostic endpoint for AWR API troubleshooting"""
    from django.http import JsonResponse
    import os
    import requests
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Get environment variables
    api_key = os.getenv('AWR_API_KEY')
    api_url = os.getenv('AWR_API_URL_V2')
    
    results = {
        'env_vars': {
            'api_key_exists': bool(api_key),
            'api_key_length': len(api_key) if api_key else 0,
            'api_url': api_url
        },
        'api_test': {}
    }
    
    # Test API connection
    params = {
        'action': 'projects',
        'key': api_key,
        'format': 'json'
    }
    
    try:
        response = requests.get(api_url, params=params)
        
        results['api_test'] = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content_type': response.headers.get('Content-Type'),
            'response_length': len(response.text),
            'response_preview': response.text[:100] + '...' if len(response.text) > 100 else response.text
        }
        
        if response.headers.get('Content-Type', '').startswith('application/json'):
            try:
                json_data = response.json()
                results['api_test']['json_data'] = json_data
            except:
                results['api_test']['json_error'] = "Could not parse JSON response"
    except Exception as e:
        results['api_test']['error'] = str(e)
    
    # Check firewall/connectivity
    try:
        import socket
        hostname = api_url.split('//')[1].split('/')[0]
        socket_test = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_test.settimeout(5)
        result = socket_test.connect_ex((hostname, 443))
        socket_test.close()
        results['connectivity'] = {
            'hostname': hostname,
            'port_443_open': (result == 0)
        }
    except Exception as e:
        results['connectivity'] = {'error': str(e)}
        
    return JsonResponse(results)
