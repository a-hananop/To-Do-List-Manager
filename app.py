"""
app.py  —  GUI frontend for ToDoList
=====================================
Run:   python app.py
Requires ToDoList.py in the same folder.

Layout
──────
┌─────────────────────────────────────────────────────────┐
│  HEADER  — title + live stats (Total/Done/Pending/OD)   │
├──────────────┬──────────────────────────────────────────┤
│  SIDEBAR     │  MAIN PANEL                              │
│  · Filters   │  · Search bar  (Linear Search O(n))      │
│  · Sort      │  · Scrollable task cards                 │
│  · Save      │  · + Add Task button                     │
└──────────────┴──────────────────────────────────────────┘
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import threading

# ── Backend import — safe because CLI code is inside if __name__ == "__main__"
from ToDoList import (
    TaskLinkedList,
    load_tasks, save_tasks,
    linear_search,
    bubble_sort_by_priority,
    merge_sort_by_due,
    validate_date,
    validate_priority,
)

# ── Optional voice (never blocks the GUI — always runs in a thread) ──────────
try:
    import pyttsx3
    _VOICE_OK = True
except ImportError:
    _VOICE_OK = False

def speak_async(text, enabled=True):
    if not (_VOICE_OK and enabled):
        return
    def _run():
        try:
            eng = pyttsx3.init()
            eng.say(text)
            eng.runAndWait()
            eng.stop()
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────
#  PALETTE
# ─────────────────────────────────────────────────────────────────────────────
BG         = "#0D1117"
CARD_BG    = "#161B22"
HOVER_BG   = "#21262D"
BORDER     = "#30363D"
ACCENT     = "#58A6FF"
GREEN      = "#3FB950"
RED        = "#F85149"
YELLOW     = "#D29922"
PURPLE     = "#BC8CFF"
WHITE      = "#E6EDF3"
MUTED      = "#8B949E"

FONT_TITLE = ("Segoe UI", 17, "bold")
FONT_HEAD  = ("Segoe UI", 11, "bold")
FONT_BODY  = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI",  9)

PRI_COLOR  = {"High": RED, "Medium": YELLOW, "Low": PURPLE}


# ─────────────────────────────────────────────────────────────────────────────
#  MODAL: Add / Edit task
# ─────────────────────────────────────────────────────────────────────────────
class TaskDialog(tk.Toplevel):
    """
    Blocks the parent window until the user saves or cancels.
    self.result is a task dict on success, None on cancel.
    """
    def __init__(self, parent, title="Task", task=None):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.result = None
        self.transient(parent)
        self.grab_set()

        # centre over parent
        W, H = 440, 300
        rx = parent.winfo_rootx() + (parent.winfo_width()  - W) // 2
        ry = parent.winfo_rooty() + (parent.winfo_height() - H) // 2
        self.geometry(f"{W}x{H}+{rx}+{ry}")

        self._build(task)
        self.wait_window()   # block until dialog closes

    # ── widgets ──────────────────────────────────────────────────────────────
    def _lbl(self, text):
        tk.Label(self, text=text, bg=BG, fg=MUTED,
                 font=FONT_SMALL).pack(anchor="w", padx=26, pady=(10, 2))

    def _entry(self, var, focus=False):
        e = tk.Entry(self, textvariable=var, bg=CARD_BG, fg=WHITE,
                     insertbackground=WHITE, relief="flat", font=FONT_BODY,
                     highlightthickness=1,
                     highlightbackground=BORDER, highlightcolor=ACCENT)
        e.pack(fill="x", padx=26, ipady=6)
        if focus:
            e.focus_set()
        return e

    def _build(self, task):
        tk.Label(self, text=self.title(), bg=BG, fg=WHITE,
                 font=FONT_HEAD).pack(pady=(18, 6))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=26)

        self.v_name = tk.StringVar(value=task["task"]     if task else "")
        self.v_pri  = tk.StringVar(value=task["priority"] if task else "High")
        self.v_due  = tk.StringVar(value=task["due"]      if task else
                                   datetime.date.today().isoformat())

        self._lbl("Task name")
        self._entry(self.v_name, focus=True)

        self._lbl("Priority")
        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=26, pady=(2, 0))
        for p, col in PRI_COLOR.items():
            tk.Radiobutton(row, text=p, variable=self.v_pri, value=p,
                           bg=BG, fg=col, selectcolor=CARD_BG,
                           activebackground=BG, activeforeground=col,
                           font=FONT_BODY).pack(side="left", padx=(0, 14))

        self._lbl("Due date  (YYYY-MM-DD)")
        self._entry(self.v_due)

        # buttons
        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(pady=18)
        tk.Button(btn_row, text="Cancel", bg=BORDER,  fg=MUTED,  relief="flat",
                  font=FONT_BODY, padx=18, pady=5, cursor="hand2",
                  activebackground=HOVER_BG, command=self.destroy
                  ).pack(side="left", padx=8)
        tk.Button(btn_row, text="Save",   bg=ACCENT,  fg=BG,     relief="flat",
                  font=FONT_BODY, padx=18, pady=5, cursor="hand2",
                  activebackground="#4090e0", command=self._save
                  ).pack(side="left", padx=8)

        # allow Enter key to save
        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())

    def _save(self):
        name = self.v_name.get().strip()
        pri  = self.v_pri.get().strip()
        due  = self.v_due.get().strip()
        if not name:
            messagebox.showerror("Error", "Task name cannot be empty.", parent=self)
            return
        if not validate_date(due):
            messagebox.showerror("Error", "Invalid date — use YYYY-MM-DD.", parent=self)
            return
        self.result = {"task": name, "done": False, "priority": pri, "due": due}
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
#  TASK CARD  — one row in the scrollable list
# ─────────────────────────────────────────────────────────────────────────────
class TaskCard(tk.Frame):
    """
    Displays one task.
    Callbacks receive the *real* index inside the full TaskLinkedList,
    so the app never has to do identity-matching.
    """
    def __init__(self, parent, task, real_index, on_done, on_edit, on_delete):
        super().__init__(parent, bg=CARD_BG, cursor="arrow")
        self.task       = task
        self.real_index = real_index
        self._on_done   = on_done
        self._on_edit   = on_edit
        self._on_delete = on_delete
        self._build()
        # hover: recolour the frame only (children keep their own bg)
        self.bind("<Enter>", lambda e: self.configure(bg=HOVER_BG))
        self.bind("<Leave>", lambda e: self.configure(bg=CARD_BG))

    def _due_color(self):
        if self.task["done"]:
            return MUTED
        try:
            d = datetime.date.fromisoformat(self.task["due"])
            today = datetime.date.today()
            if d < today:
                return RED
            if d == today:
                return YELLOW
        except ValueError:
            pass
        return MUTED

    def _due_label(self):
        base = f"  {self.task['due']}"
        if not self.task["done"]:
            try:
                d = datetime.date.fromisoformat(self.task["due"])
                today = datetime.date.today()
                if d < today:   base += "  ⚠ OVERDUE"
                elif d == today: base += "  ★ TODAY"
            except ValueError:
                pass
        return base

    def _build(self):
        t       = self.task
        done    = t["done"]
        pri_col = PRI_COLOR.get(t["priority"], MUTED)
        strip_c = GREEN if done else pri_col

        # left colour strip
        tk.Frame(self, bg=strip_c, width=5).pack(side="left", fill="y")

        # body
        body = tk.Frame(self, bg=CARD_BG)
        body.pack(side="left", fill="both", expand=True, padx=(10, 4), pady=8)

        name_fg   = MUTED if done else WHITE
        name_font = ("Segoe UI", 10, "overstrike") if done else FONT_BODY
        tk.Label(body, text=t["task"], bg=CARD_BG, fg=name_fg,
                 font=name_font, anchor="w").pack(fill="x")

        meta = tk.Frame(body, bg=CARD_BG)
        meta.pack(fill="x", pady=(3, 0))
        tk.Label(meta, text=f"● {t['priority']}", bg=CARD_BG,
                 fg=pri_col if not done else MUTED,
                 font=FONT_SMALL).pack(side="left", padx=(0, 14))
        tk.Label(meta, text=self._due_label(), bg=CARD_BG,
                 fg=self._due_color(), font=FONT_SMALL).pack(side="left")

        # action buttons
        btn_pane = tk.Frame(self, bg=CARD_BG)
        btn_pane.pack(side="right", padx=8)
        self._ibtn(btn_pane, "↩" if done else "✔", GREEN if not done else MUTED,
                   lambda: self._on_done(self.real_index))
        self._ibtn(btn_pane, "✎", ACCENT,
                   lambda: self._on_edit(self.real_index))
        self._ibtn(btn_pane, "✕", RED,
                   lambda: self._on_delete(self.real_index))

    def _ibtn(self, parent, text, fg, cmd):
        tk.Button(parent, text=text, fg=fg, bg=CARD_BG, relief="flat",
                  font=("Segoe UI", 11), padx=6, pady=2, cursor="hand2",
                  activebackground=HOVER_BG, activeforeground=fg,
                  command=cmd).pack(side="left", padx=2)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────────────────────────────────────
class ToDoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("To-Do List")
        self.configure(bg=BG)
        self.geometry("980x680")
        self.minsize(800, 500)

        self.tasks       = load_tasks()
        self.filter_mode = tk.StringVar(value="All")
        self.search_var  = tk.StringVar()
        self.voice_on    = tk.BooleanVar(value=True)

        self._build_ui()
        self._refresh()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        speak_async("Welcome to To-Do List.", self.voice_on.get())

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        content = tk.Frame(self, bg=BG)
        content.pack(fill="both", expand=True)
        self._build_sidebar(content)
        self._build_main(content)

    # header ──────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=CARD_BG, height=62)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="✔  To-Do List", bg=CARD_BG, fg=ACCENT,
                 font=FONT_TITLE).pack(side="left", padx=22)

        # voice toggle (right side, packed first so it stays leftmost of right)
        tk.Checkbutton(hdr, text="🔊 Voice", variable=self.voice_on,
                       bg=CARD_BG, fg=MUTED, selectcolor=CARD_BG,
                       activebackground=CARD_BG, font=FONT_SMALL
                       ).pack(side="right", padx=16)

        # stat tiles
        stats = tk.Frame(hdr, bg=CARD_BG)
        stats.pack(side="right", padx=8)
        self._lbl_total   = self._stat_tile(stats, "Total",   WHITE)
        self._lbl_done    = self._stat_tile(stats, "Done",    GREEN)
        self._lbl_pending = self._stat_tile(stats, "Pending", YELLOW)
        self._lbl_overdue = self._stat_tile(stats, "Overdue", RED)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

    def _stat_tile(self, parent, label, color):
        f = tk.Frame(parent, bg=CARD_BG)
        f.pack(side="left", padx=10)
        val = tk.Label(f, text="0", bg=CARD_BG, fg=color,
                       font=("Segoe UI", 15, "bold"))
        val.pack()
        tk.Label(f, text=label, bg=CARD_BG, fg=MUTED, font=FONT_SMALL).pack()
        return val

    # sidebar ─────────────────────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=BG, width=188)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        tk.Frame(sb, bg=BORDER, width=1).pack(side="right", fill="y")

        self._sb_head(sb, "FILTER")
        for label, value in [
            ("All Tasks",   "All"),
            ("✔  Done",     "Done"),
            ("✘  Pending",  "Pending"),
            ("★  Due Today","Today"),
            ("⚠  Overdue",  "Overdue"),
            ("●  High",     "High"),
            ("●  Medium",   "Medium"),
            ("●  Low",      "Low"),
        ]:
            self._filter_btn(sb, label, value)

        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x", padx=12, pady=8)
        self._sb_head(sb, "SORT")
        self._side_btn(sb, "Priority  (Bubble Sort)",  self._sort_priority)
        self._side_btn(sb, "Due Date  (Merge Sort)",   self._sort_due)

        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x", padx=12, pady=8)
        self._sb_head(sb, "FILE")
        self._side_btn(sb, "💾  Save Tasks", self._save)

    def _sb_head(self, parent, text):
        tk.Label(parent, text=text, bg=BG, fg=MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=16, pady=(12, 3))

    def _filter_btn(self, parent, label, value):
        def cmd():
            self.filter_mode.set(value)
            self._refresh()
        tk.Button(parent, text=label, bg=BG, fg=WHITE, relief="flat",
                  font=FONT_SMALL, anchor="w", padx=16, pady=5, cursor="hand2",
                  activebackground=HOVER_BG, activeforeground=ACCENT,
                  command=cmd).pack(fill="x")

    def _side_btn(self, parent, label, cmd):
        tk.Button(parent, text=label, bg=BG, fg=MUTED, relief="flat",
                  font=FONT_SMALL, anchor="w", padx=16, pady=4, cursor="hand2",
                  activebackground=HOVER_BG, activeforeground=WHITE,
                  command=cmd).pack(fill="x")

    # main panel ──────────────────────────────────────────────────────────────
    def _build_main(self, parent):
        main = tk.Frame(parent, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        # toolbar
        tb = tk.Frame(main, bg=BG)
        tb.pack(fill="x", padx=16, pady=10)

        sf = tk.Frame(tb, bg=CARD_BG, highlightthickness=1,
                      highlightbackground=BORDER, highlightcolor=ACCENT)
        sf.pack(side="left", fill="x", expand=True, padx=(0, 12))
        tk.Label(sf, text="🔍", bg=CARD_BG, fg=MUTED,
                 font=FONT_BODY).pack(side="left", padx=(8, 2))
        se = tk.Entry(sf, textvariable=self.search_var, bg=CARD_BG, fg=WHITE,
                      insertbackground=WHITE, relief="flat", font=FONT_BODY)
        se.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 8))
        se.bind("<KeyRelease>", lambda e: self._refresh())
        tk.Label(sf, text="Linear Search O(n)", bg=CARD_BG, fg=MUTED,
                 font=("Segoe UI", 8)).pack(side="right", padx=8)

        tk.Button(tb, text="+ Add Task", bg=ACCENT, fg=BG, font=FONT_HEAD,
                  relief="flat", padx=16, pady=6, cursor="hand2",
                  activebackground="#4090e0", command=self._add_task
                  ).pack(side="right")

        # scrollable task list
        lf = tk.Frame(main, bg=BG)
        lf.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        self._canvas = tk.Canvas(lf, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(lf, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._task_frame = tk.Frame(self._canvas, bg=BG)
        self._win_id = self._canvas.create_window(
            (0, 0), window=self._task_frame, anchor="nw")

        self._task_frame.bind("<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
            lambda e: self._canvas.itemconfig(self._win_id, width=e.width))
        self._canvas.bind_all("<MouseWheel>", self._scroll)
        self._canvas.bind_all("<Button-4>",   self._scroll)
        self._canvas.bind_all("<Button-5>",   self._scroll)

    def _scroll(self, event):
        if event.num == 4:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(1, "units")
        else:
            self._canvas.yview_scroll(int(-1 * event.delta / 120), "units")

    # ── data helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _is_overdue(t):
        try:
            return datetime.date.fromisoformat(t["due"]) < datetime.date.today()
        except ValueError:
            return False

    def _get_view(self):
        """
        Returns a list of (real_index, task_dict) tuples that match
        the current search keyword + filter mode.
        real_index is the 0-based index inside self.tasks (the linked list).
        Using real_index avoids identity-matching bugs.
        """
        full = self.tasks.to_list()          # plain list, fresh each time
        kw   = self.search_var.get().strip()
        mode = self.filter_mode.get()
        today = datetime.date.today().isoformat()

        # linear search across all tasks first
        if kw:
            matched_names = {t["task"] for t in linear_search(full, kw)}
            pairs = [(i, t) for i, t in enumerate(full) if t["task"] in matched_names]
        else:
            pairs = list(enumerate(full))

        # then filter
        if mode == "Done":
            pairs = [(i, t) for i, t in pairs if t["done"]]
        elif mode == "Pending":
            pairs = [(i, t) for i, t in pairs if not t["done"]]
        elif mode == "Today":
            pairs = [(i, t) for i, t in pairs if t["due"] == today]
        elif mode == "Overdue":
            pairs = [(i, t) for i, t in pairs if not t["done"] and self._is_overdue(t)]
        elif mode in ("High", "Medium", "Low"):
            pairs = [(i, t) for i, t in pairs if t["priority"].lower() == mode.lower()]

        return pairs

    # ── refresh ──────────────────────────────────────────────────────────────

    def _refresh(self):
        for w in self._task_frame.winfo_children():
            w.destroy()

        view = self._get_view()

        if not view:
            tk.Label(self._task_frame,
                     text="No tasks here.\nClick  + Add Task  to get started.",
                     bg=BG, fg=MUTED, font=("Segoe UI", 11),
                     justify="center").pack(pady=70)
        else:
            for real_idx, task in view:
                TaskCard(
                    self._task_frame, task, real_idx,
                    on_done=self._toggle_done,
                    on_edit=self._edit_task,
                    on_delete=self._delete_task,
                ).pack(fill="x", pady=(0, 1))
                tk.Frame(self._task_frame, bg=BORDER, height=1).pack(fill="x")

        self._update_stats()

    def _update_stats(self):
        lst     = self.tasks.to_list()
        total   = len(lst)
        done    = sum(1 for t in lst if t["done"])
        pending = total - done
        overdue = sum(1 for t in lst if not t["done"] and self._is_overdue(t))
        self._lbl_total  .config(text=str(total))
        self._lbl_done   .config(text=str(done))
        self._lbl_pending.config(text=str(pending))
        self._lbl_overdue.config(text=str(overdue))

    # ── actions ──────────────────────────────────────────────────────────────

    def _add_task(self):
        dlg = TaskDialog(self, title="Add Task")
        if dlg.result:
            self.tasks.append(dlg.result)
            self._refresh()
            speak_async(f"Task added.", self.voice_on.get())

    def _toggle_done(self, real_idx):
        t = self.tasks.get_at(real_idx)
        if t is None: return
        t["done"] = not t["done"]
        self.tasks.update_at(real_idx, t)
        status = "done" if t["done"] else "pending"
        speak_async(f"Marked as {status}.", self.voice_on.get())
        self._refresh()

    def _edit_task(self, real_idx):
        t = self.tasks.get_at(real_idx)
        if t is None: return
        dlg = TaskDialog(self, title="Edit Task", task=t)
        if dlg.result:
            dlg.result["done"] = t["done"]   # preserve done state
            self.tasks.update_at(real_idx, dlg.result)
            speak_async("Task updated.", self.voice_on.get())
            self._refresh()

    def _delete_task(self, real_idx):
        t = self.tasks.get_at(real_idx)
        if t is None: return
        if not messagebox.askyesno("Delete", f"Delete  '{t['task']}'?"):
            return
        self.tasks.delete_at(real_idx)
        speak_async("Task deleted.", self.voice_on.get())
        self._refresh()

    def _sort_priority(self):
        self.tasks.from_list(bubble_sort_by_priority(self.tasks.to_list()))
        speak_async("Sorted by priority.", self.voice_on.get())
        self._refresh()

    def _sort_due(self):
        self.tasks.from_list(merge_sort_by_due(self.tasks.to_list()))
        speak_async("Sorted by due date.", self.voice_on.get())
        self._refresh()

    def _save(self):
        save_tasks(self.tasks)
        speak_async("Saved.", self.voice_on.get())
        messagebox.showinfo("Saved", "Tasks saved to tasks.txt  ✔")

    def _on_close(self):
        save_tasks(self.tasks)
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ToDoApp().mainloop()