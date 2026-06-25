"""
ToDoList.py  —  CLI frontend + shared backend logic
====================================================
Run directly for the terminal interface:
    python ToDoList.py

Imported by app.py for the GUI interface.
All data/DSA logic lives here; CLI code is inside  if __name__ == "__main__"
so it never runs when imported.
"""

import datetime
import os

# ─────────────────────────────────────────────────────────────────────────────
#  Optional colour support (colorama)
# ─────────────────────────────────────────────────────────────────────────────
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = BLUE = WHITE = ""
    class Style:
        BRIGHT = RESET_ALL = DIM = ""

# ─────────────────────────────────────────────────────────────────────────────
#  Optional voice (pyttsx3)  — used by CLI only
# ─────────────────────────────────────────────────────────────────────────────
def speak(text):
    """Print + speak text (CLI use only)."""
    print(text)
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        pass   # speech is optional; never crash because of it


# ─────────────────────────────────────────────────────────────────────────────
#  DSA: Node  +  Singly Linked List
# ─────────────────────────────────────────────────────────────────────────────
class Node:
    """One node in the linked list — holds one task dict."""
    def __init__(self, task_dict):
        self.data = task_dict
        self.next = None


class TaskLinkedList:
    """
    Singly Linked List for task storage.
    Insertion/deletion avoids array-shifting — O(n) traversal,
    O(1) structural change once the position is found.
    """
    def __init__(self):
        self.head = None
        self.size = 0

    # O(n) — walks to tail
    def append(self, task_dict):
        node = Node(task_dict)
        if not self.head:
            self.head = node
        else:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = node
        self.size += 1

    # O(n)
    def to_list(self):
        result, cur = [], self.head
        while cur:
            result.append(cur.data)
            cur = cur.next
        return result

    # O(n)
    def from_list(self, lst):
        self.head = None
        self.size = 0
        for item in lst:
            self.append(item)

    # O(n)
    def delete_at(self, index):
        if index < 0 or index >= self.size:
            return None
        if index == 0:
            data = self.head.data
            self.head = self.head.next
            self.size -= 1
            return data
        cur = self.head
        for _ in range(index - 1):
            cur = cur.next
        data = cur.next.data
        cur.next = cur.next.next
        self.size -= 1
        return data

    # O(n)
    def get_at(self, index):
        cur = self.head
        for _ in range(index):
            if cur is None:
                return None
            cur = cur.next
        return cur.data if cur else None

    # O(n)
    def update_at(self, index, new_data):
        cur = self.head
        for _ in range(index):
            if cur is None:
                return
            cur = cur.next
        if cur:
            cur.data = new_data

    def __len__(self):
        return self.size


# ─────────────────────────────────────────────────────────────────────────────
#  DSA: Merge Sort  —  sort by due date   O(n log n)
# ─────────────────────────────────────────────────────────────────────────────
def merge_sort_by_due(lst):
    """Stable sort by due date.  Time O(n log n), Space O(n)."""
    if len(lst) <= 1:
        return lst
    mid   = len(lst) // 2
    left  = merge_sort_by_due(lst[:mid])
    right = merge_sort_by_due(lst[mid:])
    return _merge(left, right)

def _merge(left, right):
    result, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        try:
            dl = datetime.date.fromisoformat(left[i]["due"])
        except ValueError:
            dl = datetime.date.max
        try:
            dr = datetime.date.fromisoformat(right[j]["due"])
        except ValueError:
            dr = datetime.date.max
        if dl <= dr:
            result.append(left[i]);  i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  DSA: Bubble Sort  —  sort by priority   O(n²)
# ─────────────────────────────────────────────────────────────────────────────
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

def bubble_sort_by_priority(lst):
    """
    Bubble Sort: High → Medium → Low.
    Time O(n²), Space O(1).
    Good choice here because n is tiny and it is easy to trace/explain.
    """
    lst = lst[:]
    n = len(lst)
    for i in range(n):
        for j in range(n - i - 1):
            p1 = PRIORITY_ORDER.get(lst[j]["priority"].lower(), 3)
            p2 = PRIORITY_ORDER.get(lst[j+1]["priority"].lower(), 3)
            if p1 > p2:
                lst[j], lst[j+1] = lst[j+1], lst[j]
    return lst


# ─────────────────────────────────────────────────────────────────────────────
#  DSA: Linear Search  —  O(n)
# ─────────────────────────────────────────────────────────────────────────────
def linear_search(lst, keyword):
    """
    Scan every task for keyword in name, priority or due-date field.
    Time O(n).
    """
    kw = keyword.lower()
    return [t for t in lst
            if kw in t["task"].lower()
            or kw in t["priority"].lower()
            or kw in t["due"].lower()]


# ─────────────────────────────────────────────────────────────────────────────
#  Validation helpers  (used by both CLI and GUI)
# ─────────────────────────────────────────────────────────────────────────────
def validate_date(date_str):
    try:
        datetime.date.fromisoformat(date_str)
        return True
    except ValueError:
        return False

def validate_priority(p):
    return p.strip().lower() in ("high", "medium", "low")


# ─────────────────────────────────────────────────────────────────────────────
#  File I/O  (shared by CLI and GUI — same tasks.txt)
# ─────────────────────────────────────────────────────────────────────────────
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
                    "task":     task.strip(),
                    "done":     done.strip().lower() == "true",
                    "priority": priority.strip(),
                    "due":      due.strip()
                })
    except FileNotFoundError:
        pass
    return tasks

def save_tasks(tasks):
    with open(FILE, "w") as f:
        for t in tasks.to_list():
            f.write(f"{t['task']} | {t['done']} | {t['priority']} | {t['due']}\n")


# ─────────────────────────────────────────────────────────────────────────────
#  CLI helpers
# ─────────────────────────────────────────────────────────────────────────────
def _header(text):
    return f"{Fore.MAGENTA}{Style.BRIGHT}{text}{Style.RESET_ALL}"

def _priority_color(priority, text):
    p = priority.lower()
    if p == "high":   return f"{Fore.RED}{Style.BRIGHT}{text}{Style.RESET_ALL}"
    if p == "medium": return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"
    if p == "low":    return f"{Fore.GREEN}{text}{Style.RESET_ALL}"
    return text

def _input_date(prompt="Due (YYYY-MM-DD): "):
    while True:
        d = input(prompt).strip()
        if validate_date(d):
            return d
        speak("Invalid date. Use YYYY-MM-DD.")

def _input_priority(prompt="Priority (High/Medium/Low): "):
    while True:
        p = input(prompt).strip().capitalize()
        if validate_priority(p):
            return p
        speak("Invalid priority. Choose High, Medium, or Low.")

def _show_tasks(lst):
    if not lst:
        speak("No tasks to show.")
        return
    today = datetime.date.today().isoformat()
    print(_header(f"\n {'─'*52}"))
    for i, t in enumerate(lst, 1):
        status = f"{Fore.CYAN}✔ Done{Style.RESET_ALL}" if t["done"] \
                 else f"{Fore.WHITE}✘ Pending{Style.RESET_ALL}"
        pri    = _priority_color(t["priority"], t["priority"])
        due    = t["due"]
        try:
            d = datetime.date.fromisoformat(t["due"])
            if not t["done"] and d < datetime.date.today():
                due = f"{Fore.RED}⚠ {t['due']} OVERDUE{Style.RESET_ALL}"
            elif t["due"] == today:
                due = f"{Fore.YELLOW}★ {t['due']} TODAY{Style.RESET_ALL}"
        except ValueError:
            pass
        print(f"  {i}. {Style.BRIGHT}{t['task']}{Style.RESET_ALL} "
              f"| {status} | Priority: {pri} | Due: {due}")
    print(_header(f" {'─'*52}"))


# ─────────────────────────────────────────────────────────────────────────────
#  CLI actions
# ─────────────────────────────────────────────────────────────────────────────
def _add_task(tasks):
    task = input("Task name: ").strip()
    if not task:
        speak("Task name cannot be empty.")
        return
    priority = _input_priority()
    due      = _input_date()
    tasks.append({"task": task, "done": False, "priority": priority, "due": due})
    speak(f"Task '{task}' added.")

def _complete_task(tasks):
    lst = tasks.to_list()
    _show_tasks(lst)
    if not lst: return
    try:
        n = int(input("Task number to mark done: "))
        if 1 <= n <= len(lst):
            t = tasks.get_at(n - 1)
            t["done"] = True
            tasks.update_at(n - 1, t)
            speak(f"'{t['task']}' marked as done.")
        else:
            speak("Invalid number.")
    except ValueError:
        speak("Enter a valid number.")

def _delete_task(tasks):
    lst = tasks.to_list()
    _show_tasks(lst)
    if not lst: return
    try:
        n = int(input("Task number to delete: "))
        if 1 <= n <= len(lst):
            deleted = tasks.delete_at(n - 1)
            speak(f"Deleted: '{deleted['task']}'")
        else:
            speak("Invalid number.")
    except ValueError:
        speak("Enter a valid number.")

def _edit_task(tasks):
    lst = tasks.to_list()
    _show_tasks(lst)
    if not lst: return
    try:
        n = int(input("Task number to edit: "))
        if not (1 <= n <= len(lst)):
            speak("Invalid number."); return
    except ValueError:
        speak("Enter a valid number."); return

    t = tasks.get_at(n - 1)
    print(f"\nEditing: {Style.BRIGHT}{t['task']}{Style.RESET_ALL}")
    print("(Press Enter to keep current value)\n")

    new_name = input(f"New name [{t['task']}]: ").strip()
    new_pri  = input(f"New priority [{t['priority']}] (High/Medium/Low): ").strip().capitalize()
    new_due  = input(f"New due date [{t['due']}] (YYYY-MM-DD): ").strip()

    if new_name:                              t["task"]     = new_name
    if new_pri  and validate_priority(new_pri): t["priority"] = new_pri
    elif new_pri: speak("Invalid priority — kept old value.")
    if new_due  and validate_date(new_due):   t["due"]      = new_due
    elif new_due: speak("Invalid date — kept old value.")

    tasks.update_at(n - 1, t)
    speak("Task updated.")

def _search_tasks(tasks):
    kw = input("Search keyword: ").strip()
    if not kw: speak("Keyword cannot be empty."); return
    results = linear_search(tasks.to_list(), kw)
    if results:
        print(_header(f"\nFound {len(results)} result(s) for '{kw}':"))
        _show_tasks(results)
    else:
        speak(f"No tasks match '{kw}'.")

def _sort_tasks(tasks):
    print(_header("\n── Sort Tasks ──"))
    print("  1. By Priority   (Bubble Sort — O(n²))")
    print("  2. By Due Date   (Merge Sort  — O(n log n))")
    choice = input("Choose: ").strip()
    lst = tasks.to_list()
    if choice == "1":
        tasks.from_list(bubble_sort_by_priority(lst))
        speak("Sorted by priority (Bubble Sort).")
        _show_tasks(tasks.to_list())
    elif choice == "2":
        tasks.from_list(merge_sort_by_due(lst))
        speak("Sorted by due date (Merge Sort).")
        _show_tasks(tasks.to_list())
    else:
        speak("Invalid choice.")

def _filter_tasks(tasks, mode):
    lst   = tasks.to_list()
    today = datetime.date.today().isoformat()
    if not lst: speak("No tasks. Add some first."); return
    print(_header(f"\n── {mode} ──"))
    out = []
    for t in lst:
        if   mode == "Completed"  and t["done"]:               out.append(t)
        elif mode == "Incomplete" and not t["done"]:            out.append(t)
        elif mode == "Due Today"  and t["due"] == today:        out.append(t)
        elif mode == "Overdue":
            try:
                if datetime.date.fromisoformat(t["due"]) < datetime.date.today() \
                        and not t["done"]:
                    out.append(t)
            except ValueError:
                pass
    _show_tasks(out) if out else speak("No matching tasks.")

def _filter_by_priority(tasks):
    lst = tasks.to_list()
    if not lst: speak("No tasks. Add some first."); return
    p = _input_priority()
    out = [t for t in lst if t["priority"].lower() == p.lower()]
    _show_tasks(out) if out else speak(f"No {p} priority tasks.")

def _stats(tasks):
    lst   = tasks.to_list()
    total = len(lst)
    if not total: speak("No tasks available."); return
    done    = sum(1 for t in lst if t["done"])
    pending = total - done
    today   = datetime.date.today()
    overdue = due_today = high = medium = low = 0
    for t in lst:
        p = t["priority"].lower()
        if p == "high":   high   += 1
        elif p == "medium": medium += 1
        elif p == "low":  low    += 1
        try:
            d = datetime.date.fromisoformat(t["due"])
            if not t["done"] and d < today: overdue   += 1
            if d == today:                  due_today += 1
        except ValueError: pass

    bar   = lambda n, tot: "█" * n + "░" * (tot - n)
    pct   = done / total * 100
    print(f"\n  {Style.BRIGHT}Total   :{Style.RESET_ALL} {total}")
    print(f"  {Fore.CYAN}Done    :{Style.RESET_ALL} {done}  {Fore.CYAN}{bar(done, total)[:20]}{Style.RESET_ALL}  {pct:.0f}%")
    print(f"  {Fore.WHITE}Pending :{Style.RESET_ALL} {pending}")
    print(f"  {Fore.RED}Overdue :{Style.RESET_ALL} {overdue}")
    print(f"  {Fore.YELLOW}Today   :{Style.RESET_ALL} {due_today}")
    print(f"\n  {Fore.RED}High    :{Style.RESET_ALL} {high}   {Fore.RED}{'█'*high}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}Medium  :{Style.RESET_ALL} {medium}   {Fore.YELLOW}{'█'*medium}{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}Low     :{Style.RESET_ALL} {low}   {Fore.GREEN}{'█'*low}{Style.RESET_ALL}\n")
    speak(f"{total} tasks. {done} done, {pending} pending, {overdue} overdue.")


# ─────────────────────────────────────────────────────────────────────────────
#  CLI entry point  — only runs when executed directly, NOT when imported
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        import pyfiglet
        HAS_FIGLET = True
    except ImportError:
        HAS_FIGLET = False

    tasks = load_tasks()
    os.system("cls" if os.name == "nt" else "clear")

    if HAS_FIGLET:
        print(f"{Fore.CYAN}{Style.BRIGHT}{pyfiglet.figlet_format('To-Do List', font='slant')}{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}{Style.BRIGHT}=== To-Do List ==={Style.RESET_ALL}\n")

    speak("Welcome to the To-Do List.")

    while True:
        print(_header("\n ════════════ MENU ════════════"))
        options = [
            (" 1", "Add Task"),
            (" 2", "View All Tasks"),
            (" 3", "Mark Task as Done"),
            (" 4", "Delete Task"),
            (" 5", "Edit Task"),
            (" 6", f"Search Tasks          {Style.DIM}[Linear Search O(n)]{Style.RESET_ALL}"),
            (" 7", f"Sort Tasks            {Style.DIM}[Bubble Sort / Merge Sort]{Style.RESET_ALL}"),
            (" 8", "View Completed"),
            (" 9", "View Incomplete"),
            ("10", "View by Priority"),
            ("11", "View Due Today"),
            ("12", "View Overdue"),
            ("13", "Stats Dashboard"),
            ("14", "Save Tasks"),
            (" 0", "Save & Exit"),
        ]
        for num, label in options:
            color = Fore.RED if num.strip() == "0" else Fore.CYAN
            print(f"  {color}{num}.{Style.RESET_ALL} {label}")
        print(_header(" ══════════════════════════════"))

        choice = input("\nChoose option: ").strip()
        if   choice == "1":  _add_task(tasks)
        elif choice == "2":  _show_tasks(tasks.to_list())
        elif choice == "3":  _complete_task(tasks)
        elif choice == "4":  _delete_task(tasks)
        elif choice == "5":  _edit_task(tasks)
        elif choice == "6":  _search_tasks(tasks)
        elif choice == "7":  _sort_tasks(tasks)
        elif choice == "8":  _filter_tasks(tasks, "Completed")
        elif choice == "9":  _filter_tasks(tasks, "Incomplete")
        elif choice == "10": _filter_by_priority(tasks)
        elif choice == "11": _filter_tasks(tasks, "Due Today")
        elif choice == "12": _filter_tasks(tasks, "Overdue")
        elif choice == "13": _stats(tasks)
        elif choice == "14":
            save_tasks(tasks)
            speak("Tasks saved.")
        elif choice == "0":
            save_tasks(tasks)
            if HAS_FIGLET:
                print(f"{Fore.CYAN}{Style.BRIGHT}"
                      f"{pyfiglet.figlet_format('Good Bye!', font='slant')}"
                      f"{Style.RESET_ALL}")
            speak("Goodbye! Have a nice day.")
            break
        else:
            speak("Invalid choice.")