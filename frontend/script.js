// API Configuration - Change this URL after deploying your backend
const API_URL = 'https://task-analyzer-j76s.onrender.com';

// State to hold tasks before and after analysis
let stagingTasks = [];
let analyzedTasks = [];

// DOM Elements
const taskForm = document.getElementById('task-form');
const stagingList = document.getElementById('staging-list');
const resultsList = document.getElementById('results-list');
const countSpan = document.getElementById('count');
const sortSelect = document.getElementById('sort-strategy');

// 1. Handle Manual Form Submission
taskForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const newTask = {
        title: document.getElementById('title').value,
        due_date: document.getElementById('due_date').value,
        estimated_hours: parseFloat(document.getElementById('hours').value),
        importance: parseInt(document.getElementById('importance').value),
        dependencies: [] // Simplified for UI
    };

    stagingTasks.push(newTask);
    updateStagingArea();
    taskForm.reset();
});

// 2. Update Staging Area UI
function updateStagingArea() {
    stagingList.innerHTML = '';
    countSpan.textContent = stagingTasks.length;
    
    stagingTasks.forEach((task, index) => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span>${task.title}</span>
            <small>${task.due_date} | Imp: ${task.importance}</small>
        `;
        stagingList.appendChild(li);
    });
}

// 3. Handle "Analyze Tasks" (API Call)
document.getElementById('analyze-btn').addEventListener('click', async () => {
    if (stagingTasks.length === 0) {
        alert("Please add at least one task!");
        return;
    }

    resultsList.innerHTML = '<div class="loading">Analyzing...</div>';

    try {
        // Get selected strategy from dropdown
        const strategy = sortSelect.value;
        const strategyMap = {
            'smart': 'smart_balance',
            'deadline': 'deadline_driven',
            'impact': 'high_impact',
            'fastest': 'quick_wins'
        };
        
        const response = await fetch(`${API_URL}/api/tasks/analyze/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tasks: stagingTasks,
                strategy: strategyMap[strategy] || 'smart_balance'
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'API Error');
        }

        const result = await response.json();
        analyzedTasks = result.tasks || result; // Handle both formats
        
        // Show circular dependency warning if detected
        if (result.circular_dependencies && result.circular_dependencies.length > 0) {
            alert(`Warning: Circular dependencies detected! ${result.circular_dependencies.length} cycle(s) found.`);
        }
        
        renderResults(); // Render with backend sorting
        
    } catch (error) {
        resultsList.innerHTML = `<div class="error">Error: ${error.message}. Is Backend running?</div>`;
    }
});

// 4. Handle Sorting Strategies - Re-analyze with new strategy
sortSelect.addEventListener('change', async () => {
    if (stagingTasks.length === 0 && analyzedTasks.length === 0) {
        return;
    }
    
    // If we have staging tasks, re-analyze with new strategy
    if (stagingTasks.length > 0) {
        resultsList.innerHTML = '<div class="loading">Re-analyzing with new strategy...</div>';
        
        try {
            const strategy = sortSelect.value;
            const strategyMap = {
                'smart': 'smart_balance',
                'deadline': 'deadline_driven',
                'impact': 'high_impact',
                'fastest': 'quick_wins'
            };
            
            const response = await fetch(`${API_URL}/api/tasks/analyze/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    tasks: stagingTasks,
                    strategy: strategyMap[strategy] || 'smart_balance'
                })
            });

            if (!response.ok) throw new Error('API Error');

            const result = await response.json();
            analyzedTasks = result.tasks || result;
            renderResults();
            
        } catch (error) {
            resultsList.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        }
    } else {
        // Just re-render with client-side sorting
        renderResults();
    }
});

function renderResults() {
    const strategy = sortSelect.value;
    let tasksToShow = [...analyzedTasks];

    // Client-side sorting as fallback
    if (strategy === 'smart') {
        tasksToShow.sort((a, b) => b.priority_score - a.priority_score);
    } else if (strategy === 'deadline') {
        tasksToShow.sort((a, b) => new Date(a.due_date) - new Date(b.due_date));
    } else if (strategy === 'impact') {
        tasksToShow.sort((a, b) => b.importance - a.importance);
    } else if (strategy === 'fastest') {
        tasksToShow.sort((a, b) => a.estimated_hours - b.estimated_hours);
    }

    // Render HTML
    resultsList.innerHTML = '';
    
    if (tasksToShow.length === 0) {
        resultsList.innerHTML = '<div class="loading">No tasks to display</div>';
        return;
    }
    
    tasksToShow.forEach(task => {
        const score = Math.round(task.priority_score);
        const priorityLevel = task.priority_level || (score >= 70 ? 'high' : score >= 40 ? 'medium' : 'low');
        let colorClass = 'priority-low';
        if (priorityLevel === 'high' || score >= 70) colorClass = 'priority-high';
        else if (priorityLevel === 'medium' || score >= 40) colorClass = 'priority-med';

        const card = document.createElement('div');
        card.className = 'task-card';
        card.innerHTML = `
            <div class="score-badge ${colorClass}">${score}</div>
            <div class="task-info">
                <h3>${task.title}</h3>
                <div class="task-meta">
                    Due: ${task.due_date || 'No date'} | ${task.estimated_hours} hrs | Imp: ${task.importance}/10
                </div>
                <div class="rationale">
                    ${task.explanation || getRationale(task, strategy)}
                </div>
            </div>
        `;
        resultsList.appendChild(card);
    });
}

// Helper to explain WHY a task is ranked (UX requirement)
function getRationale(task, strategy) {
    if (strategy === 'deadline') return `Due in ${daysUntil(task.due_date)} days`;
    if (strategy === 'impact') return `Rated importance ${task.importance}/10`;
    if (strategy === 'fastest') return `Only takes ${task.estimated_hours} hours`;
    return `Smart Score: ${task.priority_score.toFixed(1)}`;
}

function daysUntil(dateStr) {
    const diff = new Date(dateStr) - new Date();
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

// Utility: Tab Switching
window.showInput = function(type) {
    document.querySelectorAll('.input-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    
    if (type === 'form') {
        document.getElementById('form-input').classList.remove('hidden');
        document.querySelector('button[onclick="showInput(\'form\')"]').classList.add('active');
    } else {
        document.getElementById('json-input').classList.remove('hidden');
        document.querySelector('button[onclick="showInput(\'json\')"]').classList.add('active');
    }
};

// Handle JSON Paste
document.getElementById('load-json-btn').addEventListener('click', () => {
    try {
        const raw = document.getElementById('json-text').value;
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
            stagingTasks = [...stagingTasks, ...parsed];
            updateStagingArea();
            alert("JSON Loaded!");
        }
    } catch (e) {
        alert("Invalid JSON format");
    }
});