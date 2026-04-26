import sys
sys.stdout.reconfigure(encoding="utf-8")

from tabulate import tabulate
from pawpal_system import Pet, Owner, Task, Scheduler, find_cross_scheduler_conflicts

# ---------------------------------------------------------------------------
# ANSI color helpers
# ---------------------------------------------------------------------------

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
DIM    = "\033[2m"

def green(text):  return f"{GREEN}{text}{RESET}"
def yellow(text): return f"{YELLOW}{text}{RESET}"
def red(text):    return f"{RED}{text}{RESET}"
def cyan(text):   return f"{CYAN}{text}{RESET}"
def bold(text):   return f"{BOLD}{text}{RESET}"
def dim(text):    return f"{DIM}{text}{RESET}"


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

PRIORITY_EMOJI = {"high": "🔴 high", "medium": "🟡 medium", "low": "🟢 low"}
RECUR_EMOJI    = {"daily": "🔁 daily", "weekly": "📅 weekly"}

def fmt_priority(p):
    label = PRIORITY_EMOJI.get(p, p)
    if p == "high":   return red(label)
    if p == "medium": return yellow(label)
    return green(label)

def fmt_status(completed):
    return green("✅ done") if completed else yellow("⏳ pending")

def fmt_recurrence(r):
    if not r:
        return dim("—")
    return cyan(RECUR_EMOJI.get(r, r))

def fmt_time(t):
    return cyan(t) if t else dim("unscheduled")


def section(title):
    bar = "-" * 52
    print(f"\n{CYAN}{bar}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{CYAN}{bar}{RESET}")


def header(title):
    bar = "=" * 52
    print(f"\n{BOLD}{bar}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{bar}{RESET}")


def print_task_table(tasks, show_start=False):
    if not tasks:
        print(dim("  (none)"))
        return

    rows = []
    for t in tasks:
        row = []
        if show_start:
            row.append(fmt_time(t.start_time))
        row += [
            t.title,
            f"{t.duration_minutes} min",
            fmt_priority(t.priority),
            fmt_recurrence(t.recurrence),
            fmt_status(t.completed),
        ]
        rows.append(row)

    headers = (["Start"] if show_start else []) + [
        "Task", "Duration", "Priority", "Recurrence", "Status"
    ]
    print(tabulate(rows, headers=headers, tablefmt="grid"))


def print_warnings(warnings):
    if not warnings:
        print(green("  ✅ No conflicts found."))
    else:
        for w in warnings:
            print(red(f"  ⚠️  {w}"))


# ---------------------------------------------------------------------------
# Pets & Owners
# ---------------------------------------------------------------------------

mochi = Pet(name="Mochi", species="dog", age=3)
luna  = Pet(name="Luna",  species="cat", age=5)

jordan = Owner(name="Jordan", available_minutes=90, pet=mochi)
alex   = Owner(name="Alex",   available_minutes=60, pet=luna)

# Tasks added out of order (low priority first) to prove sorting works
mochi_scheduler = Scheduler(owner=jordan)
mochi_scheduler.add_task(Task(title="Bath",             duration_minutes=45, priority="low"))
mochi_scheduler.add_task(Task(title="Fetch / playtime", duration_minutes=40, priority="low"))
mochi_scheduler.add_task(Task(title="Flea medication",  duration_minutes=5,  priority="medium", recurrence="weekly"))
mochi_scheduler.add_task(Task(title="Breakfast feeding",duration_minutes=10, priority="high",   recurrence="daily"))
mochi_scheduler.add_task(Task(title="Morning walk",     duration_minutes=30, priority="high",   recurrence="daily"))

luna_scheduler = Scheduler(owner=alex)
luna_scheduler.add_task(Task(title="Laser pointer play", duration_minutes=20, priority="low"))
luna_scheduler.add_task(Task(title="Vet checkup prep",   duration_minutes=30, priority="medium"))
luna_scheduler.add_task(Task(title="Brush / grooming",   duration_minutes=15, priority="medium"))
luna_scheduler.add_task(Task(title="Litter box cleaning",duration_minutes=10, priority="high"))
luna_scheduler.add_task(Task(title="Breakfast feeding",  duration_minutes=10, priority="high"))

# Build schedules
mochi_scheduler.build_schedule()
luna_scheduler.build_schedule()

# Mark a couple of tasks complete to test filtering
mochi_scheduler.scheduled_tasks[0].mark_complete()
mochi_scheduler.scheduled_tasks[1].mark_complete()
luna_scheduler.scheduled_tasks[0].mark_complete()


# ============================================================
# sort_by_time()
# ============================================================

header("SORTED BY START TIME")

section("Mochi's schedule (sorted by time)")
print_task_table(mochi_scheduler.sort_by_time(), show_start=True)

section("Luna's schedule (sorted by time)")
print_task_table(luna_scheduler.sort_by_time(), show_start=True)


# ============================================================
# filter_by_completion()
# ============================================================

header("FILTER BY COMPLETION STATUS")

section("Mochi — completed tasks")
print_task_table(mochi_scheduler.filter_by_completion(completed=True))

section("Mochi — pending tasks")
print_task_table(mochi_scheduler.filter_by_completion(completed=False))

section("Luna — completed tasks")
print_task_table(luna_scheduler.filter_by_completion(completed=True))

section("Luna — pending tasks")
print_task_table(luna_scheduler.filter_by_completion(completed=False))


# ============================================================
# filter_by_pet()
# ============================================================

header("FILTER BY PET NAME")

section("filter_by_pet('Mochi') on mochi_scheduler")
print_task_table(mochi_scheduler.filter_by_pet("Mochi"))

section("filter_by_pet('Luna') on mochi_scheduler  →  expect none")
print_task_table(mochi_scheduler.filter_by_pet("Luna"))

section("filter_by_pet('Luna') on luna_scheduler")
print_task_table(luna_scheduler.filter_by_pet("Luna"))


# ============================================================
# complete_task() — recurrence demo
# ============================================================

header("RECURRENCE — complete_task() DEMO")

walk = mochi_scheduler.scheduled_tasks[1]
flea = mochi_scheduler.scheduled_tasks[2]
bath = next(t for t in mochi_scheduler.tasks if t.title == "Bath")

print(f"\n  Task pool size before: {bold(str(len(mochi_scheduler.tasks)))}")

section(f"Completing '{walk.title}'  (recurrence: {walk.recurrence})")
next_walk = mochi_scheduler.complete_task(walk)
print(f"  next_occurrence → {cyan(str(next_walk))}")
print(f"  Pool size after: {bold(str(len(mochi_scheduler.tasks)))}  {dim('(expected +1)')}")

section(f"Completing '{flea.title}'  (recurrence: {flea.recurrence})")
next_flea = mochi_scheduler.complete_task(flea)
print(f"  next_occurrence → {cyan(str(next_flea))}")
print(f"  Pool size after: {bold(str(len(mochi_scheduler.tasks)))}  {dim('(expected +1)')}")

section(f"Completing '{bath.title}'  (recurrence: {bath.recurrence})")
next_bath = mochi_scheduler.complete_task(bath)
print(f"  next_occurrence → {dim(str(next_bath))}  {dim('(expected None)')}")
print(f"  Pool size after: {bold(str(len(mochi_scheduler.tasks)))}  {dim('(expected no change)')}")

section("Full task pool after completions")
print_task_table(mochi_scheduler.tasks)


# ============================================================
# conflict detection
# ============================================================

header("CONFLICT DETECTION DEMO")

conflict_pet   = Pet(name="Biscuit", species="dog", age=2)
conflict_owner = Owner(name="Sam", available_minutes=120, pet=conflict_pet)
conflict_sched = Scheduler(owner=conflict_owner)

task_a = Task(title="Morning walk", duration_minutes=30, priority="high")
task_b = Task(title="Vet visit",    duration_minutes=60, priority="high")
task_a.start_time = "8:00 AM"
task_b.start_time = "8:15 AM"
conflict_sched.scheduled_tasks = [task_a, task_b]

section("Same-pet conflict  (detect_conflicts)")
print_warnings(conflict_sched.detect_conflicts())

section("Cross-pet conflict  (find_cross_scheduler_conflicts)")

mochi2 = Pet(name="Mochi", species="dog", age=3)
luna2  = Pet(name="Luna",  species="cat", age=5)
s1 = Scheduler(owner=Owner(name="Jordan", available_minutes=60, pet=mochi2))
s2 = Scheduler(owner=Owner(name="Alex",   available_minutes=60, pet=luna2))

s1.add_task(Task(title="Morning walk",     duration_minutes=30, priority="high"))
s1.add_task(Task(title="Breakfast feeding",duration_minutes=15, priority="medium"))
s2.add_task(Task(title="Litter box cleaning",duration_minutes=20, priority="high"))
s2.add_task(Task(title="Breakfast feeding",  duration_minutes=15, priority="medium"))

s1.build_schedule()
s2.build_schedule()

print_warnings(find_cross_scheduler_conflicts([s1, s2]))

print()
