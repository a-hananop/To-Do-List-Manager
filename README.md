# To-Do-List-Manager
A simple and interactive command-line To-Do List Manager built with Python to help you organize and keep track of your tasks efficiently.
 
## Features
- **Add new tasks** with details including:
  - Task description
  - Priority level (High / Medium / Low)
  - Due date (YYYY-MM-DD format)
- **View all tasks** in a clear, numbered list.
- **Mark tasks as completed** or incomplete.
- **Delete tasks** you no longer need.
- **Filter tasks** by:
  - Completion status (Completed / Incomplete)
  - Priority level
  - Tasks due today
  - Overdue tasks
- **Persistent storage** of tasks in a simple text file (`tasks.txt`).
- **Audio feedback** using text-to-speech (`pyttsx3`).
- Stylish command-line interface with ASCII art headings using `pyfiglet`.

## Installation
1. Clone the repository or download the script.
2. Make sure you have Python installed (version 3.6 or higher recommended).
3. Install the required Python packages:
   ```bash
   pip install pyttsx3 pyfiglet
