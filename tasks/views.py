from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Task
from .serializers import TaskSerializer, TaskAnalyzeSerializer
from .scoring import (
    calculate_priority_score, 
    analyze_tasks, 
    get_suggestions, 
    detect_circular_dependencies,
    get_score_explanation
)
from datetime import date
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
def analyze_tasks_view(request):
    """
    POST /api/tasks/analyze/
    
    Accepts a list of tasks and returns them sorted by priority score.
    Each task includes its calculated score and explanation.
    
    Request body can be:
    - A list of tasks directly: [{"title": "...", ...}, ...]
    - An object with tasks: {"tasks": [...], "strategy": "smart_balance"}
    """
    logger.debug(f"Received analyze request: {request.data}")
    
    # Handle both formats: list of tasks or object with 'tasks' key
    if isinstance(request.data, list):
        tasks = request.data
        strategy = 'smart_balance'
    else:
        tasks = request.data.get('tasks', request.data)
        strategy = request.data.get('strategy', 'smart_balance')
        
        # If it's still not a list, treat the whole thing as a single task
        if isinstance(tasks, dict) and 'title' in tasks:
            tasks = [tasks]
    
    # Validate tasks is a list
    if not isinstance(tasks, list):
        return Response(
            {'error': 'Tasks must be a list', 'message': 'Invalid task data'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate each task with serializer
    serializer = TaskAnalyzeSerializer(data=tasks, many=True)
    if not serializer.is_valid():
        logger.error(f"Validation errors: {serializer.errors}")
        return Response(
            {"errors": serializer.errors, "message": "Invalid task data"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Add IDs to tasks if missing
    validated_tasks = []
    for i, task in enumerate(serializer.validated_data):
        task_dict = dict(task)
        if 'id' not in task_dict or task_dict['id'] is None:
            task_dict['id'] = i + 1
        validated_tasks.append(task_dict)
    
    # Analyze tasks using the scoring module
    try:
        result = analyze_tasks(validated_tasks, strategy)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error analyzing tasks: {e}")
        return Response(
            {'error': f'Analysis failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'POST'])
def suggest_tasks(request):
    """
    GET /api/tasks/suggest/ - Return the top 3 tasks from the database
    POST /api/tasks/suggest/ - Return the top 3 tasks from provided data
    
    Returns the top 3 tasks the user should work on today,
    with explanations for why each was chosen.
    """
    logger.debug(f"Received suggest request: {request.method}")
    
    if request.method == 'POST':
        # Handle POST with task data
        if isinstance(request.data, list):
            tasks = request.data
            strategy = 'smart_balance'
        else:
            tasks = request.data.get('tasks', [])
            strategy = request.data.get('strategy', 'smart_balance')
        
        if not isinstance(tasks, list):
            return Response(
                {'error': 'Tasks must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add IDs if missing
        for i, task in enumerate(tasks):
            if 'id' not in task:
                task['id'] = i + 1
        
        try:
            suggestions = get_suggestions(tasks, strategy, count=3)
            circular_deps = detect_circular_dependencies(tasks)
            
            response_data = {
                'suggestions': suggestions,
                'date': date.today().isoformat(),
                'strategy_used': strategy,
                'total_tasks': len(tasks)
            }
            
            if circular_deps:
                response_data['warnings'] = {
                    'circular_dependencies': circular_deps,
                    'message': 'Circular dependencies detected! Some tasks may be impossible to complete in order.'
                }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return Response(
                {'error': f'Suggestion generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    else:
        # Handle GET - fetch from database
        db_tasks = Task.objects.all()
        
        if not db_tasks.exists():
            return Response({
                'suggestions': [],
                'date': date.today().isoformat(),
                'message': 'No tasks in database. Use POST to analyze tasks or add tasks to the database.'
            })
        
        # Convert DB tasks to dict format
        tasks = []
        for task in db_tasks:
            task_dict = {
                'id': task.id,
                'title': task.title,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'estimated_hours': task.estimated_hours,
                'importance': task.importance,
                'dependencies': list(task.dependencies.values_list('id', flat=True))
            }
            tasks.append(task_dict)
        
        # Get suggestions
        suggestions = get_suggestions(tasks, 'smart_balance', count=3)
        
        # Add blocking count info
        for suggestion in suggestions:
            task_id = suggestion['task']['id']
            db_task = Task.objects.get(id=task_id)
            blocking_count = db_task.required_by.count()
            if blocking_count > 0:
                suggestion['reason'] += f" Blocks {blocking_count} other task(s)."
        
        return Response({
            'suggestions': suggestions,
            'date': date.today().isoformat(),
            'total_tasks': len(tasks)
        })