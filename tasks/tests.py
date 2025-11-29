from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta
from .scoring import (
    calculate_priority_score, 
    detect_circular_dependencies, 
    get_score_explanation,
    analyze_tasks,
    calculate_urgency_score,
    calculate_importance_score,
    calculate_effort_score
)


class ScoringAlgorithmTests(TestCase):
    """Unit tests for the priority scoring algorithm"""
    
    def test_overdue_task_gets_highest_urgency(self):
        """Test that past-due tasks get high urgency scores"""
        task = {
            'id': 1,
            'title': 'Overdue task',
            'due_date': (date.today() - timedelta(days=5)).isoformat(),
            'estimated_hours': 2,
            'importance': 5,
            'dependencies': []
        }
        score = calculate_priority_score(task, [], strategy='smart_balance')
        # Past due tasks should have high scores
        self.assertGreater(score, 50)
    
    def test_urgency_score_future_due(self):
        """Test that far-future tasks get lower urgency scores"""
        task = {
            'id': 1,
            'title': 'Future task',
            'due_date': (date.today() + timedelta(days=30)).isoformat(),
            'estimated_hours': 2,
            'importance': 5,
            'dependencies': []
        }
        score = calculate_priority_score(task, [], strategy='smart_balance')
        # Far future tasks should have lower scores
        self.assertLess(score, 70)
    
    def test_importance_affects_score(self):
        """Test that higher importance leads to higher scores"""
        base_task = {
            'id': 1,
            'title': 'Test task',
            'due_date': (date.today() + timedelta(days=7)).isoformat(),
            'estimated_hours': 2,
            'dependencies': []
        }
        
        low_importance_task = {**base_task, 'importance': 2}
        high_importance_task = {**base_task, 'importance': 9}
        
        low_score = calculate_priority_score(low_importance_task, [], strategy='smart_balance')
        high_score = calculate_priority_score(high_importance_task, [], strategy='smart_balance')
        
        self.assertGreater(high_score, low_score)
    
    def test_quick_win_bonus(self):
        """Test that quick_wins strategy prioritizes low effort tasks"""
        base_task = {
            'id': 1,
            'title': 'Test task',
            'due_date': (date.today() + timedelta(days=7)).isoformat(),
            'importance': 5,
            'dependencies': []
        }
        
        low_effort_task = {**base_task, 'estimated_hours': 1}
        high_effort_task = {**base_task, 'estimated_hours': 20}
        
        low_effort_score = calculate_priority_score(low_effort_task, [], strategy='quick_wins')
        high_effort_score = calculate_priority_score(high_effort_task, [], strategy='quick_wins')
        
        self.assertGreater(low_effort_score, high_effort_score)
    
    def test_high_impact_strategy(self):
        """Test that high_impact strategy prioritizes importance"""
        base_task = {
            'id': 1,
            'title': 'Test task',
            'due_date': (date.today() + timedelta(days=7)).isoformat(),
            'estimated_hours': 5,
            'dependencies': []
        }
        
        low_importance_task = {**base_task, 'importance': 2}
        high_importance_task = {**base_task, 'importance': 10}
        
        low_score = calculate_priority_score(low_importance_task, [], strategy='high_impact')
        high_score = calculate_priority_score(high_importance_task, [], strategy='high_impact')
        
        # High impact should heavily favor importance
        self.assertGreater(high_score - low_score, 30)
    
    def test_deadline_driven_strategy(self):
        """Test that deadline_driven strategy prioritizes urgency"""
        base_task = {
            'id': 1,
            'title': 'Test task',
            'estimated_hours': 5,
            'importance': 5,
            'dependencies': []
        }
        
        urgent_task = {**base_task, 'due_date': (date.today() + timedelta(days=1)).isoformat()}
        not_urgent_task = {**base_task, 'due_date': (date.today() + timedelta(days=30)).isoformat()}
        
        urgent_score = calculate_priority_score(urgent_task, [], strategy='deadline_driven')
        not_urgent_score = calculate_priority_score(not_urgent_task, [], strategy='deadline_driven')
        
        self.assertGreater(urgent_score, not_urgent_score)
    
    def test_dependency_blocking_boost(self):
        """Test that tasks blocking others get higher scores"""
        blocking_task = {
            'id': 1,
            'title': 'Blocking task',
            'due_date': (date.today() + timedelta(days=7)).isoformat(),
            'estimated_hours': 2,
            'importance': 5,
            'dependencies': []
        }
        
        dependent_task = {
            'id': 2,
            'title': 'Dependent task',
            'due_date': (date.today() + timedelta(days=7)).isoformat(),
            'estimated_hours': 2,
            'importance': 5,
            'dependencies': [1]
        }
        
        non_blocking_task = {
            'id': 3,
            'title': 'Non-blocking task',
            'due_date': (date.today() + timedelta(days=7)).isoformat(),
            'estimated_hours': 2,
            'importance': 5,
            'dependencies': []
        }
        
        all_tasks = [blocking_task, dependent_task, non_blocking_task]
        
        blocking_score = calculate_priority_score(blocking_task, all_tasks, strategy='smart_balance')
        non_blocking_score = calculate_priority_score(non_blocking_task, all_tasks, strategy='smart_balance')
        
        # Blocking task should have higher score
        self.assertGreater(blocking_score, non_blocking_score)


class CircularDependencyTests(TestCase):
    """Unit tests for circular dependency detection"""
    
    def test_no_circular_dependencies(self):
        """Test detection when no circular dependencies exist"""
        tasks = [
            {'id': 1, 'dependencies': []},
            {'id': 2, 'dependencies': [1]},
            {'id': 3, 'dependencies': [2]},
        ]
        cycles = detect_circular_dependencies(tasks)
        self.assertEqual(len(cycles), 0)
    
    def test_simple_circular_dependency(self):
        """Test detection of simple A->B->A cycle"""
        tasks = [
            {'id': 1, 'dependencies': [2]},
            {'id': 2, 'dependencies': [1]},
        ]
        cycles = detect_circular_dependencies(tasks)
        self.assertGreater(len(cycles), 0)
    
    def test_complex_circular_dependency(self):
        """Test detection of A->B->C->A cycle"""
        tasks = [
            {'id': 1, 'dependencies': [3]},
            {'id': 2, 'dependencies': [1]},
            {'id': 3, 'dependencies': [2]},
        ]
        cycles = detect_circular_dependencies(tasks)
        self.assertGreater(len(cycles), 0)
    
    def test_self_dependency(self):
        """Test detection of task depending on itself"""
        tasks = [
            {'id': 1, 'dependencies': [1]},
        ]
        cycles = detect_circular_dependencies(tasks)
        self.assertGreater(len(cycles), 0)


class ScoreExplanationTests(TestCase):
    """Unit tests for score explanation generation"""
    
    def test_explanation_contains_components(self):
        """Test that explanation includes all scoring components"""
        task = {
            'id': 1,
            'title': 'Test task',
            'due_date': (date.today() + timedelta(days=3)).isoformat(),
            'estimated_hours': 2,
            'importance': 8,
            'dependencies': []
        }
        explanation = get_score_explanation(task, [], strategy='smart_balance')
        
        # Should mention key factors
        self.assertIn('Urgency', explanation)
        self.assertIn('Importance', explanation)
    
    def test_explanation_for_overdue_task(self):
        """Test that overdue tasks get appropriate explanation"""
        task = {
            'id': 1,
            'title': 'Overdue task',
            'due_date': (date.today() - timedelta(days=5)).isoformat(),
            'estimated_hours': 2,
            'importance': 5,
            'dependencies': []
        }
        explanation = get_score_explanation(task, [], strategy='smart_balance')
        
        # Should mention overdue status
        self.assertIn('OVERDUE', explanation)


class MissingDataHandlingTests(TestCase):
    """Unit tests for handling missing or invalid data"""
    
    def test_missing_due_date(self):
        """Test handling of task without due date"""
        task = {
            'id': 1,
            'title': 'No due date task',
            'estimated_hours': 2,
            'importance': 5,
            'dependencies': []
        }
        # Should not raise an exception
        try:
            score = calculate_priority_score(task, [], strategy='smart_balance')
            self.assertIsInstance(score, (int, float))
        except Exception as e:
            self.fail(f"Should handle missing due_date gracefully: {e}")
    
    def test_missing_importance(self):
        """Test handling of task without importance"""
        task = {
            'id': 1,
            'title': 'No importance task',
            'due_date': (date.today() + timedelta(days=7)).isoformat(),
            'estimated_hours': 2,
            'dependencies': []
        }
        try:
            score = calculate_priority_score(task, [], strategy='smart_balance')
            self.assertIsInstance(score, (int, float))
        except Exception as e:
            self.fail(f"Should handle missing importance gracefully: {e}")
    
    def test_missing_estimated_hours(self):
        """Test handling of task without estimated_hours"""
        task = {
            'id': 1,
            'title': 'No effort task',
            'due_date': (date.today() + timedelta(days=7)).isoformat(),
            'importance': 5,
            'dependencies': []
        }
        try:
            score = calculate_priority_score(task, [], strategy='smart_balance')
            self.assertIsInstance(score, (int, float))
        except Exception as e:
            self.fail(f"Should handle missing estimated_hours gracefully: {e}")
    
    def test_missing_all_optional_fields(self):
        """Test handling of task with only title"""
        task = {
            'id': 1,
            'title': 'Minimal task'
        }
        try:
            score = calculate_priority_score(task, [], strategy='smart_balance')
            self.assertIsInstance(score, (int, float))
            self.assertGreater(score, 0)
        except Exception as e:
            self.fail(f"Should handle minimal task gracefully: {e}")


class AnalyzeTasksTests(TestCase):
    """Unit tests for the analyze_tasks function"""
    
    def test_returns_sorted_tasks(self):
        """Test that analyze_tasks returns tasks sorted by priority"""
        tasks = [
            {
                'id': 1,
                'title': 'Low priority',
                'due_date': (date.today() + timedelta(days=30)).isoformat(),
                'importance': 2,
                'estimated_hours': 10,
                'dependencies': []
            },
            {
                'id': 2,
                'title': 'High priority',
                'due_date': (date.today() + timedelta(days=1)).isoformat(),
                'importance': 10,
                'estimated_hours': 1,
                'dependencies': []
            }
        ]
        
        result = analyze_tasks(tasks, strategy='smart_balance')
        
        self.assertIn('tasks', result)
        self.assertEqual(len(result['tasks']), 2)
        # High priority should be first
        self.assertEqual(result['tasks'][0]['id'], 2)
    
    def test_includes_priority_scores(self):
        """Test that analyze_tasks includes priority scores"""
        tasks = [
            {
                'id': 1,
                'title': 'Test task',
                'due_date': (date.today() + timedelta(days=7)).isoformat(),
                'importance': 5,
                'estimated_hours': 2,
                'dependencies': []
            }
        ]
        
        result = analyze_tasks(tasks)
        
        self.assertIn('priority_score', result['tasks'][0])
        self.assertIn('explanation', result['tasks'][0])
        self.assertIn('priority_level', result['tasks'][0])
    
    def test_detects_circular_dependencies(self):
        """Test that analyze_tasks detects circular dependencies"""
        tasks = [
            {'id': 1, 'title': 'Task A', 'dependencies': [2]},
            {'id': 2, 'title': 'Task B', 'dependencies': [1]}
        ]
        
        result = analyze_tasks(tasks)
        
        self.assertIn('circular_dependencies', result)
        self.assertGreater(len(result['circular_dependencies']), 0)
    
    def test_empty_task_list(self):
        """Test handling of empty task list"""
        result = analyze_tasks([])
        
        self.assertEqual(result['tasks'], [])
        self.assertEqual(result['total_tasks'], 0)


class UrgencyScoreTests(TestCase):
    """Detailed tests for urgency score calculation"""
    
    def test_due_today(self):
        """Test score for task due today"""
        task = {'due_date': date.today().isoformat()}
        score, explanation = calculate_urgency_score(task)
        self.assertEqual(score, 95.0)
        self.assertIn('TODAY', explanation)
    
    def test_overdue(self):
        """Test score for overdue task"""
        task = {'due_date': (date.today() - timedelta(days=3)).isoformat()}
        score, explanation = calculate_urgency_score(task)
        self.assertEqual(score, 100.0)
        self.assertIn('OVERDUE', explanation)
    
    def test_no_due_date(self):
        """Test score for task without due date"""
        task = {}
        score, explanation = calculate_urgency_score(task)
        self.assertEqual(score, 50.0)
        self.assertIn('neutral', explanation.lower())


class ImportanceScoreTests(TestCase):
    """Detailed tests for importance score calculation"""
    
    def test_max_importance(self):
        """Test score for maximum importance"""
        task = {'importance': 10}
        score, explanation = calculate_importance_score(task)
        self.assertEqual(score, 100.0)
        self.assertIn('Critical', explanation)
    
    def test_min_importance(self):
        """Test score for minimum importance"""
        task = {'importance': 1}
        score, explanation = calculate_importance_score(task)
        self.assertEqual(score, 10.0)
        self.assertIn('Low', explanation)
    
    def test_default_importance(self):
        """Test default importance when missing"""
        task = {}
        score, explanation = calculate_importance_score(task)
        self.assertEqual(score, 50.0)  # Default is 5 * 10


class EffortScoreTests(TestCase):
    """Detailed tests for effort score calculation"""
    
    def test_quick_task(self):
        """Test score for very quick task"""
        task = {'estimated_hours': 1}
        score, explanation = calculate_effort_score(task)
        self.assertEqual(score, 100.0)
        self.assertIn('Quick', explanation)
    
    def test_long_task(self):
        """Test score for long task"""
        task = {'estimated_hours': 20}
        score, explanation = calculate_effort_score(task)
        self.assertLess(score, 20)
        self.assertIn('Major', explanation)