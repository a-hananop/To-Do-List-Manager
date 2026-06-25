import datetime 
import pyttsx3 
import pyfiglet

# Initialize the voice engine
def speak(text):
    print(text)
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"Speech error: {e}")


file = "tasks.txt"

# Function to load tasks from the file 
def load_tasks():
    tasks = []
    try:
        with open(file, "r") as f:
            for line in f:
                task, done, priority, due = line.strip().split("|")
                tasks.append({
                    "task": task.strip(),
                    "done": done.strip().lower() == "true",
                    "priority": priority.strip(),
                    "due": due.strip()
                })
    except FileNotFoundError:
        pass
    return tasks 

# Function to save tasks to file
def save_tasks(tasks):
    with open(file, "w") as f:
        for t in tasks:
            f.write(f"{t['task']} | {t['done']} | {t['priority']} | {t['due']}\n")

# Function to display all tasks in a numbered list 
def show_tasks(tasks):
    if not tasks:
        speak("No tasks.")
        return
    for i, t in enumerate(tasks, start=1):
        status = "Completed" if t["done"] else "Not Completed"
        print(f"{i}. {t['task']} | {status} | Priority: {t['priority']} | Due: {t['due']}")

# Function to add a new task  
def add_task(tasks):
    task = input("Task: ").strip()
    priority = input("Priority (High/Medium/Low): ").capitalize().strip()
    due = input("Due (YYYY-MM-DD): ").strip()
    tasks.append({"task": task, "done": False, "priority": priority, "due": due})
    speak("Task added")

# Function to mark a task as done 
def complete_task(tasks):
    show_tasks(tasks)
    try:
        num = int(input("Task number to mark done: "))
        if 1 <= num <= len(tasks):
            tasks[num-1]["done"] = True
            speak("Marked as done")
        else:
            speak("Invalid number.")
    except:
        speak("Invalid input.")

# Function to delete a task 
def delete_task(tasks):
    show_tasks(tasks)
    try:
        num = int(input("Task number to delete: "))
        if 1 <= num <= len(tasks):
            deleted = tasks.pop(num-1)
            speak(f"Deleted: {deleted['task']}")
        else:
            speak("Invalid number.")
    except:
        speak("Invalid input.")

# Function to filter tasks by type
def filter_tasks(tasks, filter_type):
    if not tasks:
        speak("No tasks found. Please add some first.")
        return 

    today = datetime.date.today().isoformat()
    print(f"\n ----- {filter_type} ----- ")
    found = False

    for t in tasks:
        show = False
        if filter_type == "Completed" and t["done"]:
            show = True
        elif filter_type == "Incomplete" and not t["done"]:
            show = True 
        elif filter_type == "Due Today" and t["due"] == today:
            show = True 
        elif filter_type == "Overdue":
            try:
                due_date = datetime.date.fromisoformat(t["due"])
                if due_date < datetime.date.today() and not t["done"]:
                    show = True 
            except ValueError:
                continue
        
        if show:
            found = True
            status = "Completed" if t["done"] else "Not Completed"
            print(f"{t['task']} | {status} | Priority: {t['priority']} | Due: {t['due']}")

    if not found:
        speak("No matching tasks found.")

# Function to display tasks filtered by a specific priority level 
def filter_by_priority(tasks):
    if not tasks:
        speak("No tasks found. Please add some first.")
        return
    p = input("Priority to filter (High/Medium/Low): ").strip().capitalize()
    print(f"----- Tasks with {p} Priority -----")
    found = False
    for t in tasks:
        if t["priority"].lower() == p.lower():
            found = True
            status = "Completed" if t["done"] else "Not Completed"
            print(f"{t['task']} | {status} | Due: {t['due']}")
    if not found:
        speak("No tasks with this priority.")

tasks = load_tasks()

out = "Welcome to the To-Do List"
print(pyfiglet.figlet_format(out))
speak(out)

speak("Please choose an option by typing the number.")

while True:
    print("\n ===== To-Do List ===== ")
    print("1. Add Task ")
    print("2. View All Tasks ")
    print("3. Mark Task as Done ")
    print("4. Delete Task ")
    print("5. View Completed Tasks ")
    print("6. View Incomplete Task ")
    print("7. View Tasks by Priority ")
    print("8. View Tasks Due Today ")
    print("9. View Overdue Tasks ")
    print("11. Save Tasks ")
    print("0. Save and Exit ")
    print()

    choice = input("Choose the option: ").strip()

    if choice == "1":
        add_task(tasks)
    elif choice == "2":
        show_tasks(tasks)
    elif choice == "3":
        complete_task(tasks)
    elif choice == "4":
        delete_task(tasks)
    elif choice == "5":
        filter_tasks(tasks, "Completed")
    elif choice == "6":
        filter_tasks(tasks, "Incomplete")
    elif choice == "7":
        filter_by_priority(tasks)
    elif choice == "8":
        filter_tasks(tasks, "Due Today")
    elif choice == "9":
        filter_tasks(tasks, "Overdue")
    elif choice == "11":
        save_tasks(tasks)
        speak("Task saved successfully.")
    elif choice == "0":
        save_tasks(tasks)
        message = "Good Bye! Have a nice day."
        print(pyfiglet.figlet_format(message))  
        speak(message)
        break
    else:
        speak("Invalid choice.")
