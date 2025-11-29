"""
Task Priority Scoring Algorithm

This module implements a flexible priority scoring system that evaluates tasks
based on multiple factors: urgency, importance, effort, and dependencies.

The algorithm supports four different strategies:
- smart_balance: Balanced weighting of all factors (default)
- quick_wins: Prioritizes low-effort tasks for quick completion
- high_impact: Prioritizes task importance above all else
- deadline_driven: Prioritizes tasks with approaching deadlines
"""

from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple


# Strategy weight configurations
STRATEGY_WEIGHTS = {
    'smart_balance': {
        'urgency': 0.35,
        'importance': 0.30,
        'effort': 0.15,
        'dependencies': 0.20
    },
    'quick_wins': {
        'urgency': 0.15,
        'importance': 0.15,
        'effort': 0.55,
        'dependencies': 0.15
    },
    'high_impact': {
        'urgency': 0.15,
        'importance': 0.60,
        'effort': 0.10,
        'dependencies': 0.15
    },
    'deadline_driven': {
        'urgency': 0.60,
        'importance': 0.15,
        'effort': 0.10,
        'dependencies': 0.15
    }
}

# Default values for missing fields
DEFAULTS = {
    'importance': 5,
    'estimated_hours': 4,
    'dependencies': []
}


def parse_date(date_value: Any) -> Optional[date]:
    """
    Parse a date from various formats.
    
    Args:
        date_value: Can be a string (ISO format), date object, or datetime object
        
    Returns:
        date object or None if parsing fails
    """
    if date_value is None:
        return None
    
    if isinstance(date_value, date) and not isinstance(date_value, datetime):
        return date_value
    
    if isinstance(date_value, datetime):
        return date_value.date()
    
    if isinstance(date_value, str):
        try:
            return datetime.strptime(date_value, '%Y-%m-%d').date()
        except ValueError:
            try:
                return datetime.fromisoformat(date_value.replace('Z', '+00:00')).date()
            except ValueError:
                return None
    
    return None


def calculate_urgency_score(task: Dict[str, Any]) -> Tuple[float, str]:
    """
    Calculate urgency score based on due date proximity.
    
    Scoring logic:
    - Past due: 100 (maximum urgency)
    - Due today: 95
    - Due within 3 days: 80-94
    - Due within 7 days: 50-79
    - Due within 14 days: 30-49
    - Due later: 10-29
    - No due date: 50 (neutral urgency)
    
    Returns:
        Tuple of (score, explanation)
    """
    due_date = parse_date(task.get('due_date'))
    
    if due_date is None:
        return 50.0, "No due date set (neutral urgency)"
    
    today = date.today()
    days_until_due = (due_date - today).days
    
    if days_until_due < 0:
        # Overdue - maximum urgency
        overdue_days = abs(days_until_due)
        score = 100.0  # Max score for overdue
        return score, f"OVERDUE by {overdue_days} day(s)!"
    elif days_until_due == 0:
        return 95.0, "Due TODAY!"
    elif days_until_due <= 3:
        score = 94 - (days_until_due - 1) * 5
        return float(score), f"Due in {days_until_due} day(s) - High urgency"
    elif days_until_due <= 7:
        score = 79 - (days_until_due - 4) * 7
        return float(score), f"Due in {days_until_due} day(s) - Medium urgency"
    elif days_until_due <= 14:
        score = 49 - (days_until_due - 8) * 3
        return float(score), f"Due in {days_until_due} day(s) - Low urgency"
    else:
        score = max(10, 29 - (days_until_due - 15))
        return float(score), f"Due in {days_until_due} day(s) - Not urgent"


def calculate_importance_score(task: Dict[str, Any]) -> Tuple[float, str]:
    """
    Calculate importance score from user-provided rating.
    
    Converts 1-10 scale to 0-100 score.
    
    Returns:
        Tuple of (score, explanation)
    """
    importance = task.get('importance')
    
    if importance is None:
        importance = DEFAULTS['importance']
    
    # Validate and clamp importance to 1-10 range
    try:
        importance = float(importance)
        importance = max(1, min(10, importance))
    except (TypeError, ValueError):
        importance = DEFAULTS['importance']
    
    score = importance * 10
    
    if importance >= 8:
        level = "Critical"
    elif importance >= 6:
        level = "High"
    elif importance >= 4:
        level = "Medium"
    else:
        level = "Low"
    
    return float(score), f"Importance: {level} ({int(importance)}/10)"


def calculate_effort_score(task: Dict[str, Any]) -> Tuple[float, str]:
    """
    Calculate effort score - lower effort = higher score (quick wins).
    
    Scoring logic (inverted - less effort is better):
    - 1-2 hours: 90-100 (quick win)
    - 3-4 hours: 70-89 (half day)
    - 5-8 hours: 40-69 (full day)
    - 9-16 hours: 20-39 (multi-day)
    - 17+ hours: 10-19 (major effort)
    
    Returns:
        Tuple of (score, explanation)
    """
    hours = task.get('estimated_hours')
    
    if hours is None:
        hours = DEFAULTS['estimated_hours']
    
    # Validate and ensure positive hours
    try:
        hours = float(hours)
        hours = max(0.5, hours)  # Minimum 30 minutes
    except (TypeError, ValueError):
        hours = DEFAULTS['estimated_hours']
    
    if hours <= 1:
        score = 100.0
        category = "Quick task"
    elif hours <= 2:
        score = 90.0
        category = "Quick win"
    elif hours <= 4:
        score = 80 - (hours - 2) * 5
        category = "Half-day task"
    elif hours <= 8:
        score = 70 - (hours - 4) * 7.5
        category = "Full-day task"
    elif hours <= 16:
        score = 40 - (hours - 8) * 2.5
        category = "Multi-day task"
    else:
        score = max(10, 20 - (hours - 16) * 0.5)
        category = "Major effort"
    
    return float(score), f"{category} ({hours}h estimated)"


def calculate_dependency_score(task: Dict[str, Any], all_tasks: List[Dict[str, Any]]) -> Tuple[float, str]:
    """
    Calculate dependency score - tasks that block others should rank higher.
    
    Scoring logic:
    - Blocks 3+ tasks: 100
    - Blocks 2 tasks: 80
    - Blocks 1 task: 60
    - Blocks nothing: 40
    - Has unmet dependencies: 20 (deprioritize until dependencies are done)
    
    Returns:
        Tuple of (score, explanation)
    """
    task_id = task.get('id')
    task_dependencies = task.get('dependencies') or DEFAULTS['dependencies']
    
    if not isinstance(task_dependencies, list):
        task_dependencies = []
    
    # Count how many tasks depend on this one
    blocking_count = 0
    for other_task in all_tasks:
        other_deps = other_task.get('dependencies') or []
        if isinstance(other_deps, list) and task_id in other_deps:
            blocking_count += 1
    
    # Check if this task has unmet dependencies
    has_unmet_deps = len(task_dependencies) > 0
    
    if has_unmet_deps:
        # Task has dependencies - lower priority until those are done
        score = 20.0
        explanation = f"Blocked by {len(task_dependencies)} other task(s)"
    elif blocking_count >= 3:
        score = 100.0
        explanation = f"Blocks {blocking_count} tasks - Critical path!"
    elif blocking_count == 2:
        score = 80.0
        explanation = f"Blocks {blocking_count} tasks"
    elif blocking_count == 1:
        score = 60.0
        explanation = f"Blocks {blocking_count} task"
    else:
        score = 40.0
        explanation = "Independent task"
    
    return score, explanation


def calculate_priority_score(
    task: Dict[str, Any],
    all_tasks: List[Dict[str, Any]] = None,
    strategy: str = 'smart_balance'
) -> float:
    """
    Calculate the overall priority score for a task.
    
    Args:
        task: The task to score
        all_tasks: All tasks (needed for dependency analysis), defaults to empty list
        strategy: Scoring strategy to use
        
    Returns:
        Priority score (0-100, higher = more priority)
    """
    if all_tasks is None:
        all_tasks = []
    
    # Get weights for the selected strategy
    weights = STRATEGY_WEIGHTS.get(strategy, STRATEGY_WEIGHTS['smart_balance'])
    
    # Calculate component scores
    urgency_score, _ = calculate_urgency_score(task)
    importance_score, _ = calculate_importance_score(task)
    effort_score, _ = calculate_effort_score(task)
    dependency_score, _ = calculate_dependency_score(task, all_tasks)
    
    # Calculate weighted score
    total_score = (
        urgency_score * weights['urgency'] +
        importance_score * weights['importance'] +
        effort_score * weights['effort'] +
        dependency_score * weights['dependencies']
    )
    
    return round(total_score, 2)


def get_score_explanation(
    task: Dict[str, Any],
    all_tasks: List[Dict[str, Any]] = None,
    strategy: str = 'smart_balance'
) -> str:
    """
    Generate a human-readable explanation of the priority score.
    
    Args:
        task: The task to explain
        all_tasks: All tasks (needed for dependency analysis)
        strategy: Scoring strategy used
        
    Returns:
        Explanation string
    """
    if all_tasks is None:
        all_tasks = []
    
    weights = STRATEGY_WEIGHTS.get(strategy, STRATEGY_WEIGHTS['smart_balance'])
    
    urgency_score, urgency_exp = calculate_urgency_score(task)
    importance_score, importance_exp = calculate_importance_score(task)
    effort_score, effort_exp = calculate_effort_score(task)
    dependency_score, dependency_exp = calculate_dependency_score(task, all_tasks)
    
    # Build explanation with weighted contributions
    parts = []
    
    # Sort by weight to show most important factors first
    factors = [
        ('Urgency', urgency_score, urgency_exp, weights['urgency']),
        ('Importance', importance_score, importance_exp, weights['importance']),
        ('Effort', effort_score, effort_exp, weights['effort']),
        ('Dependencies', dependency_score, dependency_exp, weights['dependencies'])
    ]
    factors.sort(key=lambda x: x[3], reverse=True)
    
    for name, score, exp, weight in factors:
        contribution = round(score * weight, 1)
        parts.append(f"{name}: {exp} (+{contribution})")
    
    return " | ".join(parts)


def detect_circular_dependencies(tasks: List[Dict[str, Any]]) -> List[List[int]]:
    """
    Detect circular dependencies in a list of tasks.
    
    Uses depth-first search to find cycles in the dependency graph.
    
    Args:
        tasks: List of tasks with 'id' and 'dependencies' fields
        
    Returns:
        List of cycles found, where each cycle is a list of task IDs
    """
    # Build adjacency list
    graph = {}
    for task in tasks:
        task_id = task.get('id')
        deps = task.get('dependencies') or []
        if not isinstance(deps, list):
            deps = []
        graph[task_id] = deps
    
    cycles = []
    visited = set()
    rec_stack = set()
    
    def dfs(node: int, path: List[int]) -> None:
        """DFS helper to find cycles"""
        if node in rec_stack:
            # Found a cycle - extract it from the path
            if node in path:
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
            return
        
        if node in visited:
            return
        
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor in graph:  # Only follow valid task IDs
                dfs(neighbor, path.copy())
        
        rec_stack.remove(node)
    
    # Run DFS from each node
    for task_id in graph:
        if task_id not in visited:
            dfs(task_id, [])
    
    return cycles


def analyze_tasks(
    tasks: List[Dict[str, Any]],
    strategy: str = 'smart_balance'
) -> Dict[str, Any]:
    """
    Analyze a list of tasks and return them sorted by priority.
    
    Args:
        tasks: List of task dictionaries
        strategy: Scoring strategy to use
        
    Returns:
        Dictionary with sorted tasks, circular dependencies, and metadata
    """
    # Validate strategy
    if strategy not in STRATEGY_WEIGHTS:
        strategy = 'smart_balance'
    
    # Detect circular dependencies
    circular_deps = detect_circular_dependencies(tasks)
    
    # Calculate scores and add to tasks
    scored_tasks = []
    for task in tasks:
        task_copy = task.copy()
        task_copy['priority_score'] = calculate_priority_score(task, tasks, strategy)
        task_copy['explanation'] = get_score_explanation(task, tasks, strategy)
        
        # Determine priority level
        score = task_copy['priority_score']
        if score >= 70:
            task_copy['priority_level'] = 'high'
        elif score >= 40:
            task_copy['priority_level'] = 'medium'
        else:
            task_copy['priority_level'] = 'low'
        
        scored_tasks.append(task_copy)
    
    # Sort by priority score (descending)
    scored_tasks.sort(key=lambda x: x['priority_score'], reverse=True)
    
    return {
        'tasks': scored_tasks,
        'circular_dependencies': circular_deps,
        'strategy_used': strategy,
        'total_tasks': len(tasks)
    }


def get_suggestions(
    tasks: List[Dict[str, Any]],
    strategy: str = 'smart_balance',
    count: int = 3
) -> List[Dict[str, Any]]:
    """
    Get top N task suggestions with detailed explanations.
    
    Args:
        tasks: List of task dictionaries
        strategy: Scoring strategy to use
        count: Number of suggestions to return
        
    Returns:
        List of top N tasks with suggestions
    """
    analysis = analyze_tasks(tasks, strategy)
    top_tasks = analysis['tasks'][:count]
    
    suggestions = []
    for i, task in enumerate(top_tasks, 1):
        suggestion = {
            'rank': i,
            'task': task,
            'reason': generate_suggestion_reason(task, i)
        }
        suggestions.append(suggestion)
    
    return suggestions


def generate_suggestion_reason(task: Dict[str, Any], rank: int) -> str:
    """
    Generate a human-friendly reason for why a task is suggested.
    
    Args:
        task: The task dictionary (with priority_score and explanation)
        rank: The rank of this task (1, 2, or 3)
        
    Returns:
        Human-readable suggestion reason
    """
    score = task.get('priority_score', 0)
    explanation = task.get('explanation', '')
    
    # Parse due date for context
    due_date = parse_date(task.get('due_date'))
    today = date.today()
    
    reasons = []
    
    if due_date:
        days_until = (due_date - today).days
        if days_until < 0:
            reasons.append(f"overdue by {abs(days_until)} day(s)")
        elif days_until == 0:
            reasons.append("due today")
        elif days_until <= 3:
            reasons.append(f"due in {days_until} day(s)")
    
    importance = task.get('importance', 5)
    if importance >= 8:
        reasons.append("marked as highly important")
    
    hours = task.get('estimated_hours', 4)
    if hours <= 2:
        reasons.append("a quick win you can complete fast")
    
    # Check if it blocks other tasks
    if 'Blocks' in explanation:
        reasons.append("blocking other tasks from starting")
    
    if reasons:
        reason_text = ", ".join(reasons)
        return f"#{rank} Priority (Score: {score}): {reason_text.capitalize()}."
    else:
        return f"#{rank} Priority (Score: {score}): Good balance of urgency, importance, and effort."