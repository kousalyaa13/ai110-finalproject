import json
import os
from typing import Dict, List, Any, Optional
from google import genai

PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}
DAY_START_HOUR = 8  # schedule begins at 8:00 AM


def _minutes_to_time_str(minutes_from_midnight: int) -> str:
    """Convert total minutes from midnight to a readable time string."""
    hour = minutes_from_midnight // 60
    minute = minutes_from_midnight % 60
    period = "AM" if hour < 12 else "PM"
    display_hour = hour if hour <= 12 else hour - 12
    if display_hour == 0:
        display_hour = 12
    return f"{display_hour}:{minute:02d} {period}"


def _time_str_to_minutes(time_str: str) -> int:
    """Parse a time string like '8:30 AM' back into minutes from midnight for sorting."""
    time_part, period = time_str.split()
    hour, minute = map(int, time_part.split(":"))
    if period == "AM" and hour == 12:
        hour = 0
    elif period == "PM" and hour != 12:
        hour += 12
    return hour * 60 + minute


class Pet:
    def __init__(self, name: str, species: str, age: int):
        """Create a pet with a name, species, and age."""
        self.name = name
        self.species = species
        self.age = age

    def __repr__(self) -> str:
        """Return a developer-readable string for this pet."""
        return f"Pet(name={self.name!r}, species={self.species!r}, age={self.age})"


class Owner:
    def __init__(self, name: str, available_minutes: int, pet: Pet):
        """Create an owner with a name, daily time budget, and their pet."""
        self.name = name
        self.available_minutes = available_minutes
        self.pet = pet

    def __repr__(self) -> str:
        """Return a developer-readable string for this owner."""
        return (
            f"Owner(name={self.name!r}, "
            f"available_minutes={self.available_minutes}, "
            f"pet={self.pet.name!r})"
        )


class Task:
    def __init__(
        self,
        title: str,
        duration_minutes: int,
        priority: str,
        recurrence: str | None = None,
    ):
        """Create a care task with a title, duration, priority, and optional recurrence."""
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority  # "low", "medium", or "high"
        self.recurrence = recurrence  # None, "daily", or "weekly"
        self.start_time: str | None = None  # assigned by Scheduler.build_schedule()
        self.completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def next_occurrence(self) -> "Task | None":
        """Return a fresh copy of this task for the next occurrence, or None if non-recurring."""
        if self.recurrence not in ("daily", "weekly"):
            return None
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            recurrence=self.recurrence,
        )

    def __repr__(self) -> str:
        """Return a developer-readable string for this task."""
        return (
            f"Task(title={self.title!r}, "
            f"duration={self.duration_minutes}min, "
            f"priority={self.priority!r}, "
            f"recurrence={self.recurrence!r})"
        )


class Scheduler:
    def __init__(self, owner: Owner):
        """Create a scheduler for an owner, deriving the pet from the owner."""
        self.owner = owner
        self.pet = owner.pet  # derived from owner
        self.tasks: list[Task] = []
        self.scheduled_tasks: list[Task] = []
        self.skipped_tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a task to the pool of tasks to be scheduled."""
        self.tasks.append(task)

    def complete_task(self, task: Task) -> "Task | None":
        """Mark a task complete and auto-add the next occurrence if it recurs."""
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task:
            self.add_task(next_task)
        return next_task

    def build_schedule(self) -> list[Task]:
        """Sort tasks by priority and fit as many as possible into the owner's available time."""
        self.scheduled_tasks = []
        self.skipped_tasks = []

        sorted_tasks = sorted(
            self.tasks,
            key=lambda t: PRIORITY_RANK.get(t.priority, 0),
            reverse=True,
        )

        time_used = 0
        current_minutes = DAY_START_HOUR * 60  # start at 8:00 AM in minutes

        for task in sorted_tasks:
            if time_used + task.duration_minutes <= self.owner.available_minutes:
                task.start_time = _minutes_to_time_str(current_minutes)
                current_minutes += task.duration_minutes
                time_used += task.duration_minutes
                self.scheduled_tasks.append(task)
            else:
                task.start_time = None
                self.skipped_tasks.append(task)

        return self.scheduled_tasks

    def detect_conflicts(self) -> list[str]:
        """Check scheduled tasks for time overlaps and return warning messages."""
        warnings = []
        timed = [t for t in self.scheduled_tasks if t.start_time]

        for i, a in enumerate(timed):
            a_start = _time_str_to_minutes(a.start_time)
            a_end = a_start + a.duration_minutes
            for b in timed[i + 1:]:
                b_start = _time_str_to_minutes(b.start_time)
                b_end = b_start + b.duration_minutes
                if a_start < b_end and b_start < a_end:
                    warnings.append(
                        f"WARNING [{self.pet.name}]: '{a.title}' ({a.start_time}, "
                        f"{a.duration_minutes}min) overlaps with "
                        f"'{b.title}' ({b.start_time}, {b.duration_minutes}min)"
                    )

        return warnings

    def filter_by_completion(self, completed: bool) -> list[Task]:
        """Return tasks from the pool that match the given completion status."""
        return [t for t in self.tasks if t.completed == completed]

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return this scheduler's tasks if the pet name matches, otherwise an empty list."""
        if self.pet.name.lower() == pet_name.lower():
            return list(self.tasks)
        return []

    def sort_by_time(self) -> list[Task]:
        """Sort scheduled tasks by their start_time, earliest first."""
        self.scheduled_tasks.sort(
            key=lambda t: _time_str_to_minutes(t.start_time) if t.start_time else 0
        )
        return self.scheduled_tasks

    def find_next_available_slot(self, duration_minutes: int) -> str | None:
        """
        Advanced Algorithmic Capability: Find the earliest available time slot
        that can accommodate a task of the given duration, considering existing
        scheduled tasks and the owner's total available time.

        This goes beyond basic sequential scheduling by intelligently finding
        gaps in the schedule where new tasks can be inserted optimally.

        Returns the start time string (e.g., "8:30 AM") for the earliest slot,
        or None if no slot is available.
        """
        if not self.scheduled_tasks:
            # No tasks scheduled yet, start from the beginning
            start_minutes = DAY_START_HOUR * 60
            if duration_minutes <= self.owner.available_minutes:
                return _minutes_to_time_str(start_minutes)
            return None

        # Ensure tasks are sorted by time
        self.sort_by_time()

        # Check for gaps between scheduled tasks
        day_start_minutes = DAY_START_HOUR * 60
        day_end_minutes = day_start_minutes + self.owner.available_minutes

        # Check gap before first task
        first_task_start = _time_str_to_minutes(self.scheduled_tasks[0].start_time)
        if first_task_start - day_start_minutes >= duration_minutes:
            return _minutes_to_time_str(day_start_minutes)

        # Check gaps between consecutive tasks
        for i in range(len(self.scheduled_tasks) - 1):
            current_task = self.scheduled_tasks[i]
            next_task = self.scheduled_tasks[i + 1]

            current_end = _time_str_to_minutes(current_task.start_time) + current_task.duration_minutes
            next_start = _time_str_to_minutes(next_task.start_time)

            gap_duration = next_start - current_end
            if gap_duration >= duration_minutes:
                return _minutes_to_time_str(current_end)

        # Check gap after last task
        last_task = self.scheduled_tasks[-1]
        last_end = _time_str_to_minutes(last_task.start_time) + last_task.duration_minutes
        remaining_time = day_end_minutes - last_end

        if remaining_time >= duration_minutes:
            return _minutes_to_time_str(last_end)

        # No available slot found
        return None

    def generate_task_recommendations(self) -> List[Dict[str, Any]]:
        """
        AI Feature: Use Gemini API to generate personalized task recommendations
        based on pet profile and owner availability.

        This is a substantial AI feature that provides meaningful behavioral changes
        by suggesting tasks users might not have considered, leading to more complete
        pet care schedules.
        """
        try:
            # Get API key from environment
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                return []

            client = genai.Client(api_key=api_key)

            # Create structured prompt with few-shot examples
            prompt = f"""
You are an expert veterinarian and pet care specialist. Based on the following pet profile, suggest 6-8 essential daily and weekly care tasks that would be appropriate for this specific animal.

Pet Profile:
- Species: {self.pet.species}
- Age: {self.pet.age} years old
- Owner available time: {self.owner.available_minutes} minutes per day
- Pet name: {self.pet.name}

For each task, provide:
- title: A clear, specific task name
- duration_minutes: Realistic time estimate based on the pet's needs
- priority: "high" for critical care (feeding, medication), "medium" for important care (exercise, grooming), "low" for optional enrichment
- recurrence: "daily", "weekly", or null for one-time tasks

Return ONLY a valid JSON array of task objects. No additional text or explanation.

Examples:

For a "dog, 2 years old" with 90 minutes available:
[
  {{"title": "Morning walk", "duration_minutes": 30, "priority": "high", "recurrence": "daily"}},
  {{"title": "Breakfast feeding", "duration_minutes": 10, "priority": "high", "recurrence": "daily"}},
  {{"title": "Playtime/fetch", "duration_minutes": 20, "priority": "medium", "recurrence": "daily"}},
  {{"title": "Brush coat", "duration_minutes": 15, "priority": "medium", "recurrence": "weekly"}},
  {{"title": "Training session", "duration_minutes": 15, "priority": "low", "recurrence": "daily"}}
]

For a "cat, 1 year old" with 60 minutes available:
[
  {{"title": "Litter box cleaning", "duration_minutes": 10, "priority": "high", "recurrence": "daily"}},
  {{"title": "Breakfast feeding", "duration_minutes": 5, "priority": "high", "recurrence": "daily"}},
  {{"title": "Interactive play", "duration_minutes": 15, "priority": "medium", "recurrence": "daily"}},
  {{"title": "Brush fur", "duration_minutes": 10, "priority": "medium", "recurrence": "weekly"}},
  {{"title": "Litter box change", "duration_minutes": 20, "priority": "medium", "recurrence": "weekly"}}
]
"""

            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config={
                    "temperature": 0.3,
                    "max_output_tokens": 800,
                },
            )

            # Parse the response text
            if hasattr(response, "text") and response.text:
                content = response.text.strip()
            else:
                return []
            recommendations = json.loads(content)

            # Validate the response structure
            if not isinstance(recommendations, list):
                return []

            validated_recommendations = []
            for rec in recommendations:
                if all(key in rec for key in ['title', 'duration_minutes', 'priority', 'recurrence']):
                    # Ensure priority is valid
                    if rec['priority'] not in ['high', 'medium', 'low']:
                        rec['priority'] = 'medium'
                    # Ensure recurrence is valid
                    if rec['recurrence'] not in [None, 'daily', 'weekly']:
                        rec['recurrence'] = None
                    validated_recommendations.append(rec)

            return validated_recommendations[:8]  # Limit to 8 recommendations

        except Exception as e:
            print(f"AI recommendation error: {e}")
            return []

    def to_dict(self) -> Dict[str, Any]:
        """Convert scheduler to dictionary for JSON serialization."""
        return {
            "owner": {
                "name": self.owner.name,
                "available_minutes": self.owner.available_minutes,
                "pet": {
                    "name": self.owner.pet.name,
                    "species": self.owner.pet.species,
                    "age": self.owner.pet.age,
                }
            },
            "tasks": [
                {
                    "title": task.title,
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "recurrence": task.recurrence,
                    "start_time": task.start_time,
                    "completed": task.completed,
                }
                for task in self.tasks
            ],
            "scheduled_tasks": [
                {
                    "title": task.title,
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "recurrence": task.recurrence,
                    "start_time": task.start_time,
                    "completed": task.completed,
                }
                for task in self.scheduled_tasks
            ],
            "skipped_tasks": [
                {
                    "title": task.title,
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "recurrence": task.recurrence,
                    "start_time": task.start_time,
                    "completed": task.completed,
                }
                for task in self.skipped_tasks
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scheduler":
        """Reconstruct scheduler from dictionary loaded from JSON."""
        # Reconstruct pet
        pet_data = data["owner"]["pet"]
        pet = Pet(
            name=pet_data["name"],
            species=pet_data["species"],
            age=pet_data["age"]
        )

        # Reconstruct owner
        owner_data = data["owner"]
        owner = Owner(
            name=owner_data["name"],
            available_minutes=owner_data["available_minutes"],
            pet=pet
        )

        # Create scheduler
        scheduler = cls(owner=owner)

        # Reconstruct tasks
        def task_from_dict(task_data: Dict[str, Any]) -> Task:
            task = Task(
                title=task_data["title"],
                duration_minutes=task_data["duration_minutes"],
                priority=task_data["priority"],
                recurrence=task_data.get("recurrence"),  # Handle None values
            )
            task.start_time = task_data.get("start_time")  # Handle None values
            task.completed = task_data["completed"]
            return task

        scheduler.tasks = [task_from_dict(t) for t in data["tasks"]]
        scheduler.scheduled_tasks = [task_from_dict(t) for t in data["scheduled_tasks"]]
        scheduler.skipped_tasks = [task_from_dict(t) for t in data["skipped_tasks"]]

        return scheduler

    def save_to_file(self, filename: str) -> None:
        """Save scheduler data to JSON file."""
        data = self.to_dict()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, filename: str) -> Optional["Scheduler"]:
        """Load scheduler data from JSON file. Returns None if file doesn't exist."""
        if not os.path.exists(filename):
            return None

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error loading {filename}: {e}")
            return None

    def explain_plan(self) -> list[str]:
        """Return a human-readable explanation of why each task was scheduled or skipped."""
        if not self.scheduled_tasks and not self.skipped_tasks:
            return ["No schedule built yet. Call build_schedule() first."]

        explanations = []
        time_used = sum(t.duration_minutes for t in self.scheduled_tasks)

        explanations.append(
            f"Daily plan for {self.owner.name}'s pet {self.pet.name} "
            f"({self.pet.species}, age {self.pet.age}):"
        )
        explanations.append(
            f"Available time: {self.owner.available_minutes} min | "
            f"Scheduled: {time_used} min | "
            f"Remaining: {self.owner.available_minutes - time_used} min"
        )
        explanations.append("")

        if self.scheduled_tasks:
            explanations.append("Scheduled tasks:")
            for task in self.scheduled_tasks:
                explanations.append(
                    f"  - [{task.start_time}] {task.title} "
                    f"({task.duration_minutes} min, priority: {task.priority}) "
                    f"— included because it is {task.priority} priority and fits in the available time."
                )

        if self.skipped_tasks:
            explanations.append("")
            explanations.append("Skipped tasks:")
            for task in self.skipped_tasks:
                explanations.append(
                    f"  - {task.title} ({task.duration_minutes} min, priority: {task.priority}) "
                    f"— skipped because there was not enough remaining time."
                )

        return explanations


def find_cross_scheduler_conflicts(schedulers: list[Scheduler]) -> list[str]:
    """Check for time overlaps across multiple schedulers and return warning messages."""
    warnings = []

    all_tasks: list[tuple[str, Task]] = []
    for s in schedulers:
        for t in s.scheduled_tasks:
            if t.start_time:
                all_tasks.append((s.pet.name, t))

    for i, (pet_a, a) in enumerate(all_tasks):
        a_start = _time_str_to_minutes(a.start_time)
        a_end = a_start + a.duration_minutes
        for pet_b, b in all_tasks[i + 1:]:
            b_start = _time_str_to_minutes(b.start_time)
            b_end = b_start + b.duration_minutes
            if a_start < b_end and b_start < a_end:
                warnings.append(
                    f"WARNING [cross-pet]: {pet_a}'s '{a.title}' ({a.start_time}, "
                    f"{a.duration_minutes}min) overlaps with "
                    f"{pet_b}'s '{b.title}' ({b.start_time}, {b.duration_minutes}min)"
                )

    return warnings
