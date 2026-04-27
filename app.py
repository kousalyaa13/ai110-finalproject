import streamlit as st
from pawpal_system import Pet, Owner, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# Data persistence file
PERSISTENCE_FILE = "pawpal_data.json"

PRIORITY_EMOJI = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}

st.title("🐾 PawPal+")

st.divider()

# --- Load existing data or create default ---
if "scheduler" not in st.session_state:
    # Try to load from file first
    loaded_scheduler = Scheduler.load_from_file(PERSISTENCE_FILE)
    if loaded_scheduler:
        st.session_state.scheduler = loaded_scheduler
        st.session_state.owner_name = loaded_scheduler.owner.name
        st.session_state.pet_name = loaded_scheduler.owner.pet.name
        st.session_state.species = loaded_scheduler.owner.pet.species
        st.session_state.available_minutes = loaded_scheduler.owner.available_minutes
        st.success("✅ Loaded previous session data!")
    else:
        # Create default scheduler
        pet = Pet(name="Mochi", species="dog", age=3)
        owner = Owner(name="Jordan", available_minutes=90, pet=pet)
        st.session_state.scheduler = Scheduler(owner=owner)
        st.session_state.owner_name = owner.name
        st.session_state.pet_name = pet.name
        st.session_state.species = pet.species
        st.session_state.available_minutes = owner.available_minutes

# --- Owner & Pet setup ---
st.subheader("Owner & Pet Info")
owner_name = st.text_input("Owner name", value=st.session_state.owner_name)
pet_name = st.text_input("Pet name", value=st.session_state.pet_name)
species = st.selectbox("Species", ["dog", "cat", "other"], index=["dog", "cat", "other"].index(st.session_state.species))
available_minutes = st.number_input(
    "Available time today (minutes)", min_value=10, max_value=480, value=st.session_state.available_minutes
)

# Build or rebuild the Scheduler when owner/pet info changes
if (
    st.session_state.get("owner_name") != owner_name
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

    # Save changes to file
    st.session_state.scheduler.save_to_file(PERSISTENCE_FILE)
    st.success("💾 Data saved!")

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
    # Save after adding task
    st.session_state.scheduler.save_to_file(PERSISTENCE_FILE)
    st.success(f"Added: **{task_title}** ({priority} priority, {duration} min) 💾")

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

# --- AI Task Recommendations ---
st.subheader("🤖 AI Task Recommendations")

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Get AI Suggestions", type="primary"):
        with st.spinner("🤖 AI is analyzing your pet's needs..."):
            recommendations = st.session_state.scheduler.generate_task_recommendations()
            if recommendations:
                st.session_state.ai_recommendations = recommendations
                st.success(f"🤖 Generated {len(recommendations)} personalized task suggestions!")
            else:
                st.error("❌ Could not generate recommendations.")
                st.info("Check the **terminal/console output** for detailed error messages. Common issues:\n- API key is invalid or expired\n- Google Generative AI API is not enabled in your Google Cloud project\n- Network connectivity issues")
                # Debug info
                import os
                has_key = bool(os.getenv('GOOGLE_API_KEY'))
                st.caption(f"DEBUG: API Key loaded? {has_key}")

with col2:
    if st.button("Clear Suggestions"):
        if "ai_recommendations" in st.session_state:
            del st.session_state.ai_recommendations
        st.success("Suggestions cleared.")

# Display AI recommendations if available
if "ai_recommendations" in st.session_state and st.session_state.ai_recommendations:
    st.write("**Review and select tasks to add:**")

    # Create checkboxes for each recommendation
    selected_indices = []
    for i, rec in enumerate(st.session_state.ai_recommendations):
        priority_emoji = PRIORITY_EMOJI.get(rec['priority'], rec['priority'])
        recurrence_text = f" ({rec['recurrence']})" if rec['recurrence'] else ""

        label = f"**{rec['title']}** - {rec['duration_minutes']} min, {priority_emoji}{recurrence_text}"
        if st.checkbox(label, key=f"rec_{i}"):
            selected_indices.append(i)

    # Add selected tasks button
    if selected_indices:
        if st.button(f"✅ Add {len(selected_indices)} Selected Task(s)", type="primary"):
            added_count = 0
            for idx in selected_indices:
                rec = st.session_state.ai_recommendations[idx]
                task = Task(
                    title=rec['title'],
                    duration_minutes=rec['duration_minutes'],
                    priority=rec['priority'],
                    recurrence=rec['recurrence']
                )
                st.session_state.scheduler.add_task(task)
                added_count += 1

            # Save after adding tasks
            st.session_state.scheduler.save_to_file(PERSISTENCE_FILE)
            st.success(f"✅ Added {added_count} AI-recommended task(s) to your schedule! 💾")

            # Clear the recommendations after adding
            del st.session_state.ai_recommendations
            st.rerun()

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
        # Save after building schedule
        scheduler.save_to_file(PERSISTENCE_FILE)

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
