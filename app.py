"""
app.py  —  GUI frontend for ToDoList  (polished v3)
====================================================
Run:   python app.py
Requires ToDoList.py in the same folder.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import threading
import base64

from ToDoList import (
    TaskLinkedList, load_tasks, save_tasks,
    linear_search, bubble_sort_by_priority, merge_sort_by_due,
    validate_date, validate_priority,
)

try:
    import pyttsx3
    _VOICE_OK = True
except ImportError:
    _VOICE_OK = False

def speak_async(text, enabled=True):
    if not (_VOICE_OK and enabled): return
    def _run():
        try:
            eng = pyttsx3.init(); eng.say(text); eng.runAndWait(); eng.stop()
        except Exception: pass
    threading.Thread(target=_run, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────
#  PALETTE
# ─────────────────────────────────────────────────────────────────────────────
BG        = "#0D1117"
CARD_BG   = "#161B22"
HOVER_BG  = "#1C2128"
SIDEBAR   = "#0D1117"
BORDER    = "#21262D"
BORDER2   = "#30363D"
ACCENT    = "#58A6FF"
ACCENT2   = "#1F6FEB"
GREEN     = "#3FB950"
GREEN2    = "#196C2E"
RED       = "#F85149"
RED2      = "#6E1C19"
YELLOW    = "#D29922"
YELLOW2   = "#5A3E1B"
PURPLE    = "#BC8CFF"
PURPLE2   = "#3D1F6E"
WHITE     = "#E6EDF3"
MUTED     = "#8B949E"
MUTED2    = "#484F58"

FT  = ("Segoe UI", 16, "bold")   # title
FH  = ("Segoe UI", 10, "bold")   # heading
FB  = ("Segoe UI", 10)           # body
FS  = ("Segoe UI",  9)           # small
FSB = ("Segoe UI",  9, "bold")   # small bold
FM  = ("Consolas", 10)           # mono

PRI_FG  = {"High": RED,    "Medium": YELLOW,  "Low": PURPLE}
PRI_BG  = {"High": RED2,   "Medium": YELLOW2, "Low": PURPLE2}
PRI_DOT = {"High": "⬤",   "Medium": "⬤",    "Low": "⬤"}

# Tiny checkmark PNG embedded as base64 (16x16 blue feather / checkmark icon)
# We generate the window icon from a simple XBM pattern
ICON_XBM = """
#define icon_width 16
#define icon_height 16
static unsigned char icon_bits[] = {
   0x00, 0x00, 0x00, 0x3c, 0x00, 0x7e, 0x00, 0x66,
   0x00, 0x06, 0x18, 0x0e, 0x3c, 0x1c, 0x7e, 0x38,
   0x66, 0x70, 0x06, 0x60, 0x06, 0x60, 0x66, 0x70,
   0x7e, 0x38, 0x3c, 0x1c, 0x00, 0x00, 0x00, 0x00 };
"""


# ─────────────────────────────────────────────────────────────────────────────
#  STYLED SCROLLBAR
# ─────────────────────────────────────────────────────────────────────────────
def styled_scrollbar(parent):
    style = ttk.Style()
    style.theme_use("default")
    style.configure("Dark.Vertical.TScrollbar",
                    background=BORDER, troughcolor=BG,
                    bordercolor=BG, arrowcolor=MUTED,
                    relief="flat", borderwidth=0)
    style.map("Dark.Vertical.TScrollbar",
              background=[("active", BORDER2)])
    return ttk.Scrollbar(parent, orient="vertical",
                         style="Dark.Vertical.TScrollbar")


# ─────────────────────────────────────────────────────────────────────────────
#  ADD / EDIT DIALOG
# ─────────────────────────────────────────────────────────────────────────────
class TaskDialog(tk.Toplevel):
    def __init__(self, parent, title="Task", task=None):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.result = None
        self.transient(parent)
        self.grab_set()
        W, H = 460, 340
        rx = parent.winfo_rootx() + (parent.winfo_width()  - W) // 2
        ry = parent.winfo_rooty() + (parent.winfo_height() - H) // 2
        self.geometry(f"{W}x{H}+{rx}+{ry}")
        self._build(task)
        self.wait_window()

    def _section_label(self, text):
        tk.Label(self, text=text, bg=BG, fg=MUTED, font=FSB
                 ).pack(anchor="w", padx=28, pady=(14, 3))

    def _text_entry(self, var, focus=False):
        wrap = tk.Frame(self, bg=BORDER2, pady=1, padx=1)
        wrap.pack(fill="x", padx=28)
        e = tk.Entry(wrap, textvariable=var, bg=CARD_BG, fg=WHITE,
                     insertbackground=WHITE, relief="flat", font=FB,
                     highlightthickness=0)
        e.pack(fill="x", ipady=7, padx=2, pady=1)
        if focus: e.focus_set()
        # highlight on focus
        e.bind("<FocusIn>",  lambda ev: wrap.configure(bg=ACCENT))
        e.bind("<FocusOut>", lambda ev: wrap.configure(bg=BORDER2))
        return e

    def _build(self, task):
        # ── dialog header ──
        hdr = tk.Frame(self, bg=CARD_BG, height=48)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        icon = "✚" if "Add" in self.title() else "✎"
        tk.Label(hdr, text=f"  {icon}  {self.title()}", bg=CARD_BG,
                 fg=WHITE, font=FH).pack(side="left", padx=16)
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        self.v_name = tk.StringVar(value=task["task"]     if task else "")
        self.v_pri  = tk.StringVar(value=task["priority"] if task else "High")
        self.v_due  = tk.StringVar(value=task["due"]      if task else
                                   datetime.date.today().isoformat())

        self._section_label("TASK NAME")
        self._text_entry(self.v_name, focus=True)

        self._section_label("PRIORITY")
        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=28, pady=(0, 4))
        for p in ("High", "Medium", "Low"):
            fg = PRI_FG[p]; bg2 = PRI_BG[p]
            rb = tk.Radiobutton(row, text=f"  {p}", variable=self.v_pri,
                                value=p, bg=BG, fg=fg,
                                selectcolor=bg2, activebackground=BG,
                                activeforeground=fg, font=FSB,
                                indicatoron=False, relief="flat",
                                padx=12, pady=4, cursor="hand2",
                                bd=1, highlightthickness=1,
                                highlightbackground=BORDER2,
                                highlightcolor=fg)
            rb.pack(side="left", padx=(0, 6))

        self._section_label("DUE DATE  (YYYY-MM-DD)")
        self._text_entry(self.v_due)

        # ── footer buttons ──
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", pady=(14, 0))
        foot = tk.Frame(self, bg=CARD_BG)
        foot.pack(fill="x")
        tk.Button(foot, text="Cancel", bg=CARD_BG, fg=MUTED, relief="flat",
                  font=FB, padx=20, pady=8, cursor="hand2",
                  activebackground=HOVER_BG, activeforeground=WHITE,
                  command=self.destroy).pack(side="right", padx=(4, 16), pady=8)
        tk.Button(foot, text="  Save  ", bg=ACCENT, fg=BG, relief="flat",
                  font=FH, padx=20, pady=8, cursor="hand2",
                  activebackground=ACCENT2, activeforeground=WHITE,
                  command=self._save).pack(side="right", pady=8)

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
#  TASK CARD
# ─────────────────────────────────────────────────────────────────────────────
class TaskCard(tk.Frame):
    def __init__(self, parent, task, real_index, on_done, on_edit, on_delete):
        super().__init__(parent, bg=CARD_BG)
        self.task       = task
        self.real_index = real_index
        self._on_done   = on_done
        self._on_edit   = on_edit
        self._on_delete = on_delete
        self._build()
        self._bind_hover(self)

    # propagate hover to all children so the whole row lights up
    def _bind_hover(self, widget):
        widget.bind("<Enter>", self._enter)
        widget.bind("<Leave>", self._leave)
        for child in widget.winfo_children():
            self._bind_hover(child)

    def _enter(self, e):
        self._set_bg(self, HOVER_BG)

    def _leave(self, e):
        self._set_bg(self, CARD_BG)
        # re-apply the priority strip colour
        if hasattr(self, "_strip"):
            self._strip.configure(bg=self._strip_color())

    def _set_bg(self, widget, color):
        # skip the strip and badge frames which have their own colour
        skip_tags = getattr(self, "_skip_bg", set())
        if str(widget) not in skip_tags:
            try: widget.configure(bg=color)
            except Exception: pass
        for child in widget.winfo_children():
            self._set_bg(child, color)

    def _strip_color(self):
        return GREEN if self.task["done"] else PRI_FG.get(self.task["priority"], MUTED)

    def _due_info(self):
        t = self.task
        if t["done"]:
            return "", MUTED
        try:
            d = datetime.date.fromisoformat(t["due"])
            today = datetime.date.today()
            if d < today:   return "  ⚠ OVERDUE", RED
            if d == today:  return "  ★ TODAY",    YELLOW
        except ValueError:
            pass
        return "", MUTED

    def _build(self):
        t    = self.task
        done = t["done"]
        pri  = t["priority"]

        self._skip_bg = set()   # widgets that keep their own background

        # ── left priority strip (5 px) ────────────────────────────────────────
        self._strip = tk.Frame(self, bg=self._strip_color(), width=5)
        self._strip.pack(side="left", fill="y")
        self._skip_bg.add(str(self._strip))

        # ── body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=CARD_BG)
        body.pack(side="left", fill="both", expand=True,
                  padx=(12, 8), pady=10)

        # task name
        name_fg   = MUTED2 if done else WHITE
        name_font = ("Segoe UI", 10, "overstrike") if done else FB
        tk.Label(body, text=t["task"], bg=CARD_BG, fg=name_fg,
                 font=name_font, anchor="w").pack(fill="x")

        # meta row: priority badge + due date
        meta = tk.Frame(body, bg=CARD_BG)
        meta.pack(fill="x", pady=(5, 0))

        # priority badge (pill)
        badge_bg = GREEN2 if done else PRI_BG.get(pri, MUTED2)
        badge_fg = GREEN  if done else PRI_FG.get(pri, MUTED)
        badge_text = ("Done" if done else pri)
        badge = tk.Frame(meta, bg=badge_bg)
        badge.pack(side="left", padx=(0, 10))
        self._skip_bg.add(str(badge))
        tk.Label(badge, text=f" {badge_text} ", bg=badge_bg, fg=badge_fg,
                 font=FSB, padx=4, pady=1).pack()

        # due date
        suffix, due_col = self._due_info()
        due_text = f"  {t['due']}{suffix}"
        tk.Label(meta, text=due_text, bg=CARD_BG, fg=due_col,
                 font=FS).pack(side="left")

        # ── action buttons ────────────────────────────────────────────────────
        btn_pane = tk.Frame(self, bg=CARD_BG)
        btn_pane.pack(side="right", padx=10)

        tick_text = "↺" if done else "✓"
        tick_col  = MUTED if done else GREEN
        self._action_btn(btn_pane, tick_text, tick_col,
                         lambda: self._on_done(self.real_index))
        self._action_btn(btn_pane, "✎", ACCENT,
                         lambda: self._on_edit(self.real_index))
        self._action_btn(btn_pane, "✕", RED,
                         lambda: self._on_delete(self.real_index))

    def _action_btn(self, parent, text, fg, cmd):
        b = tk.Button(parent, text=text, fg=fg, bg=CARD_BG, relief="flat",
                      font=("Segoe UI", 12), width=2, pady=3,
                      cursor="hand2", activebackground=HOVER_BG,
                      activeforeground=fg, bd=0, command=cmd)
        b.pack(side="left", padx=2)
        self._skip_bg.discard(str(b))   # buttons recolour on hover naturally


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────────────────────────────────────
class ToDoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("To-Do List")
        self.configure(bg=BG)
        self.geometry("1020x700")
        self.minsize(820, 520)

        # set window icon using XBM (works cross-platform without .ico file)
        try:
            icon = tk.BitmapImage(data=ICON_XBM, foreground=ACCENT)
            self.iconbitmap(default="")   # clear default
            self.tk.call("wm", "iconphoto", self._w, icon)
        except Exception:
            pass

        self.tasks       = load_tasks()
        self.filter_mode = tk.StringVar(value="All")
        self.search_var  = tk.StringVar()
        self.voice_on    = tk.BooleanVar(value=True)
        self._active_filter_btn = None

        self._build_ui()
        self._refresh()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        speak_async("Welcome to To-Do List.", self.voice_on.get())

    # ─────────────────────────────────────────────────────────────────────────
    #  HEADER
    # ─────────────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=CARD_BG, height=66)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # left: logo mark + title
        left = tk.Frame(hdr, bg=CARD_BG)
        left.pack(side="left", padx=(18, 0))
        tk.Label(left, text="✔", bg=CARD_BG, fg=ACCENT,
                 font=("Segoe UI", 20, "bold")).pack(side="left", padx=(0, 8))
        tk.Label(left, text="To-Do List", bg=CARD_BG, fg=WHITE,
                 font=FT).pack(side="left")

        # right: voice toggle
        vc = tk.Checkbutton(hdr, text="Voice", variable=self.voice_on,
                            bg=CARD_BG, fg=MUTED, selectcolor=CARD_BG,
                            activebackground=CARD_BG, activeforeground=WHITE,
                            font=FS, cursor="hand2")
        vc.pack(side="right", padx=18)

        # stat tiles (right of center)
        stats_frame = tk.Frame(hdr, bg=CARD_BG)
        stats_frame.pack(side="right", padx=12)
        self._tile_total   = self._stat_tile(stats_frame, "Total",   WHITE,  "▣")
        self._tile_done    = self._stat_tile(stats_frame, "Done",    GREEN,  "✔")
        self._tile_pending = self._stat_tile(stats_frame, "Pending", YELLOW, "◷")
        self._tile_overdue = self._stat_tile(stats_frame, "Overdue", RED,    "⚠")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

    def _stat_tile(self, parent, label, color, icon):
        """A stat card: icon + big number + small label."""
        tile = tk.Frame(parent, bg=CARD_BG, padx=12, pady=6)
        tile.pack(side="left", padx=4)
        top = tk.Frame(tile, bg=CARD_BG)
        top.pack()
        tk.Label(top, text=icon, bg=CARD_BG, fg=color,
                 font=("Segoe UI", 11)).pack(side="left", padx=(0, 4))
        val = tk.Label(top, text="0", bg=CARD_BG, fg=color,
                       font=("Segoe UI", 15, "bold"))
        val.pack(side="left")
        tk.Label(tile, text=label, bg=CARD_BG, fg=MUTED,
                 font=FS).pack()
        return val

    # ─────────────────────────────────────────────────────────────────────────
    #  SIDEBAR
    # ─────────────────────────────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=SIDEBAR, width=200)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        tk.Frame(sb, bg=BORDER, width=1).pack(side="right", fill="y")

        self._sb_section(sb, "FILTER")
        self._filter_btn(sb, "All Tasks",   "All",     icon="≡",  color=WHITE)
        self._filter_btn(sb, "Done",        "Done",    icon="✔",  color=GREEN)
        self._filter_btn(sb, "Pending",     "Pending", icon="◷",  color=YELLOW)
        self._filter_btn(sb, "Due Today",   "Today",   icon="★",  color=ACCENT)
        self._filter_btn(sb, "Overdue",     "Overdue", icon="⚠",  color=RED)
        self._filter_btn(sb, "High",        "High",    icon="⬤",  color=RED)
        self._filter_btn(sb, "Medium",      "Medium",  icon="⬤",  color=YELLOW)
        self._filter_btn(sb, "Low",         "Low",     icon="⬤",  color=PURPLE)

        tk.Frame(sb, bg=BORDER2, height=1).pack(fill="x", padx=14, pady=10)
        self._sb_section(sb, "SORT")
        self._side_btn(sb, "Priority",  "Bubble Sort O(n²)",    self._sort_priority)
        self._side_btn(sb, "Due Date",  "Merge Sort O(n log n)", self._sort_due)

        tk.Frame(sb, bg=BORDER2, height=1).pack(fill="x", padx=14, pady=10)
        self._sb_section(sb, "FILE")
        self._side_btn(sb, "Save Tasks", "", self._save, icon="💾", hi_color=GREEN)

    def _sb_section(self, parent, text):
        tk.Label(parent, text=text, bg=SIDEBAR, fg=MUTED2,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=16, pady=(12, 4))

    def _filter_btn(self, parent, label, value, icon="", color=WHITE):
        """Filter button — highlights when active."""
        var = self.filter_mode
        def cmd():
            var.set(value)
            self._refresh()

        f = tk.Frame(parent, bg=SIDEBAR, cursor="hand2")
        f.pack(fill="x")

        icon_lbl = tk.Label(f, text=icon, bg=SIDEBAR, fg=color,
                            font=("Segoe UI", 10), width=2)
        icon_lbl.pack(side="left", padx=(14, 4), pady=3)

        text_lbl = tk.Label(f, text=label, bg=SIDEBAR, fg=WHITE,
                            font=FS, anchor="w")
        text_lbl.pack(side="left", fill="x", expand=True)

        # active indicator bar (left edge)
        bar = tk.Frame(f, bg=SIDEBAR, width=3)
        bar.pack(side="left", fill="y")

        def enter(e):
            if var.get() != value:
                f.configure(bg=HOVER_BG)
                icon_lbl.configure(bg=HOVER_BG)
                text_lbl.configure(bg=HOVER_BG)
                bar.configure(bg=HOVER_BG)

        def leave(e):
            if var.get() != value:
                f.configure(bg=SIDEBAR)
                icon_lbl.configure(bg=SIDEBAR)
                text_lbl.configure(bg=SIDEBAR)
                bar.configure(bg=SIDEBAR)

        def refresh_state(*_):
            active = (var.get() == value)
            bg_c = HOVER_BG if active else SIDEBAR
            fg_c = color    if active else WHITE
            bar_c= color    if active else SIDEBAR
            f.configure(bg=bg_c)
            icon_lbl.configure(bg=bg_c, fg=color)
            text_lbl.configure(bg=bg_c, fg=fg_c, font=FSB if active else FS)
            bar.configure(bg=bar_c)

        for w in (f, icon_lbl, text_lbl):
            w.bind("<Button-1>", lambda e, c=cmd, rs=refresh_state: (c(), rs()))
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)

        var.trace_add("write", lambda *_: refresh_state())
        refresh_state()

    def _side_btn(self, parent, label, sublabel, cmd, icon="", hi_color=MUTED):
        f = tk.Frame(parent, bg=SIDEBAR, cursor="hand2")
        f.pack(fill="x")
        inner = tk.Frame(f, bg=SIDEBAR)
        inner.pack(fill="x", padx=16, pady=3)
        if icon:
            tk.Label(inner, text=icon, bg=SIDEBAR, fg=hi_color,
                     font=FB).pack(side="left", padx=(0, 6))
        tk.Label(inner, text=label, bg=SIDEBAR, fg=WHITE,
                 font=FS).pack(side="left")
        if sublabel:
            tk.Label(inner, text=f"  {sublabel}", bg=SIDEBAR, fg=MUTED2,
                     font=("Segoe UI", 7)).pack(side="left")

        def enter(e):
            f.configure(bg=HOVER_BG); inner.configure(bg=HOVER_BG)
            for w in inner.winfo_children(): w.configure(bg=HOVER_BG)
        def leave(e):
            f.configure(bg=SIDEBAR);  inner.configure(bg=SIDEBAR)
            for w in inner.winfo_children(): w.configure(bg=SIDEBAR)

        for w in (f, inner):
            w.bind("<Button-1>", lambda e: cmd())
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)
        for child in inner.winfo_children():
            child.bind("<Button-1>", lambda e: cmd())
            child.bind("<Enter>", enter)
            child.bind("<Leave>", leave)

    # ─────────────────────────────────────────────────────────────────────────
    #  MAIN PANEL
    # ─────────────────────────────────────────────────────────────────────────
    def _build_main(self, parent):
        main = tk.Frame(parent, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        # toolbar row
        tb = tk.Frame(main, bg=BG)
        tb.pack(fill="x", padx=18, pady=12)

        # search box
        sf = tk.Frame(tb, bg=CARD_BG, highlightthickness=1,
                      highlightbackground=BORDER2, highlightcolor=ACCENT)
        sf.pack(side="left", fill="x", expand=True, padx=(0, 14))
        tk.Label(sf, text=" 🔍", bg=CARD_BG, fg=MUTED,
                 font=FB).pack(side="left")
        se = tk.Entry(sf, textvariable=self.search_var, bg=CARD_BG, fg=WHITE,
                      insertbackground=WHITE, relief="flat", font=FB)
        se.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        se.bind("<KeyRelease>", lambda e: self._refresh())
        se.bind("<FocusIn>",  lambda e: sf.configure(highlightbackground=ACCENT))
        se.bind("<FocusOut>", lambda e: sf.configure(highlightbackground=BORDER2))
        tk.Label(sf, text="Linear Search O(n)  ", bg=CARD_BG, fg=MUTED2,
                 font=("Segoe UI", 8)).pack(side="right")

        # add button
        tk.Button(tb, text=" + Add Task ", bg=ACCENT, fg=BG, font=FH,
                  relief="flat", padx=14, pady=8, cursor="hand2",
                  activebackground=ACCENT2, activeforeground=WHITE,
                  command=self._add_task).pack(side="right")

        # progress bar strip (full width, shows done%)
        self._prog_frame = tk.Frame(main, bg=BG, height=4)
        self._prog_frame.pack(fill="x", padx=18)
        self._prog_done = tk.Frame(self._prog_frame, bg=GREEN, height=4)
        self._prog_done.place(x=0, y=0, relheight=1, relwidth=0)

        # scrollable list
        lf = tk.Frame(main, bg=BG)
        lf.pack(fill="both", expand=True, padx=18, pady=(8, 14))

        self._canvas = tk.Canvas(lf, bg=BG, highlightthickness=0)
        vsb = styled_scrollbar(lf)
        vsb.configure(command=self._canvas.yview)
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

    def _scroll(self, e):
        if e.num == 4:   self._canvas.yview_scroll(-1, "units")
        elif e.num == 5: self._canvas.yview_scroll( 1, "units")
        else:            self._canvas.yview_scroll(int(-e.delta/120), "units")

    def _build_ui(self):
        self._build_header()
        content = tk.Frame(self, bg=BG)
        content.pack(fill="both", expand=True)
        self._build_sidebar(content)
        self._build_main(content)

    # ─────────────────────────────────────────────────────────────────────────
    #  DATA / REFRESH
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _is_overdue(t):
        try: return datetime.date.fromisoformat(t["due"]) < datetime.date.today()
        except ValueError: return False

    def _get_view(self):
        full  = self.tasks.to_list()
        kw    = self.search_var.get().strip()
        mode  = self.filter_mode.get()
        today = datetime.date.today().isoformat()

        if kw:
            names = {t["task"] for t in linear_search(full, kw)}
            pairs = [(i, t) for i, t in enumerate(full) if t["task"] in names]
        else:
            pairs = list(enumerate(full))

        if   mode == "Done":    pairs = [(i,t) for i,t in pairs if t["done"]]
        elif mode == "Pending": pairs = [(i,t) for i,t in pairs if not t["done"]]
        elif mode == "Today":   pairs = [(i,t) for i,t in pairs if t["due"] == today]
        elif mode == "Overdue": pairs = [(i,t) for i,t in pairs if not t["done"] and self._is_overdue(t)]
        elif mode in ("High","Medium","Low"):
            pairs = [(i,t) for i,t in pairs if t["priority"].lower() == mode.lower()]
        return pairs

    def _refresh(self):
        for w in self._task_frame.winfo_children():
            w.destroy()

        view = self._get_view()

        if not view:
            tk.Label(self._task_frame,
                     text="No tasks here.\nPress  + Add Task  to create one.",
                     bg=BG, fg=MUTED, font=("Segoe UI", 12),
                     justify="center").pack(pady=80)
        else:
            for real_idx, task in view:
                card = TaskCard(self._task_frame, task, real_idx,
                                on_done=self._toggle_done,
                                on_edit=self._edit_task,
                                on_delete=self._delete_task)
                card.pack(fill="x", pady=(0, 0))
                tk.Frame(self._task_frame, bg=BORDER, height=1).pack(fill="x")

        self._update_stats()

    def _update_stats(self):
        lst     = self.tasks.to_list()
        total   = len(lst)
        done    = sum(1 for t in lst if t["done"])
        pending = total - done
        overdue = sum(1 for t in lst if not t["done"] and self._is_overdue(t))

        self._tile_total  .config(text=str(total))
        self._tile_done   .config(text=str(done))
        self._tile_pending.config(text=str(pending))
        self._tile_overdue.config(text=str(overdue))

        # update progress bar
        pct = (done / total) if total else 0
        self._prog_done.place(relwidth=pct)

    # ─────────────────────────────────────────────────────────────────────────
    #  ACTIONS
    # ─────────────────────────────────────────────────────────────────────────
    def _add_task(self):
        dlg = TaskDialog(self, title="Add Task")
        if dlg.result:
            self.tasks.append(dlg.result)
            self._refresh()
            speak_async("Task added.", self.voice_on.get())

    def _toggle_done(self, real_idx):
        t = self.tasks.get_at(real_idx)
        if t is None: return
        t["done"] = not t["done"]
        self.tasks.update_at(real_idx, t)
        speak_async("Marked as " + ("done." if t["done"] else "pending."),
                    self.voice_on.get())
        self._refresh()

    def _edit_task(self, real_idx):
        t = self.tasks.get_at(real_idx)
        if t is None: return
        dlg = TaskDialog(self, title="Edit Task", task=t)
        if dlg.result:
            dlg.result["done"] = t["done"]
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


if __name__ == "__main__":
    ToDoApp().mainloop()