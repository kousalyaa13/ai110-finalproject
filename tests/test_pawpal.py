import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Pet, Owner, Task, Scheduler, find_cross_scheduler_conflicts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_scheduler(available_minutes=120):
    """Return a fresh Scheduler wired to a default pet/owner."""
    pet = Pet(name="Mochi", species="dog", age=3)
    owner = Owner(name="Jordan", available_minutes=available_minutes, pet=pet)
    return Scheduler(owner=owner)

def test_mark_complete_changes_status():
    """Task.completed should be False by default and True after mark_complete()."""
    task = Task(title="Morning walk", duration_minutes=30, priority="high")

    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_count():
    """Scheduler.add_task() should increase the number of tasks tracked for a pet."""
    pet = Pet(name="Mochi", species="dog", age=3)
    owner = Owner(name="Jordan", available_minutes=90, pet=pet)
    scheduler = Scheduler(owner=owner)

    assert len(scheduler.tasks) == 0

    scheduler.add_task(Task(title="Feeding", duration_minutes=10, priority="high"))
    assert len(scheduler.tasks) == 1

    scheduler.add_task(Task(title="Walk", duration_minutes=20, priority="medium"))
    assert len(scheduler.tasks) == 2


# ---------------------------------------------------------------------------
# Happy path: build_schedule
# ---------------------------------------------------------------------------

def test_build_schedule_happy_path():
    """All tasks that fit within available time should be scheduled."""
    scheduler = make_scheduler(available_minutes=60)
    scheduler.add_task(Task(title="Walk", duration_minutes=30, priority="high"))
    scheduler.add_task(Task(title="Feeding", duration_minutes=10, priority="medium"))

    scheduled = scheduler.build_schedule()

    assert len(scheduled) == 2
    assert len(scheduler.skipped_tasks) == 0


def test_build_schedule_skips_tasks_that_dont_fit():
    """Tasks exceeding the time budget should land in skipped_tasks."""
    scheduler = make_scheduler(available_minutes=30)
    scheduler.add_task(Task(title="Walk", duration_minutes=30, priority="high"))
    scheduler.add_task(Task(title="Bath", duration_minutes=45, priority="medium"))

    scheduler.build_schedule()

    assert len(scheduler.scheduled_tasks) == 1
    assert scheduler.scheduled_tasks[0].title == "Walk"
    assert len(scheduler.skipped_tasks) == 1
    assert scheduler.skipped_tasks[0].title == "Bath"


def test_build_schedule_assigns_start_times():
    """Every scheduled task should have a non-None start_time after build_schedule()."""
    scheduler = make_scheduler(available_minutes=60)
    scheduler.add_task(Task(title="Walk", duration_minutes=20, priority="high"))
    scheduler.add_task(Task(title="Feeding", duration_minutes=10, priority="medium"))

    scheduler.build_schedule()

    for task in scheduler.scheduled_tasks:
        assert task.start_time is not None


# ---------------------------------------------------------------------------
# Edge case: empty task list
# ---------------------------------------------------------------------------

def test_build_schedule_no_tasks():
    """Scheduler with zero tasks should produce an empty schedule without crashing."""
    scheduler = make_scheduler()

    scheduled = scheduler.build_schedule()

    assert scheduled == []
    assert scheduler.skipped_tasks == []


def test_build_schedule_zero_available_minutes():
    """When the owner has no free time, every task should be skipped."""
    scheduler = make_scheduler(available_minutes=0)
    scheduler.add_task(Task(title="Walk", duration_minutes=30, priority="high"))

    scheduler.build_schedule()

    assert scheduler.scheduled_tasks == []
    assert len(scheduler.skipped_tasks) == 1


def test_build_schedule_task_fits_exactly():
    """A task whose duration equals available_minutes exactly should be scheduled."""
    scheduler = make_scheduler(available_minutes=30)
    scheduler.add_task(Task(title="Walk", duration_minutes=30, priority="high"))

    scheduler.build_schedule()

    assert len(scheduler.scheduled_tasks) == 1
    assert scheduler.skipped_tasks == []


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """sort_by_time() should return tasks ordered earliest start_time first."""
    scheduler = make_scheduler(available_minutes=120)
    # Add in reverse priority so build_schedule assigns Walk first (high), then Feeding
    scheduler.add_task(Task(title="Walk", duration_minutes=30, priority="high"))
    scheduler.add_task(Task(title="Feeding", duration_minutes=20, priority="medium"))
    scheduler.add_task(Task(title="Playtime", duration_minutes=15, priority="low"))
    scheduler.build_schedule()

    # Manually scramble the order to prove sort_by_time fixes it
    scheduler.scheduled_tasks.reverse()
    sorted_tasks = scheduler.sort_by_time()

    times = [t.start_time for t in sorted_tasks]
    from pawpal_system import _time_str_to_minutes
    minutes = [_time_str_to_minutes(t) for t in times]
    assert minutes == sorted(minutes), f"Expected ascending order, got {times}"


def test_build_schedule_priority_order():
    """High-priority tasks should be scheduled before lower-priority ones."""
    scheduler = make_scheduler(available_minutes=40)
    # Only 40 min available; low task (30 min) + medium task (20 min) = 50 min total
    # High task (10 min) should always make it in; low (30 min) should be skipped
    scheduler.add_task(Task(title="Low task", duration_minutes=30, priority="low"))
    scheduler.add_task(Task(title="High task", duration_minutes=10, priority="high"))
    scheduler.add_task(Task(title="Medium task", duration_minutes=20, priority="medium"))

    scheduler.build_schedule()

    scheduled_titles = [t.title for t in scheduler.scheduled_tasks]
    assert "High task" in scheduled_titles
    assert "Medium task" in scheduled_titles
    assert "Low task" not in scheduled_titles


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_complete_daily_task_creates_new_occurrence():
    """Completing a daily task should add exactly one new task to the pool."""
    scheduler = make_scheduler()
    task = Task(title="Morning walk", duration_minutes=30, priority="high", recurrence="daily")
    scheduler.add_task(task)

    pool_before = len(scheduler.tasks)
    new_task = scheduler.complete_task(task)

    assert new_task is not None, "Expected a new Task for a daily recurrence"
    assert len(scheduler.tasks) == pool_before + 1


def test_complete_daily_task_new_occurrence_is_fresh():
    """The new occurrence from a daily task must be uncompleted with no start_time."""
    scheduler = make_scheduler()
    task = Task(title="Morning walk", duration_minutes=30, priority="high", recurrence="daily")
    task.start_time = "8:00 AM"
    scheduler.add_task(task)

    new_task = scheduler.complete_task(task)

    assert new_task.completed is False
    assert new_task.start_time is None


def test_complete_weekly_task_creates_new_occurrence():
    """Completing a weekly task should also regenerate one new task."""
    scheduler = make_scheduler()
    task = Task(title="Flea medication", duration_minutes=5, priority="high", recurrence="weekly")
    scheduler.add_task(task)

    pool_before = len(scheduler.tasks)
    new_task = scheduler.complete_task(task)

    assert new_task is not None
    assert len(scheduler.tasks) == pool_before + 1


def test_complete_non_recurring_task_does_not_add_to_pool():
    """Completing a one-off task must not grow the task pool."""
    scheduler = make_scheduler()
    task = Task(title="Bath", duration_minutes=20, priority="medium", recurrence=None)
    scheduler.add_task(task)

    pool_before = len(scheduler.tasks)
    new_task = scheduler.complete_task(task)

    assert new_task is None
    assert len(scheduler.tasks) == pool_before


def test_completing_recurring_task_twice_grows_pool_linearly():
    """Completing the same daily task twice should add exactly two new tasks total."""
    scheduler = make_scheduler()
    task = Task(title="Walk", duration_minutes=30, priority="high", recurrence="daily")
    scheduler.add_task(task)

    scheduler.complete_task(task)
    first_new = scheduler.tasks[-1]
    scheduler.complete_task(first_new)

    # Started with 1, completed twice → should now have 3 tasks (original + 2 new)
    assert len(scheduler.tasks) == 3


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_flags_overlapping_tasks():
    """Two tasks manually set to overlapping times should produce a warning."""
    scheduler = make_scheduler()
    task_a = Task(title="Walk", duration_minutes=30, priority="high")
    task_b = Task(title="Vet visit", duration_minutes=60, priority="high")
    task_a.start_time = "8:00 AM"
    task_b.start_time = "8:15 AM"  # starts while Walk is still running
    scheduler.scheduled_tasks.extend([task_a, task_b])

    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "Walk" in warnings[0]
    assert "Vet visit" in warnings[0]


def test_detect_conflicts_same_start_time():
    """Two tasks at the exact same start time should be flagged as a conflict."""
    scheduler = make_scheduler()
    task_a = Task(title="Feeding", duration_minutes=10, priority="high")
    task_b = Task(title="Medication", duration_minutes=5, priority="high")
    task_a.start_time = "9:00 AM"
    task_b.start_time = "9:00 AM"
    scheduler.scheduled_tasks.extend([task_a, task_b])

    warnings = scheduler.detect_conflicts()

    assert len(warnings) >= 1


def test_detect_conflicts_no_overlap_returns_empty():
    """Non-overlapping tasks should produce zero conflict warnings."""
    scheduler = make_scheduler()
    task_a = Task(title="Walk", duration_minutes=30, priority="high")
    task_b = Task(title="Feeding", duration_minutes=10, priority="medium")
    task_a.start_time = "8:00 AM"
    task_b.start_time = "9:00 AM"  # starts well after Walk ends at 8:30 AM
    scheduler.scheduled_tasks.extend([task_a, task_b])

    warnings = scheduler.detect_conflicts()

    assert warnings == []


def test_detect_conflicts_no_tasks():
    """Scheduler with no scheduled tasks should return no warnings."""
    scheduler = make_scheduler()

    warnings = scheduler.detect_conflicts()

    assert warnings == []


def test_detect_conflicts_single_task():
    """A single scheduled task cannot overlap with anything."""
    scheduler = make_scheduler()
    task = Task(title="Walk", duration_minutes=30, priority="high")
    task.start_time = "8:00 AM"
    scheduler.scheduled_tasks.append(task)

    warnings = scheduler.detect_conflicts()

    assert warnings == []


# ---------------------------------------------------------------------------
# Cross-pet conflict detection
# ---------------------------------------------------------------------------

def test_cross_scheduler_conflicts_detected():
    """Tasks from two pets at the same time should trigger a cross-pet warning."""
    pet1 = Pet(name="Mochi", species="dog", age=3)
    owner1 = Owner(name="Jordan", available_minutes=120, pet=pet1)
    s1 = Scheduler(owner=owner1)
    task1 = Task(title="Walk", duration_minutes=30, priority="high")
    task1.start_time = "8:00 AM"
    s1.scheduled_tasks.append(task1)

    pet2 = Pet(name="Luna", species="cat", age=2)
    owner2 = Owner(name="Jordan", available_minutes=120, pet=pet2)
    s2 = Scheduler(owner=owner2)
    task2 = Task(title="Feeding", duration_minutes=10, priority="high")
    task2.start_time = "8:00 AM"
    s2.scheduled_tasks.append(task2)

    warnings = find_cross_scheduler_conflicts([s1, s2])

    assert len(warnings) >= 1
    assert "cross-pet" in warnings[0]


def test_cross_scheduler_no_conflicts():
    """Non-overlapping tasks across pets should produce no cross-pet warnings."""
    pet1 = Pet(name="Mochi", species="dog", age=3)
    owner1 = Owner(name="Jordan", available_minutes=120, pet=pet1)
    s1 = Scheduler(owner=owner1)
    task1 = Task(title="Walk", duration_minutes=30, priority="high")
    task1.start_time = "8:00 AM"
    s1.scheduled_tasks.append(task1)

    pet2 = Pet(name="Luna", species="cat", age=2)
    owner2 = Owner(name="Jordan", available_minutes=120, pet=pet2)
    s2 = Scheduler(owner=owner2)
    task2 = Task(title="Feeding", duration_minutes=10, priority="high")
    task2.start_time = "9:00 AM"
    s2.scheduled_tasks.append(task2)

    warnings = find_cross_scheduler_conflicts([s1, s2])

    assert warnings == []
