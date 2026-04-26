# PawPal+ UML Design
---

```
classDiagram
    class Pet {
        +str name
        +str species
        +int age
    }

    class Owner {
        +str name
        +int available_minutes
        +Pet pet
    }

    class Task {
        +str title
        +int duration_minutes
        +str priority
        +str recurrence
        +str start_time
        +bool completed
        +mark_complete() None
        +next_occurrence() Task
    }

    class Scheduler {
        +Owner owner
        +Pet pet
        +list~Task~ tasks
        +list~Task~ scheduled_tasks
        +list~Task~ skipped_tasks
        +add_task(task: Task) None
        +complete_task(task: Task) Task
        +build_schedule() list~Task~
        +sort_by_time() list~Task~
        +filter_by_completion(completed: bool) list~Task~
        +filter_by_pet(pet_name: str) list~Task~
        +detect_conflicts() list~str~
        +explain_plan() list~str~
    }

    class Utilities {
        <<module>>
        +PRIORITY_RANK dict
        +_minutes_to_time_str(minutes: int) str
        +_time_str_to_minutes(time_str: str) int
        +find_cross_scheduler_conflicts(schedulers: list) list~str~
    }

    Owner "1" --> "1" Pet : owns
    Scheduler --> Owner : uses
    Scheduler ..> Pet : derived from owner
    Scheduler "1" --> "many" Task : manages
    Task ..> Task : next_occurrence()
    Scheduler ..> Utilities : uses
```
