Slide 1: Title + Project Overview
- Title: PawPal+ AI Pet Care Scheduler
- Subtitle: Extending a pet care scheduling app with Gemini 2.5 Flash AI recommendations
- Bullet points:
  - Original base project: pet care scheduler with recurring tasks, priority ordering, and conflict detection
  - New extension: AI task recommendation feature, JSON persistence, reliability handling
- Image: assets/pic1.jpg (homepage or main UI screenshot)

Slide 2: Original Project and Scope
- Short description of original system:
  - Base project goal: build a pet care scheduling assistant for owners
  - Capabilities: add tasks, schedule based on owner time, detect conflicts, support daily/weekly recurrence
- Why it was a good starting point for extension
- Image: assets/pic2.jpg (task creation or schedule page screenshot)

Slide 3: New AI Extension
- What was added:
  - Gemini 2.5 Flash powered task recommendations
  - Personalized task suggestions based on pet profile and owner availability
  - Robust error handling for empty or malformed AI output
- What this adds to the system:
  - More complete pet care plans
  - Suggestions users might not have considered
- Image: assets/pic3a.jpg or pic3b.jpg (AI recommendation UI)

Slide 4: System Diagram
- Main components:
  - Data Retriever / Loader: loads saved pet and schedule data from JSON
  - Agent: AI recommendation engine using Google Gemini 2.5 Flash
  - Scheduler: builds schedules, detects conflicts, explains task decisions
  - Evaluator / Tester: validation and reliability logic plus test suite
- Data flow:
  - Input: owner info, pet profile, tasks, saved data
  - Process: load data -> generate recommendations -> schedule tasks -> detect conflicts -> save data
  - Output: optimized schedule, task list, AI suggestions
- Human/testing involvement:
  - User enters pet and task data in the UI
  - User reviews AI recommendations and chooses tasks
  - Automated tests validate behavior and error handling
- Image: assets/uml_final.jpg (final UML diagram)

Slide 5: Demo Case 1 — End-to-End Run
- Show a complete flow with 2-3 inputs:
  - Input 1: dog, 90 min available, feeding and walk tasks
  - Input 2: cat, 60 min available, litter and play tasks
  - Input 3: add AI recommendations for a new pet or schedule
- Show outputs clearly:
  - Scheduled tasks list
  - Skipped tasks explanation
  - Remaining time/used time
- Image: assets/pic4.jpg (schedule output screenshot)

Slide 6: AI Feature Behavior
- Explain the AI behavior:
  - Uses pet profile and minutes available
  - Generates 5-6 recommendation tasks with title, duration, priority, recurrence
  - Limits output to 8 suggestions
- Show a live example:
  - Click "Get AI Suggestions"
  - Display generated recommended tasks
  - Select items to add to the schedule
- Image: assets/pic5.jpg or pic6.jpg (recommendation result screenshot)

Slide 7: Reliability and Guardrails
- Show reliability behavior:
  - Graceful fallback when API key is missing
  - Error handling for truncated or malformed JSON
  - Validation of recommendation structure and priority values
- Explain testing/evaluation:
  - Use automated tests to verify scheduling, persistence, and AI behavior
  - Show how the system prints error details when AI output fails
- Image: assets/pic6.jpg or assets/pic3b.jpg (error/debug UI, if available)

Slide 8: Responsible AI Reflection
- Limitations / biases:
  - AI suggestions depend on the prompt and can reflect generic pet care assumptions
  - Recommendation quality may vary for unusual pets or rare care needs
- Misuse and prevention:
  - Misuse risk: users may blindly accept AI tasks without vet review
  - Prevention: keep human in the loop, verify with pet health professionals, provide clear user control
- Reliability insight:
  - What surprised me: AI output may be wrapped in markdown or cut off, requiring robust parsing
  - What improved reliability: recovery logic, prompt simplification, and strict validation

Slide 9: Collaboration with AI
- Describe how AI helped:
  - Helpful suggestion: AI helped generate the initial task recommendation design and candidate prompt structure
  - Flawed suggestion: AI output sometimes included markdown formatting or incomplete JSON, which required manual debugging
- Emphasize active collaboration:
  - AI was used as a development partner, not a final authority
  - Human review was necessary to implement reliable parsing and error handling

Slide 10: Summary and Next Steps
- Recap the project:
  - Base project: pet care scheduler with recurrence and conflict detection
  - Extension: AI-powered personalized task recommendations with Gemini 2.5 Flash
  - Reliability: JSON parsing guards, error fallback, persistence, and test coverage
- Suggested next improvements:
  - Add multi-pet scheduling aggregation
  - Add user-specific health rules or medication reminders
  - Add richer UI for AI explanation and user feedback
- Closing image: assets/uml_final.jpg or assets/pic1.jpg
