import datetime
import pyttsx3
import pyfiglet
import os

# ─────────────────────────────────────────────
#  Try to import colorama for colored terminal output
# ─────────────────────────────────────────────
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLOR = True
except ImportError:
    COLOR = False
    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = BLUE = WHITE = ""
    class Style:
        BRIGHT = RESET_ALL = DIM = ""

# ─────────────────────────────────────────────
#  DSA: Node class for Singly Linked List
# ─────────────────────────────────────────────
class Node:
    """A single node in the linked list. Each node holds one task."""
    def __init__(self, task_dict):
        self.data = task_dict   # The task dictionary
        self.next = None        # Pointer to the next node


# ─────────────────────────────────────────────
#  DSA: Singly Linked List to manage tasks
# ─────────────────────────────────────────────
class TaskLinkedList:
    """
    Singly Linked List — tasks are nodes chained together.
    This is more memory-efficient for dynamic insertion/deletion
    compared to a plain Python list (no shifting needed).
    """
    def __init__(self):
        self.head = None
        self.size = 0

    def append(self, task_dict):
        """Add a new task node at the end — O(n)."""
        new_node = Node(task_dict)
        if not self.head:
            self.head = new_node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node
        self.size += 1

    def to_list(self):
        """Convert linked list to a plain Python list — O(n)."""
        result = []
        current = self.head
        while current:
            result.append(current.data)
            current = current.next
        return result

    def from_list(self, lst):
        """Rebuild linked list from a plain Python list — O(n)."""
        self.head = None
        self.size = 0
        for item in lst:
            self.append(item)

    def delete_at(self, index):
        """Delete node at given 0-based index — O(n)."""
        if index < 0 or index >= self.size:
            return None
        if index == 0:
            deleted = self.head.data
            self.head = self.head.next
            self.size -= 1
            return deleted
        current = self.head
        for _ in range(index - 1):
            current = current.next
        deleted = current.next.data
        current.next = current.next.next
        self.size -= 1
        return deleted

    def get_at(self, index):
        """Get task at 0-based index — O(n)."""
        current = self.head
        for _ in range(index):
            current = current.next
        return current.data if current else None

    def update_at(self, index, new_data):
        """Update task data at 0-based index — O(n)."""
        current = self.head
        for _ in range(index):
            current = current.next
        if current:
            current.data = new_data

    def __len__(self):
        return self.size


# ─────────────────────────────────────────────
#  DSA: Merge Sort — sort by due date (stable, O(n log n))
# ─────────────────────────────────────────────
def merge_sort_by_due(lst):
    """
    Merge Sort on a Python list of task dicts, sorted by due date.
    Time: O(n log n) | Space: O(n)
    """
    if len(lst) <= 1:
        return lst
    mid = len(lst) // 2
    left = merge_sort_by_due(lst[:mid])
    right = merge_sort_by_due(lst[mid:])
    return _merge(left, right)

def _merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        try:
            d_left = datetime.date.fromisoformat(left[i]["due"])
        except ValueError:
            d_left = datetime.date.max
        try:
            d_right = datetime.date.fromisoformat(right[j]["due"])
        except ValueError:
            d_right = datetime.date.max
        if d_left <= d_right:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


# ─────────────────────────────────────────────
#  DSA: Bubble Sort — sort by priority (O(n²), simple & educational)
# ─────────────────────────────────────────────
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

def bubble_sort_by_priority(lst):
    """
    Bubble Sort by priority: High → Medium → Low.
    Time: O(n²) | Space: O(1)
    Chosen here because it's easy to trace and n is small.
    """
    lst = lst[:]
    n = len(lst)
    for i in range(n):
        for j in range(0, n - i - 1):
            p1 = PRIORITY_ORDER.get(lst[j]["priority"].lower(), 3)
            p2 = PRIORITY_ORDER.get(lst[j+1]["priority"].lower(), 3)
            if p1 > p2:
                lst[j], lst[j+1] = lst[j+1], lst[j]
    return lst


# ─────────────────────────────────────────────
#  DSA: Linear Search — search by keyword (O(n))
# ─────────────────────────────────────────────
def linear_search(lst, keyword):
    """
    Linear Search through all tasks for a keyword match.
    Time: O(n) | Searches task name, priority, and due date fields.
    """
    keyword = keyword.lower()
    return [t for t in lst if keyword in t["task"].lower()
            or keyword in t["priority"].lower()
            or keyword in t["due"].lower()]


# ─────────────────────────────────────────────
#  Voice Engine
# ─────────────────────────────────────────────
def speak(text):
    print(text)
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"Speech error: {e}")


# ─────────────────────────────────────────────
#  File I/O
# ─────────────────────────────────────────────
FILE = "tasks.txt"

def load_tasks():
    tasks = TaskLinkedList()
    try:
        with open(FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) != 4:
                    continue
                task, done, priority, due = parts
                tasks.append({
                    "task": task.strip(),
                    "done": done.strip().lower() == "true",
                    "priority": priority.strip(),
                    "due": due.strip()
                })
    except FileNotFoundError:
        pass
    return tasks

def save_tasks(tasks):
    lst = tasks.to_list()
    with open(FILE, "w") as f:
        for t in lst:
            f.write(f"{t['task']} | {t['done']} | {t['priority']} | {t['due']}\n")


# ─────────────────────────────────────────────
#  Helpers: colors & validation
# ─────────────────────────────────────────────
def priority_color(priority, text):
    p = priority.lower()
    if p == "high":
        return f"{Fore.RED}{Style.BRIGHT}{text}{Style.RESET_ALL}"
    elif p == "medium":
        return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"
    elif p == "low":
        return f"{Fore.GREEN}{text}{Style.RESET_ALL}"
    return text

def done_color(text):
    return f"{Fore.CYAN}{text}{Style.RESET_ALL}"

def header(text):
    return f"{Fore.MAGENTA}{Style.BRIGHT}{text}{Style.RESET_ALL}"

def validate_date(date_str):
    try:
        datetime.date.fromisoformat(date_str)
        return True
    except ValueError:
        return False

def validate_priority(p):
    return p.lower() in ["high", "medium", "low"]

def input_date(prompt="Due (YYYY-MM-DD): "):
    while True:
        d = input(prompt).strip()
        if validate_date(d):
            return d
        speak("Invalid date format. Use YYYY-MM-DD.")

def input_priority(prompt="Priority (High/Medium/Low): "):
    while True:
        p = input(prompt).strip().capitalize()
        if validate_priority(p):
            return p
        speak("Invalid priority. Choose High, Medium, or Low.")


# ─────────────────────────────────────────────
#  Display
# ─────────────────────────────────────────────
def format_task_row(i, t, show_index=True):
    status = done_color("✔ Done") if t["done"] else f"{Fore.WHITE}✘ Pending{Style.RESET_ALL}"
    pri = priority_color(t["priority"], t["priority"])
    today = datetime.date.today().isoformat()
    due_display = t["due"]
    try:
        due_date = datetime.date.fromisoformat(t["due"])
        if not t["done"] and due_date < datetime.date.today():
            due_display = f"{Fore.RED}⚠ {t['due']} OVERDUE{Style.RESET_ALL}"
        elif t["due"] == today:
            due_display = f"{Fore.YELLOW}★ {t['due']} TODAY{Style.RESET_ALL}"
    except ValueError:
        pass
    prefix = f"{i}. " if show_index else "   "
    print(f"{prefix}{Style.BRIGHT}{t['task']}{Style.RESET_ALL} | {status} | Priority: {pri} | Due: {due_display}")

def show_tasks(tasks, task_list=None):
    lst = task_list if task_list is not None else tasks.to_list()
    if not lst:
        speak("No tasks to show.")
        return
    print(header(f"\n {'─'*50}"))
    for i, t in enumerate(lst, start=1):
        format_task_row(i, t)
    print(header(f" {'─'*50}"))


# ─────────────────────────────────────────────
#  Core Features
# ─────────────────────────────────────────────
def add_task(tasks):
    print(header("\n── Add New Task ──"))
    task = input("Task name: ").strip()
    if not task:
        speak("Task name cannot be empty.")
        return
    priority = input_priority()
    due = input_date()
    tasks.append({"task": task, "done": False, "priority": priority, "due": due})
    speak(f"Task '{task}' added successfully.")

def complete_task(tasks):
    print(header("\n── Mark Task as Done ──"))
    lst = tasks.to_list()
    show_tasks(tasks, lst)
    if not lst:
        return
    try:
        num = int(input("Task number to mark done: "))
        if 1 <= num <= len(lst):
            t = tasks.get_at(num - 1)
            t["done"] = True
            tasks.update_at(num - 1, t)
            speak(f"'{t['task']}' marked as done.")
        else:
            speak("Invalid number.")
    except ValueError:
        speak("Please enter a valid number.")

def delete_task(tasks):
    print(header("\n── Delete Task ──"))
    lst = tasks.to_list()
    show_tasks(tasks, lst)
    if not lst:
        return
    try:
        num = int(input("Task number to delete: "))
        if 1 <= num <= len(lst):
            deleted = tasks.delete_at(num - 1)
            speak(f"Deleted: '{deleted['task']}'")
        else:
            speak("Invalid number.")
    except ValueError:
        speak("Please enter a valid number.")

def edit_task(tasks):
    print(header("\n── Edit Task ──"))
    lst = tasks.to_list()
    show_tasks(tasks, lst)
    if not lst:
        return
    try:
        num = int(input("Task number to edit: "))
        if not (1 <= num <= len(lst)):
            speak("Invalid number.")
            return
    except ValueError:
        speak("Please enter a valid number.")
        return

    t = tasks.get_at(num - 1)
    print(f"\nEditing: {Style.BRIGHT}{t['task']}{Style.RESET_ALL}")
    print("(Press Enter to keep current value)\n")

    new_name = input(f"New name [{t['task']}]: ").strip()
    new_priority = input(f"New priority [{t['priority']}] (High/Medium/Low): ").strip().capitalize()
    new_due = input(f"New due date [{t['due']}] (YYYY-MM-DD): ").strip()

    if new_name:
        t["task"] = new_name
    if new_priority and validate_priority(new_priority):
        t["priority"] = new_priority
    elif new_priority:
        speak("Invalid priority — keeping old value.")
    if new_due and validate_date(new_due):
        t["due"] = new_due
    elif new_due:
        speak("Invalid date — keeping old value.")

    tasks.update_at(num - 1, t)
    speak("Task updated successfully.")

def search_tasks(tasks):
    """DSA: Linear Search — O(n)"""
    print(header("\n── Search Tasks (Linear Search) ──"))
    keyword = input("Enter keyword to search: ").strip()
    if not keyword:
        speak("Keyword cannot be empty.")
        return
    lst = tasks.to_list()
    results = linear_search(lst, keyword)
    if results:
        print(header(f"\nFound {len(results)} result(s) for '{keyword}':"))
        show_tasks(tasks, results)
    else:
        speak(f"No tasks found matching '{keyword}'.")

def sort_tasks(tasks):
    """DSA: Bubble Sort (priority) or Merge Sort (due date)"""
    print(header("\n── Sort Tasks ──"))
    print("1. Sort by Priority   (Bubble Sort  — O(n²))")
    print("2. Sort by Due Date   (Merge Sort   — O(n log n))")
    choice = input("Choose sort type: ").strip()
    lst = tasks.to_list()

    if choice == "1":
        sorted_lst = bubble_sort_by_priority(lst)
        tasks.from_list(sorted_lst)
        speak("Tasks sorted by priority using Bubble Sort.")
        show_tasks(tasks)
    elif choice == "2":
        sorted_lst = merge_sort_by_due(lst)
        tasks.from_list(sorted_lst)
        speak("Tasks sorted by due date using Merge Sort.")
        show_tasks(tasks)
    else:
        speak("Invalid choice.")

def filter_tasks(tasks, filter_type):
    lst = tasks.to_list()
    if not lst:
        speak("No tasks found. Please add some first.")
        return

    today = datetime.date.today().isoformat()
    print(header(f"\n── {filter_type} ──"))
    filtered = []

    for t in lst:
        if filter_type == "Completed" and t["done"]:
            filtered.append(t)
        elif filter_type == "Incomplete" and not t["done"]:
            filtered.append(t)
        elif filter_type == "Due Today" and t["due"] == today:
            filtered.append(t)
        elif filter_type == "Overdue":
            try:
                due_date = datetime.date.fromisoformat(t["due"])
                if due_date < datetime.date.today() and not t["done"]:
                    filtered.append(t)
            except ValueError:
                continue

    if filtered:
        show_tasks(tasks, filtered)
    else:
        speak("No matching tasks found.")

def filter_by_priority(tasks):
    print(header("\n── Filter by Priority ──"))
    lst = tasks.to_list()
    if not lst:
        speak("No tasks found. Please add some first.")
        return
    p = input_priority()
    filtered = [t for t in lst if t["priority"].lower() == p.lower()]
    if filtered:
        show_tasks(tasks, filtered)
    else:
        speak(f"No tasks with {p} priority.")

def stats_dashboard(tasks):
    """Summary stats — O(n) traversal."""
    print(header("\n── Stats Dashboard ──"))
    lst = tasks.to_list()
    total = len(lst)
    if total == 0:
        speak("No tasks available.")
        return

    done = sum(1 for t in lst if t["done"])
    pending = total - done
    today = datetime.date.today()
    overdue = 0
    due_today = 0
    high = medium = low = 0

    for t in lst:
        p = t["priority"].lower()
        if p == "high":   high += 1
        elif p == "medium": medium += 1
        elif p == "low":  low += 1
        try:
            d = datetime.date.fromisoformat(t["due"])
            if not t["done"] and d < today:
                overdue += 1
            if d == today:
                due_today += 1
        except ValueError:
            pass

    bar_done    = "█" * done    + "░" * pending
    bar_high    = "█" * high
    bar_medium  = "█" * medium
    bar_low     = "█" * low

    print(f"\n  {Style.BRIGHT}Total Tasks   :{Style.RESET_ALL} {total}")
    print(f"  {Fore.CYAN}Completed     :{Style.RESET_ALL} {done}  {Fore.CYAN}{bar_done[:20]}{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}Pending       :{Style.RESET_ALL} {pending}")
    print(f"  {Fore.RED}Overdue       :{Style.RESET_ALL} {overdue}")
    print(f"  {Fore.YELLOW}Due Today     :{Style.RESET_ALL} {due_today}")
    print(f"\n  {Fore.RED}High Priority :{Style.RESET_ALL} {high}  {Fore.RED}{bar_high}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}Medium Priority:{Style.RESET_ALL} {medium}  {Fore.YELLOW}{bar_medium}{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}Low Priority  :{Style.RESET_ALL} {low}  {Fore.GREEN}{bar_low}{Style.RESET_ALL}")
    print()

    completion_pct = (done / total * 100) if total else 0
    speak(f"You have {total} tasks. {done} done, {pending} pending, {overdue} overdue.")
    print(f"  Completion: {completion_pct:.1f}%")


# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────
tasks = load_tasks()

os.system("cls" if os.name == "nt" else "clear")
banner = pyfiglet.figlet_format("To-Do List", font="slant")
print(f"{Fore.CYAN}{Style.BRIGHT}{banner}{Style.RESET_ALL}")
speak("Welcome to the To-Do List. Please choose an option.")

while True:
    print(header("\n ════════════ MENU ════════════"))
    print(f"  {Fore.CYAN} 1.{Style.RESET_ALL} Add Task")
    print(f"  {Fore.CYAN} 2.{Style.RESET_ALL} View All Tasks")
    print(f"  {Fore.CYAN} 3.{Style.RESET_ALL} Mark Task as Done")
    print(f"  {Fore.CYAN} 4.{Style.RESET_ALL} Delete Task")
    print(f"  {Fore.CYAN} 5.{Style.RESET_ALL} Edit Task")
    print(f"  {Fore.CYAN} 6.{Style.RESET_ALL} Search Tasks          {Style.DIM}[Linear Search — O(n)]{Style.RESET_ALL}")
    print(f"  {Fore.CYAN} 7.{Style.RESET_ALL} Sort Tasks             {Style.DIM}[Bubble Sort / Merge Sort]{Style.RESET_ALL}")
    print(f"  {Fore.CYAN} 8.{Style.RESET_ALL} View Completed Tasks")
    print(f"  {Fore.CYAN} 9.{Style.RESET_ALL} View Incomplete Tasks")
    print(f"  {Fore.CYAN}10.{Style.RESET_ALL} View by Priority")
    print(f"  {Fore.CYAN}11.{Style.RESET_ALL} View Due Today")
    print(f"  {Fore.CYAN}12.{Style.RESET_ALL} View Overdue Tasks")
    print(f"  {Fore.CYAN}13.{Style.RESET_ALL} Stats Dashboard")
    print(f"  {Fore.CYAN}14.{Style.RESET_ALL} Save Tasks")
    print(f"  {Fore.RED}  0.{Style.RESET_ALL} Save and Exit")
    print(header(" ══════════════════════════════"))

    choice = input("\nChoose option: ").strip()

    if   choice == "1":  add_task(tasks)
    elif choice == "2":  show_tasks(tasks)
    elif choice == "3":  complete_task(tasks)
    elif choice == "4":  delete_task(tasks)
    elif choice == "5":  edit_task(tasks)
    elif choice == "6":  search_tasks(tasks)
    elif choice == "7":  sort_tasks(tasks)
    elif choice == "8":  filter_tasks(tasks, "Completed")
    elif choice == "9":  filter_tasks(tasks, "Incomplete")
    elif choice == "10": filter_by_priority(tasks)
    elif choice == "11": filter_tasks(tasks, "Due Today")
    elif choice == "12": filter_tasks(tasks, "Overdue")
    elif choice == "13": stats_dashboard(tasks)
    elif choice == "14":
        save_tasks(tasks)
        speak("Tasks saved successfully.")
    elif choice == "0":
        save_tasks(tasks)
        print(f"{Fore.CYAN}{Style.BRIGHT}{pyfiglet.figlet_format('Good Bye!', font='slant')}{Style.RESET_ALL}")
        speak("Goodbye! Have a nice day.")
        break
    else:
        speak("Invalid choice. Please try again.")