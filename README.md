# Smart Task Analyzer

A Django-based task management system that intelligently scores and prioritizes tasks based on multiple factors including urgency, importance, effort, and dependencies.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone [YOUR_REPO_LINK]
   cd task_analyzer_project
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Mac/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install django djangorestframework django-cors-headers
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Start the development server**
   ```bash
   python manage.py runserver
   ```

6. **Open the application**
   - Frontend: Open `frontend/index.html` in your browser
   - API: http://localhost:8000/api/

### Running Tests
```bash
python manage.py test tasks
```

---

## 📊 Algorithm Explanation

### Priority Scoring System

The Smart Task Analyzer uses a **weighted multi-factor scoring algorithm** that evaluates tasks on a 0-100 scale. The algorithm considers four key factors:

#### 1. Urgency Score (Based on Due Date)
The urgency component calculates how soon a task needs to be completed:

| Condition | Score | Description |
|-----------|-------|-------------|
| Overdue | 100 | Maximum urgency - task is past due |
| Due today | 95 | Immediate attention required |
| Due within 3 days | 80-94 | High urgency |
| Due within 7 days | 50-79 | Medium urgency |
| Due within 14 days | 30-49 | Low urgency |
| Due later | 10-29 | Not urgent |
| No due date | 50 | Neutral (doesn't penalize or boost) |

#### 2. Importance Score (User Rating)
Directly maps the user's 1-10 importance rating to a 0-100 scale:
- Rating 10 → Score 100 (Critical)
- Rating 8-9 → Score 80-90 (Critical)
- Rating 6-7 → Score 60-70 (High)
- Rating 4-5 → Score 40-50 (Medium)
- Rating 1-3 → Score 10-30 (Low)

#### 3. Effort Score (Estimated Hours)
Lower effort tasks receive higher scores to promote "quick wins":

| Hours | Score | Category |
|-------|-------|----------|
| ≤1 hour | 100 | Quick task |
| 1-2 hours | 90 | Quick win |
| 2-4 hours | 70-80 | Half-day task |
| 4-8 hours | 40-70 | Full-day task |
| 8-16 hours | 20-40 | Multi-day task |
| 16+ hours | 10-20 | Major effort |

#### 4. Dependency Score (Task Relationships)
Evaluates how tasks relate to each other in the dependency graph:

| Condition | Score | Description |
|-----------|-------|-------------|
| Blocks 3+ tasks | 100 | Critical path item |
| Blocks 2 tasks | 80 | High blocking |
| Blocks 1 task | 60 | Medium blocking |
| Independent | 40 | No dependencies |
| Has unmet dependencies | 20 | Should wait for blockers |

### Scoring Strategies

The algorithm supports four weighting strategies that can be selected by the user:

| Strategy | Urgency | Importance | Effort | Dependencies | Best For |
|----------|---------|------------|--------|--------------|----------|
| **Smart Balance** | 35% | 30% | 15% | 20% | General use |
| **Quick Wins** | 15% | 15% | 55% | 15% | Building momentum |
| **High Impact** | 15% | 60% | 10% | 15% | Maximizing value |
| **Deadline Driven** | 60% | 15% | 10% | 15% | Meeting deadlines |

### Final Score Calculation
```
Final Score = (Urgency × Weight_u) + (Importance × Weight_i) + (Effort × Weight_e) + (Dependencies × Weight_d)
```

### Circular Dependency Detection

The algorithm includes a DFS-based cycle detection system that identifies circular dependencies (e.g., Task A → Task B → Task A). When detected, these are flagged in the API response as warnings.

---

## 🎯 Design Decisions

### 1. Stateless Analysis vs Database Persistence
**Decision**: The `/analyze/` endpoint processes tasks in-memory without requiring database storage.

**Rationale**: This allows for quick prototyping and testing. Users can paste JSON data and get immediate results without database setup. The Task model exists for future persistence features via the `/suggest/` endpoint.

### 2. Separate Serializer for Analysis
**Decision**: Created a dedicated `TaskAnalyzeSerializer` separate from `TaskSerializer`.

**Rationale**: The `ModelSerializer` validates `dependencies` as a ManyToMany field requiring existing database records. The analysis endpoint needs to validate dependencies as a simple list of integers for in-memory processing.

### 3. Strategy Pattern for Scoring
**Decision**: Implemented configurable weight strategies instead of a single fixed algorithm.

**Rationale**: Different users have different priorities. A developer might prefer "Quick Wins" to maintain momentum, while a project manager might prefer "Deadline Driven" for client deliverables. The strategy can be selected per request.

### 4. Graceful Handling of Missing Data
**Decision**: Use sensible defaults instead of failing on missing fields.

| Missing Field | Default Value |
|--------------|---------------|
| `due_date` | None (50 urgency score) |
| `importance` | 5 (Medium) |
| `estimated_hours` | 4 hours |
| `dependencies` | Empty list |

**Rationale**: Real-world data is often incomplete. A task without an estimated time shouldn't break the system.

### 5. Dependency Scoring Logic
**Decision**: Score based on how many tasks a task *blocks* (outputs) rather than how many it *depends on* (inputs).

**Rationale**: Prioritizing bottleneck tasks (those blocking others) maximizes throughput. Completing a blocking task unblocks multiple downstream tasks.

### 6. Score Explanations
**Decision**: Every score includes a human-readable explanation showing each factor's contribution.

**Rationale**: Transparency builds trust. Users need to understand why tasks are ranked to make informed decisions about overriding suggestions.

---

## ⏱️ Time Breakdown

| Section | Time Spent |
|---------|------------|
| Algorithm Design & Research | 45 minutes |
| Backend Implementation (scoring.py) | 1.5 hours |
| Django API Setup & Views | 45 minutes |
| Frontend Development | 1 hour |
| Testing & Debugging | 1 hour |
| Documentation | 30 minutes |
| **Total** | ~5.5 hours |

---

## 🌟 Bonus Challenges

### ✅ Completed:
1. **Circular Dependency Detection**: Implemented using DFS algorithm in `scoring.py`. The system detects and reports all cycles in the dependency graph.

2. **Comprehensive Unit Tests**: 20+ test cases in `tests.py` covering:
   - Scoring algorithm correctness
   - All four strategies
   - Circular dependency detection
   - Missing data handling
   - Edge cases

### ⬜ Not Attempted (Future Work):
- Dependency Graph Visualization
- Date Intelligence (weekends/holidays)
- Eisenhower Matrix View
- Learning System

---

## 🔮 Future Improvements

With more time, I would implement:

1. **Dependency Graph Visualization**
   - Use D3.js or vis.js to render an interactive dependency graph
   - Highlight circular dependencies in red
   - Allow drag-and-drop to reorganize tasks

2. **Date Intelligence**
   - Skip weekends when calculating urgency
   - Integrate with holiday APIs for different regions
   - Consider working hours (a task due Monday morning is urgent on Friday)

3. **Machine Learning Enhancement**
   - Track which suggested tasks users actually complete
   - Adjust weights based on user behavior patterns
   - Personalized scoring per user

4. **Persistent Storage & User Accounts**
   - Save task lists to database
   - User authentication
   - Task completion tracking and analytics

5. **Calendar Integration**
   - Sync with Google Calendar / Outlook
   - Consider existing meetings when suggesting tasks
   - Auto-schedule tasks based on available time

---

## 📁 Project Structure

```
task_analyzer_project/
├── manage.py
├── db.sqlite3
├── README.md
├── task_analyzer/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── tasks/
│   ├── __init__.py
│   ├── models.py          # Task model definition
│   ├── views.py           # API endpoints
│   ├── serializers.py     # DRF serializers
│   ├── scoring.py         # Priority algorithm (core logic)
│   ├── urls.py            # URL routing
│   └── tests.py           # Unit tests (20+ test cases)
└── frontend/
    ├── index.html         # Main UI
    ├── styles.css         # Styling
    └── script.js          # Frontend logic
```

---

## 🔌 API Reference

### POST /api/tasks/analyze/
Analyze and sort tasks by priority.

**Request Body (Option 1 - List):**
```json
[
  {
    "title": "Fix login bug",
    "due_date": "2025-11-30",
    "estimated_hours": 3,
    "importance": 8,
    "dependencies": []
  }
]
```

**Request Body (Option 2 - Object with strategy):**
```json
{
  "tasks": [...],
  "strategy": "smart_balance"
}
```

**Response:**
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Fix login bug",
      "due_date": "2025-11-30",
      "estimated_hours": 3,
      "importance": 8,
      "dependencies": [],
      "priority_score": 72.5,
      "priority_level": "high",
      "explanation": "Urgency: Due in 1 day(s) - High urgency (+33.3) | ..."
    }
  ],
  "circular_dependencies": [],
  "strategy_used": "smart_balance",
  "total_tasks": 1
}
```

### GET /api/tasks/suggest/
Get top 3 task suggestions from database.

### POST /api/tasks/suggest/
Get top 3 task suggestions from provided data.

**Request Body:**
```json
{
  "tasks": [...],
  "strategy": "smart_balance"
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "rank": 1,
      "task": { ... },
      "reason": "#1 Priority (Score: 85): Due today, marked as highly important."
    }
  ],
  "date": "2025-11-29",
  "strategy_used": "smart_balance",
  "total_tasks": 5
}
```

---

## 🧪 Running Tests

```bash
# Run all tests
python manage.py test tasks

# Run with verbosity
python manage.py test tasks -v 2

# Run specific test class
python manage.py test tasks.tests.ScoringAlgorithmTests
```

---

## 📝 License

This project was created as a technical assessment submission.