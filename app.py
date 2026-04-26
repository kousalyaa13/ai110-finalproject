import streamlit as st
from pawpal_system import Pet, Owner, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

PRIORITY_EMOJI = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}

st.title("🐾 PawPal+")

st.divider()

# --- Owner & Pet setup ---
st.subheader("Owner & Pet Info")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
available_minutes = st.number_input(
    "Available time today (minutes)", min_value=10, max_value=480, value=90
)

# Build or rebuild the Scheduler when owner/pet info changes
if (
    "scheduler" not in st.session_state
    or st.session_state.get("owner_name") != owner_name
    or st.session_state.get("pet_name") != pet_name
    or st.session_state.get("species") != species
    or st.session_state.get("available_minutes") != available_minutes
):
    pet = Pet(name=pet_name, species=species, age=1)
    owner = Owner(name=owner_name, available_minutes=int(available_minutes), pet=pet)
    st.session_state.scheduler = Scheduler(owner=owner)
    st.session_state.owner_name = owner_name
    st.session_state.pet_name = pet_name
    st.session_state.species = species
    st.session_state.available_minutes = available_minutes

st.divider()

# --- Add tasks ---
st.subheader("Tasks")

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    recurrence = st.selectbox("Recurrence", ["none", "daily", "weekly"])

if st.button("Add task"):
    task = Task(
        title=task_title,
        duration_minutes=int(duration),
        priority=priority,
        recurrence=None if recurrence == "none" else recurrence,
    )
    st.session_state.scheduler.add_task(task)
    st.success(f"Added: **{task_title}** ({priority} priority, {duration} min)")

# Display current task pool
current_tasks = st.session_state.scheduler.tasks
if current_tasks:
    st.caption(f"{len(current_tasks)} task(s) in pool")
    st.table(
        [
            {
                "Title": t.title,
                "Duration (min)": t.duration_minutes,
                "Priority": PRIORITY_EMOJI.get(t.priority, t.priority),
                "Recurrence": t.recurrence or "—",
                "Status": "Done" if t.completed else "Pending",
            }
            for t in current_tasks
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Generate schedule ---
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    scheduler = st.session_state.scheduler
    if not scheduler.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler.build_schedule()
        scheduler.sort_by_time()

        time_used = sum(t.duration_minutes for t in scheduler.scheduled_tasks)
        time_remaining = int(available_minutes) - time_used

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Scheduled", f"{len(scheduler.scheduled_tasks)} tasks")
        col2.metric("Time used", f"{time_used} min")
        col3.metric("Time remaining", f"{time_remaining} min")

        # Scheduled tasks
        if scheduler.scheduled_tasks:
            st.success("Scheduled tasks (sorted by start time)")
            st.table(
                [
                    {
                        "Start time": t.start_time,
                        "Task": t.title,
                        "Duration (min)": t.duration_minutes,
                        "Priority": PRIORITY_EMOJI.get(t.priority, t.priority),
                        "Recurrence": t.recurrence or "—",
                    }
                    for t in scheduler.scheduled_tasks
                ]
            )

        # Skipped tasks
        if scheduler.skipped_tasks:
            st.warning(f"{len(scheduler.skipped_tasks)} task(s) skipped — not enough time")
            st.table(
                [
                    {
                        "Task": t.title,
                        "Duration (min)": t.duration_minutes,
                        "Priority": PRIORITY_EMOJI.get(t.priority, t.priority),
                    }
                    for t in scheduler.skipped_tasks
                ]
            )

        # Conflict detection
        conflicts = scheduler.detect_conflicts()
        if conflicts:
            st.error(f"{len(conflicts)} scheduling conflict(s) detected")
            for w in conflicts:
                st.warning(w)
        else:
            st.success("No scheduling conflicts detected.")

        # Completion filter
        st.divider()
        st.subheader("Filter by Status")
        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            st.markdown("**Completed tasks**")
            done = scheduler.filter_by_completion(completed=True)
            if done:
                st.table([{"Task": t.title, "Priority": PRIORITY_EMOJI.get(t.priority, t.priority)} for t in done])
            else:
                st.info("No completed tasks yet.")

        with filter_col2:
            st.markdown("**Pending tasks**")
            pending = scheduler.filter_by_completion(completed=False)
            if pending:
                st.table([{"Task": t.title, "Priority": PRIORITY_EMOJI.get(t.priority, t.priority)} for t in pending])
            else:
                st.success("All tasks completed!")

        # Plan explanation
        with st.expander("View plan explanation"):
            for line in scheduler.explain_plan():
                st.text(line)
