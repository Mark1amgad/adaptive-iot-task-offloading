import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

DEFAULT_REPO = r"D:\computer network research\adaptive-iot-task-offloading"
MY_WORK_FOLDER = "team-work/Ayoub/rl_model/"


class GitHubGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub GUI - Adaptive IoT")
        self.root.geometry("1120x760")
        self.root.minsize(850, 600)
        self.root.configure(bg="#f3f6fb")

        self.repo_var = tk.StringVar(value=DEFAULT_REPO)
        self.message_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.branch_var = tk.StringVar(value="Branch: —")
        self.items = {}

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure("Treeview", rowheight=29, font=("Segoe UI", 10),
                             background="white", fieldbackground="white")
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.style.configure("TButton", font=("Segoe UI", 10), padding=(9, 7))
        self.style.configure("TLabel", background="#f3f6fb", font=("Segoe UI", 10))
        self.style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        self.build_ui()
        self.refresh_status()

    def build_ui(self):
        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="◆  GitHub GUI - Adaptive IoT",
                  style="Title.TLabel").pack(side="left")
        ttk.Label(header, textvariable=self.branch_var,
                  font=("Segoe UI", 11, "bold")).pack(side="right", padx=8)

        ttk.Label(outer, text="Repository path").pack(anchor="w")
        pathrow = ttk.Frame(outer)
        pathrow.pack(fill="x", pady=(4, 12))
        ttk.Entry(pathrow, textvariable=self.repo_var).pack(side="left", fill="x", expand=True)
        ttk.Button(pathrow, text="Browse…", command=self.browse_repo).pack(side="left", padx=(8, 0))

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(0, 12))
        self.action_button(actions, "↻ Refresh Changes", self.refresh_status, "#1976d2")
        self.action_button(actions, "↓ Pull", self.pull, "#2e9d65")
        self.action_button(actions, "＋ Stage Selected", self.stage_selected, "#7652c8")
        self.action_button(actions, "− Unstage Selected", self.unstage_selected, "#d9822b")
        self.action_button(actions, "✓ Commit", self.commit, "#315f9e")
        self.action_button(actions, "↑ Push", self.push, "#159aa2")

        content = ttk.Panedwindow(outer, orient="horizontal")
        content.pack(fill="both", expand=True)

        left = ttk.Frame(content, padding=(0, 0, 8, 0))
        right = ttk.Frame(content, padding=(8, 0, 0, 0))
        content.add(left, weight=3)
        content.add(right, weight=2)

        ttk.Label(left, text="Changed files  (Ctrl/Shift to select)").pack(anchor="w", pady=(0, 6))
        columns = ("mark", "status", "path")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("mark", text="Stage")
        self.tree.heading("status", text="Status")
        self.tree.heading("path", text="File path")
        self.tree.column("mark", width=55, anchor="center", stretch=False)
        self.tree.column("status", width=100, anchor="center", stretch=False)
        self.tree.column("path", width=390, anchor="w")
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self.show_diff)

        ttk.Label(right, text="Commit message").pack(anchor="w", pady=(0, 6))
        self.message = tk.Text(right, height=5, wrap="word", font=("Segoe UI", 10),
                               relief="solid", bd=1)
        self.message.pack(fill="x")
        self.message.insert("1.0", "")
        ttk.Label(right, text=f"Your work folder: {MY_WORK_FOLDER}",
                  wraplength=330).pack(anchor="w", pady=(8, 14))

        notes = ttk.LabelFrame(right, text="Safety notes", padding=10)
        notes.pack(fill="x", pady=(0, 12))
        note_text = (
            "• Pull is blocked when the working tree has changes.\n"
            "• Review staged files before Commit.\n"
            "• Push requires confirmation.\n"
            "• Merge conflicts must be resolved manually.\n"
            "• Avoid committing other team members' files."
        )
        ttk.Label(notes, text=note_text, justify="left", wraplength=340).pack(anchor="w")

        ttk.Label(outer, text="Output / Logs").pack(anchor="w", pady=(12, 4))
        logframe = ttk.Frame(outer)
        logframe.pack(fill="both", expand=False)
        self.output = tk.Text(logframe, height=7, wrap="word", bg="#17212f",
                              fg="#e8eef7", insertbackground="white",
                              font=("Consolas", 9), relief="flat", padx=8, pady=6)
        logscroll = ttk.Scrollbar(logframe, orient="vertical", command=self.output.yview)
        self.output.configure(yscrollcommand=logscroll.set)
        self.output.pack(side="left", fill="both", expand=True)
        logscroll.pack(side="right", fill="y")
        self.log("Ready. Select your local repository and refresh changes.")
        ttk.Label(outer, textvariable=self.status_var).pack(anchor="w", pady=(8, 0))

    def action_button(self, parent, text, command, color):
        btn = tk.Button(parent, text=text, command=command, bg=color, fg="white",
                        activebackground=color, activeforeground="white",
                        relief="flat", bd=0, padx=10, pady=9,
                        font=("Segoe UI", 9, "bold"), cursor="hand2")
        btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

    def repo(self):
        return Path(self.repo_var.get().strip().strip('"'))

    def run_git(self, *args, check=True):
        repo = self.repo()
        if not repo.is_dir():
            raise RuntimeError(f"Repository folder not found:\n{repo}")
        p = subprocess.run(["git", *args], cwd=str(repo), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", shell=False)
        output = (p.stdout or "") + (p.stderr or "")
        self.log(f"> git {' '.join(args)}\n{output.strip() or '(no output)'}")
        if check and p.returncode != 0:
            raise RuntimeError(output.strip() or "Git command failed.")
        return p

    def log(self, text):
        self.output.insert("end", text + "\n\n")
        self.output.see("end")

    def browse_repo(self):
        folder = filedialog.askdirectory(title="Choose local Git repository",
                                         initialdir=str(self.repo()))
        if folder:
            self.repo_var.set(folder)
            self.refresh_status()

    def refresh_status(self):
        try:
            self.run_git("rev-parse", "--is-inside-work-tree")
            branch = self.run_git("branch", "--show-current").stdout.strip() or "(detached HEAD)"
            self.branch_var.set("Branch: " + branch)
            result = self.run_git("status", "--porcelain=v1", "-uall")
            self.tree.delete(*self.tree.get_children())
            self.items.clear()
            staged_count = 0
            for line in result.stdout.splitlines():
                if len(line) < 4:
                    continue
                code, path = line[:2], line[3:]
                if " -> " in path:
                    path = path.split(" -> ")[-1]
                if code == "??":
                    status = "Untracked"
                elif "U" in code:
                    status = "Conflict"
                elif "D" in code:
                    status = "Deleted"
                elif "R" in code:
                    status = "Renamed"
                elif "A" in code:
                    status = "Added"
                elif "M" in code:
                    status = "Modified"
                else:
                    status = code
                staged = code[0] not in (" ", "?")
                if staged:
                    staged_count += 1
                iid = self.tree.insert("", "end", values=("Yes" if staged else "No", status, path))
                self.items[iid] = (code, path)
            self.status_var.set(f"Refresh complete • {len(self.items)} changed path(s) • {staged_count} staged")
        except Exception as e:
            self.status_var.set("Repository check failed")
            messagebox.showerror("Git Error", str(e))

    def selected_paths(self):
        return [self.items[i][1] for i in self.tree.selection() if i in self.items]

    def stage_selected(self):
        paths = self.selected_paths()
        if not paths:
            messagebox.showinfo("Select files", "Select one or more files first.")
            return
        try:
            self.run_git("add", "--", *paths)
            self.refresh_status()
        except Exception as e:
            messagebox.showerror("Stage Error", str(e))

    def unstage_selected(self):
        paths = self.selected_paths()
        if not paths:
            messagebox.showinfo("Select files", "Select staged files first.")
            return
        try:
            self.run_git("restore", "--staged", "--", *paths)
            self.refresh_status()
        except Exception as e:
            messagebox.showerror("Unstage Error", str(e))

    def commit(self):
        message = self.message.get("1.0", "end").strip()
        if not message:
            messagebox.showwarning("Missing message", "Write a commit message first.")
            return
        try:
            staged = self.run_git("diff", "--cached", "--name-only").stdout.splitlines()
            if not staged:
                messagebox.showwarning("Nothing staged", "Select files and click Stage Selected first.")
                return
            outside = [p for p in staged if not p.replace("\\", "/").startswith(MY_WORK_FOLDER)]
            if outside:
                preview = "\n".join(outside[:15])
                if len(outside) > 15:
                    preview += "\n…"
                if not messagebox.askyesno("Outside your work folder",
                    "These staged files are outside your folder:\n\n" + preview +
                    "\n\nInclude them in this commit?"):
                    return
            if not messagebox.askyesno("Confirm Commit",
                    f"Commit {len(staged)} staged file(s)?\n\n{message}"):
                return
            self.run_git("commit", "-m", message)
            self.message.delete("1.0", "end")
            self.refresh_status()
            messagebox.showinfo("Success", "Commit completed.")
        except Exception as e:
            messagebox.showerror("Commit Error", str(e))

    def pull(self):
        try:
            dirty = self.run_git("status", "--porcelain=v1", "-uall").stdout.strip()
            if dirty:
                messagebox.showwarning("Local changes detected",
                    "Pull is blocked because local changes exist.\nReview or commit them first.")
                return
            if not messagebox.askyesno("Confirm Pull",
                    "Pull from origin for the current branch?"):
                return
            result = self.run_git("pull", "--no-rebase", "origin", check=False)
            if result.returncode != 0:
                messagebox.showerror("Pull Error",
                    (result.stdout or "") + (result.stderr or "") +
                    "\n\nIf a merge conflict occurred, resolve it manually.")
            else:
                messagebox.showinfo("Success", "Pull completed.")
            self.refresh_status()
        except Exception as e:
            messagebox.showerror("Pull Error", str(e))

    def push(self):
        try:
            branch = self.run_git("branch", "--show-current").stdout.strip()
            if not branch:
                raise RuntimeError("No current branch is checked out.")
            if not messagebox.askyesno("Confirm Push",
                f"Push commits from '{branch}' to origin?\n\n"
                "Review commits first to ensure they do not include other members' files."):
                return
            result = self.run_git("push", "-u", "origin", branch, check=False)
            if result.returncode != 0:
                messagebox.showerror("Push Error", (result.stdout or "") + (result.stderr or ""))
            else:
                messagebox.showinfo("Success", "Push completed.")
            self.refresh_status()
        except Exception as e:
            messagebox.showerror("Push Error", str(e))

    def show_diff(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        code, path = self.items[selected[0]]
        try:
            if code == "??":
                messagebox.showinfo("Untracked file",
                    "This file is new and has no Git diff until staged.")
                return
            result = self.run_git("diff", "HEAD", "--", path, check=False)
            text = result.stdout or result.stderr or "(No diff output)"
            win = tk.Toplevel(self.root)
            win.title("Diff — " + path)
            win.geometry("850x520")
            box = tk.Text(win, wrap="none", font=("Consolas", 10))
            box.pack(fill="both", expand=True)
            box.insert("1.0", text)
            box.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("Diff Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubGUI(root)
    root.mainloop()
