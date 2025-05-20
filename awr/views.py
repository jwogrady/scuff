from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .utils import AWRClient
from .models import Project

def projects_list(request):
    """Display list of AWR projects"""
    client = AWRClient()
    projects_data = client.get_projects()
    
    # For API view, just return the JSON response
    if request.headers.get('Content-Type') == 'application/json':
        return JsonResponse(projects_data)
    
    # For HTML view, render a template
    return render(request, 'awr/projects_list.html', {'projects': projects_data})

def project_detail(request, project_id):
    """Display details of a specific AWR project"""
    client = AWRClient()
    project_data = client.get_project_details(project_id)
    
    # For API view, just return the JSON response
    if request.headers.get('Content-Type') == 'application/json':
        return JsonResponse(project_data)
    
    # For HTML view, render a template
    return render(request, 'awr/project_detail.html', {'project': project_data})
