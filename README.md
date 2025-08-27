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


## Usage 
Run the script using:
    
    python ToDoList.py

Follow the on-screen prompts to add, view, update, delete, or filter your tasks.
Tasks are automatically saved to tasks.txt. You can also manually save anytime using the menu option.


## How it works
On startup, the program loads existing tasks from tasks.txt if available.
You interact with the menu by entering the number of the desired action.
Tasks are stored in the format:

    task description | done (True/False) | priority | due date

The program handles invalid inputs gracefully and provides audio cues for feedback.


## Example Menu 

    ===== To-Do List =====
    1. Add Task
    2. View All Tasks
    3. Mark Task as Done
    4. Delete Task
    5. View Completed Tasks
    6. View Incomplete Tasks
    7. View Tasks by Priority
    8. View Tasks Due Today
    9. View Overdue Tasks
    11. Save Tasks
    0. Save and Exit


