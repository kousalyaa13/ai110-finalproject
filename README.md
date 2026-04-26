# PawPal+

## Overview

PawPal+ is an AI-powered pet care scheduling assistant that helps busy pet owners create optimized daily care plans. Originally developed as a capstone project for an applied AI systems course (Modules 1-3), this system takes pet care tasks, owner time constraints, and task priorities to generate conflict-free schedules with human-readable explanations.

The original project focused on building a robust scheduling algorithm that could handle real-world pet care scenarios, including recurring tasks (daily/weekly), priority-based ordering, and conflict detection across multiple pets.

## What PawPal+ Does

PawPal+ solves the challenge of inconsistent pet care by providing:
- **Intelligent scheduling** that fits tasks within available time while respecting priorities
- **Recurring task management** for daily routines like feeding and walks
- **Conflict detection** to prevent overlapping care activities
- **Clear explanations** of why tasks were scheduled or skipped
- **Multi-pet support** for owners with multiple animals

The system prioritizes pet health needs (feeding, medication) while fitting in enrichment activities (walks, playtime) within the owner's time budget.

## Data Persistence Layer

PawPal+ now includes full JSON-based data persistence, ensuring that pet information, tasks, and schedules survive between application runs.

**Features:**
- **Automatic Save/Load**: Data persists between web app sessions and CLI runs
- **JSON Format**: Human-readable data storage with proper error handling
- **State Preservation**: Task completion status, start times, and recurrence cycles are maintained
- **Multi-File Orchestration**: Seamlessly integrates logic layer persistence with UI state management

**Web App Persistence:**
- Loads previous session data on startup
- Automatically saves when tasks are added, owner info changes, or schedules are built
- Shows confirmation messages when data is saved

**CLI Persistence:**
- Demonstrates loading from saved web app sessions
- Saves demo data for future runs
- Shows file size and persistence status

## Architecture Overview

The system follows a clean object-oriented design with four core classes:

- **Pet**: Stores basic animal information (name, species, age)
- **Owner**: Represents the caregiver with available time and their pet
- **Task**: Individual care activities with duration, priority, and recurrence
- **Scheduler**: Core logic engine that builds schedules, detects conflicts, and explains decisions

The Scheduler uses a greedy algorithm that prioritizes high-importance tasks first, then fits lower-priority ones until time runs out. Tasks are assigned sequential start times starting from 8:00 AM.

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip for package management

### Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

#### Web Interface (Recommended)
```bash
streamlit run app.py
```
This launches a Streamlit web app where you can:
- Enter owner and pet information
- Add care tasks with priorities and durations
- Generate and view optimized schedules
- Filter tasks by completion status
- See conflict warnings and plan explanations

#### Command-Line Demo
```bash
python main.py
```
This runs a pre-configured demo showing all features with sample pets (Mochi the dog and Luna the cat).

### Running Tests
```bash
python -m pytest tests/test_pawpal.py -v
```
The test suite includes 22 tests covering scheduling logic, edge cases, recurrence, and conflict detection.

## Sample Interactions

### Basic Scheduling Example
**Input:**
- Owner: Jordan, 90 minutes available
- Pet: Mochi (dog)
- Tasks:
  - Morning walk: 30 min, high priority, daily recurrence
  - Breakfast feeding: 10 min, high priority, daily recurrence
  - Flea medication: 5 min, medium priority, weekly recurrence
  - Fetch/playtime: 40 min, low priority
  - Bath: 45 min, low priority

**Output:**
```
Scheduled tasks (sorted by start time):
┌─────────────┬────────────────────┬────────────┬────────────┬─────────────┬─────────┐
│ Start       │ Task               │ Duration   │ Priority   │ Recurrence  │ Status  │
├─────────────┼────────────────────┼────────────┼────────────┼─────────────┼─────────┤
│ 8:00 AM    │ Morning walk        │ 30 min     │ 🔴 high    │ 🔁 daily    │ ⏳ pending │
│ 8:30 AM    │ Breakfast feeding   │ 10 min     │ 🔴 high    │ 🔁 daily    │ ⏳ pending │
│ 8:40 AM    │ Flea medication     │ 5 min      │ 🟡 medium  │ 📅 weekly   │ ⏳ pending │
│ 8:45 AM    │ Fetch / playtime    │ 40 min     │ 🟢 low     │ —           │ ⏳ pending │
└─────────────┴────────────────────┴────────────┴────────────┴─────────────┴─────────┘

Skipped tasks (not enough time):
┌────────────────────┬────────────┬────────────┐
│ Task               │ Duration   │ Priority   │
├────────────────────┼────────────┼────────────┤
│ Bath               │ 45 min     │ 🟢 low     │
└────────────────────┴────────────┴────────────┘

✅ No scheduling conflicts detected.

Time used: 85 min | Time remaining: 5 min
```

### Recurrence Demonstration
**Input:** Complete the "Morning walk" task

**Output:**
```
Completing 'Morning walk' (recurrence: daily)
next_occurrence → Task(title='Morning walk', duration_minutes=30, priority='high', recurrence='daily', start_time=None, completed=False)
Pool size after: 6 (expected +1)
```

The completed task regenerates a fresh copy for the next day, maintaining the daily routine.

### Conflict Detection Example
**Input:** Two overlapping tasks
- Morning walk: starts 8:00 AM, 30 min duration
- Vet visit: starts 8:15 AM, 60 min duration

**Output:**
```
⚠️  Conflict: "Morning walk" (8:00 AM - 8:30 AM) overlaps with "Vet visit" (8:15 AM - 9:15 AM)
```

### Cross-Pet Conflict Example
**Input:** Jordan owns both Mochi (dog) and Luna (cat)
- Mochi: Morning walk at 8:00 AM
- Luna: Litter box cleaning at 8:00 AM

**Output:**
```
⚠️  Cross-pet conflict: Mochi's "Morning walk" overlaps with Luna's "Litter box cleaning" at 8:00 AM
```

### Advanced Gap Detection Example
**Input:** Find the next available 15-minute slot in an existing schedule with tasks at 8:00 AM (30 min) and 9:00 AM (10 min)

**Output:**
```
Next available slot for 15-minute task: 8:30 AM
(This fits in the gap between the 30-min walk ending at 8:30 AM and the 10-min feeding starting at 9:00 AM)
```

### Data Persistence Example
**Web App Startup:**
```
✅ Loaded previous session data!
💾 Data saved!
```

**CLI Demo:**
```
🐾 PawPal+ Persistence Demo
Data file: pawpal_data.json
✅ Loaded previous session data!
...
Saving Mochi's scheduler to pawpal_data.json...
✅ Data saved successfully!
File size: 1247 bytes
```

## Design Decisions

### Why This Architecture?
The system separates data storage (Pet, Owner, Task) from business logic (Scheduler) following single responsibility principle. This makes the code modular and testable.

### Key Trade-offs

**Greedy Scheduling Algorithm:**
- **Decision**: Use priority-first greedy approach instead of optimal scheduling
- **Rationale**: Simple, fast, and predictable for daily pet care
- **Trade-off**: May skip some lower-priority tasks that could fit if reordered, but ensures critical care (feeding, medication) always gets scheduled first

**Time-Based Ordering:**
- **Decision**: Assign sequential start times starting at 8:00 AM
- **Rationale**: Creates natural daily routines and makes schedules human-readable
- **Trade-off**: Doesn't consider owner preferences for specific times, but simplifies conflict detection

**Recurrence as Task Regeneration:**
- **Decision**: Completed recurring tasks create new instances rather than modifying existing ones
- **Rationale**: Maintains clean separation between completed and pending tasks
- **Trade-off**: Task pool grows over time, but prevents state mutation issues

## Testing Summary

### What Worked Well
- **Core scheduling logic**: All 32 tests pass, covering priority ordering, time budgeting, recurrence, conflict detection, advanced gap-finding, and data persistence
- **Edge case handling**: Zero tasks, zero time, exact time matches all work correctly
- **Integration testing**: Web interface properly connects to backend logic

### What Didn't Work Initially
- **Conflict detection complexity**: Early nested O(n²) approach was simplified to O(n) linear scan after realizing build_schedule() already ensures chronological ordering
- **Recurrence regeneration**: Initial implementation had exponential growth bugs; fixed with proper single-instance creation

### Lessons Learned
- **AI collaboration**: Claude Code was instrumental in generating initial skeletons, writing tests, and implementing features, but required careful review to catch integration issues
- **Incremental development**: Building core scheduling first, then adding features like recurrence and conflicts, made debugging much easier
- **Test-driven insights**: Writing tests first revealed edge cases (like zero-minute budgets) that weren't initially considered

## Reflection

This project taught me that AI systems aren't just about complex algorithms—they're about solving real human problems with the right balance of sophistication and simplicity. The greedy scheduling approach works because pet care has clear priority hierarchies: health first, then enrichment.

Working with AI tools showed me the importance of being an active collaborator rather than a passive recipient. While Claude Code could generate impressive amounts of code quickly, the real value came from guiding it toward the right design decisions and catching its occasional integration mistakes.

The project also reinforced that good system design is about trade-offs. We chose simplicity over optimality because pet owners need reliable, understandable schedules more than mathematically perfect ones. This pragmatism—prioritizing what matters most to users—is a key lesson for any AI system builder.

Most importantly, this project demonstrated how AI can augment human problem-solving. The system doesn't replace pet owner judgment; it amplifies it by handling the tedious optimization work, leaving owners free to focus on the relationship aspects of pet care.

## Video Walkthrough

Link!