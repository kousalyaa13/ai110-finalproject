# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
    - My initial UML design was based on the classes I decided to make. I designed the system with four main classes: Pet, Owner, Task, and Scheduler. The Pet class stores basic information about the animal, such as its name, species, and age. The Owner class stores details about the person, including their name and how much time they have each day to take care of their pet. The Owner is also connected to one Pet, showing that each owner is responsible for a specific animal. The Task class represents different care activities, such as feeding or walking, and includes details like the task name, how long it takes, and its priority level.
    - The Scheduler is the main part of the system where all the logic happens. It takes information from the Owner, the Pet, and a list of Tasks to create a daily care plan. The Scheduler decides which tasks should be included based on the owner’s available time and the priority of each task. It also explains why certain tasks were included or skipped. While the Pet, Owner, and Task classes are mainly used to store data, the Scheduler is responsible for making decisions and organizing everything into a useful plan.

- What classes did you include, and what responsibilities did you assign to each?
    - Three core actions the user should be able to perform are:
        1. Manage pet and owner data - Store owner's and pet info
        2. Manage tasks - add a list of tasks for the owner to choose from, add remove and editing a task functionality, show list of tasks
        3. Build a schedule based on these requirements - be able to assign order of the tasks, sort/filter tasks by priorities and duration so they fit within the owner's schedule
    - The classes I included were:
        1. Pet 
            Attributes: name, species, age
            Actions: Represents the animal being cared for
        2. Owner
            Attributes: name, available_minutes
            Actions: Know the owner of the pet
        3. Task
            Attributes: title, duration_minutes, priority
            Actions: Represents one care activity
        4. Scheduler
            Attributes: owner, pet, tasks
            Methods: build_schedule() - builds schedule, explain_plan() - explains what was skipped/included in the schedule

**b. Design changes**

- Did your design change during implementation? If yes, describe at least one change and why you made it.
    - Yes, the design changed during the review of the skeleton. Originally, Scheduler took both an Owner and a Pet as separate parameters, but since Owner already holds a reference to their Pet, passing Pet again was redundant. The fix was to have Scheduler only take Owner, then derive the pet from owner.pet internally. This made the relationship cleaner and more consistent with how the classes are actually connected.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
    - The scheduler considers two main constraints: time and priority. Time is the core limit as the owner only has a fixed number of minutes available in a day, so tasks that push past that budget get skipped. Priority acts as the sorting rule that decides which tasks get those minutes first. High-priority tasks (like feeding or medication) are always scheduled before medium or low ones.
    - When thinking about conflict detection specifically, there is also an implicit ordering constraint as no two tasks can overlap in time. The original detect_conflicts approach used a nested loop to check every possible pair of tasks, which runs in O(n²) time. But because build_schedule already places tasks in strict time order, a single linear scan is enough: you only need to check if each task starts before the previous one finishes. This cuts the work down to O(n) and matches how the schedule is actually built.

- How did you decide which constraints mattered most?
    - Priority was chosen as the most important constraint because it directly reflects a pet's health needs. For example, a missed feeding matters more than a missed grooming session. Time was treated as a hard cap rather than something to negotiate around, since the owner's availability is fixed. Ordering and conflict detection were considered secondary because the build process already guarantees a conflict-free sequence, making the nested loop unnecessary for normal use.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
    - The scheduler uses a greedy approach, meaning it picks the highest-priority tasks first and stops as soon as the time budget runs out. This is fast and simple, but it is not always optimal. For example, two medium-priority tasks that together fit perfectly in the remaining time might get skipped in favor of one high-priority task that uses all the time by itself. A smarter approach would consider all possible combinations, but that would be much slower and more complex to implement.

- Why is that tradeoff reasonable for this scenario?
    - For a daily pet care planner, speed and simplicity matter more than finding the perfect combination. Owners are not running hundreds of tasks at once, so the small loss in optimality is not noticeable in practice. The greedy approach also matches how people naturally think about scheduling: do the most important things first, then fit in whatever else there is time for.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
    - I used Claude Code throughout the entire project, starting with brainstorming the core actions the app should support and deciding which classes to create. It helped draft the initial UML diagram, generate the class skeletons, and then flesh out the full implementation with working logic. It also wrote the test suite, added docstrings, wired the backend to the Streamlit UI, and helped add features like recurrence, conflict detection, sorting, and filtering. Later in the project it helped improve the terminal output in main.py using tabulate and ANSI color codes, and updated the README and UML diagram to reflect all the changes.

- What kinds of prompts or questions were most helpful?
    - The most useful prompts were specific and tied to a concrete goal. Asking to "review the skeleton and identify any missing relationships or logic bottlenecks" led to catching the redundant Pet parameter in Scheduler before any logic was written. Asking to "flesh out the full implementation" with a clear description of what each method should do produced working code right away. Asking follow-up questions like "how could this algorithm be simplified?" helped think through tradeoffs without changing the code unnecessarily.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
    - When the conflict detection feature was added, the AI's edit accidentally moved several Scheduler methods outside the class body, leaving them as loose module-level functions. The code looked correct at a glance but would have failed at runtime. This was caught by reviewing the full file after the edit, not just the diff.

- How did you evaluate or verify what the AI suggested?
    - Every significant change was verified by running the code in the terminal through main.py. If a new feature was added, main.py was updated to call it directly so the output could be checked. For structural changes like the class fix above, the whole file was re-read to confirm the indentation and method ownership were correct before moving on.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
    - The test suite covered task completion, meaning that calling mark_complete() correctly flips the completed flag. It also tested that adding a task to a Scheduler increases the task count, that build_schedule respects the time budget and skips tasks that do not fit, that tasks are sorted correctly by priority before scheduling, and that sort_by_time returns tasks in chronological order. 
    - Recurrence was tested for both daily and weekly tasks by verifying that complete_task returns a fresh Task copy and adds it back to the pool, and that non-recurring tasks return None. Edge cases like an empty task list and a zero-minute time budget were also included.

- Why were these tests important?
    - These tests mattered because the scheduler's usefulness depends entirely on its correctness. If priority ordering is wrong, critical tasks like feeding or medication could be skipped in favor of low-priority ones. If recurrence does not regenerate tasks properly, daily care routines would silently disappear after the first completion. Testing the edge cases ensured the code does not crash or behave unexpectedly in boundary situations.

**b. Confidence**

- How confident are you that your scheduler works correctly?
    - The core scheduling logic is reliable for the scenarios it was built for. The greedy algorithm is straightforward, and the tests cover the main happy paths and several edge cases. I am reasonably confident that this scheduler works for all test cases.

- What edge cases would you test next if you had more time?
    - It would be worth testing what happens when two tasks have the same priority but only one fits. The current implementation picks whichever comes first in the list, which may not always be the right choice. Testing with tasks that have exactly equal durations to the time budget would also be useful, as well as verifying that cross-pet conflict detection works correctly when three or more schedulers are passed in at the same time.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
    - The conflict detection and recurrence features felt like the most meaningful additions. Conflict detection adds real value because it surfaces problems the user might not notice just by looking at a list of tasks. Recurrence was satisfying because it required thinking about how objects should generate new versions of themselves, which felt like a genuinely object-oriented design decision rather than just storing data. 
    - I also liked implementing the two extension features: Advanced Priority Scheduling and Professional UI and Output Formatting. This improved the overall feel and readability of the app.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
    - The time budgeting system only works in total minutes and does not account for breaks, travel time, or tasks that must happen at a specific time of day. A future version could let owners set hard time windows for certain tasks, like "feeding must happen between 7am and 9am," and have the app respect those windows. It would also be better to let users mark tasks complete directly from the Streamlit UI instead of only tracking it in the backend.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
    - The most important lesson was that AI is most useful when you already have a clear idea of what you want. Vague prompts produced generic results, but specific prompts tied to a concrete goal produced working code and useful design feedback. Knowing enough about the system to review what the AI produced critically, rather than just accepting it, was what made the collaboration effective. AI accelerated the work, but judgment about what was correct still had to come from the developer.
