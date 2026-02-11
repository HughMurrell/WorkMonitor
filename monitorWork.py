#!/usr/bin/env python3
"""
WorkMonitor GUI Application
A graphical interface for managing work sessions across multiple git repositories.
"""

import sys
import os

# Check for tkinter and try system Python on macOS if needed
try:
    import tkinter as tk
except ImportError:
    if sys.platform == 'darwin':
        # Try to use system Python which has tkinter
        system_python = '/usr/bin/python3'
        if os.path.exists(system_python):
            print("Switching to system Python for tkinter support...")
            os.execv(system_python, [system_python] + sys.argv)
    print("Error: tkinter is not available.")
    print("\nOn macOS with Homebrew Python, you have two options:")
    print("1. Run with system Python: /usr/bin/python3 monitorWork.py")
    print("2. Install tkinter support: brew install python-tk")
    sys.exit(1)

from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import subprocess
import fcntl
import tempfile
from pathlib import Path
from datetime import datetime

# Configuration
CONFIG_DIR = Path.home() / ".workmonitor"
CONFIG_FILE = CONFIG_DIR / "repositories.json"
LOCK_FILE = CONFIG_DIR / "monitorWork.lock"

class SingleInstance:
    """Ensure only one instance of the application runs at a time."""
    def __init__(self, lock_file):
        self.lock_file = lock_file
        self.lock_fd = None
        
    def __enter__(self):
        # Create config directory if it doesn't exist
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            self.lock_fd = open(self.lock_file, 'w')
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_fd.write(str(os.getpid()))
            self.lock_fd.flush()
            return self
        except (IOError, OSError):
            messagebox.showerror(
                "Already Running",
                "monitorWork.py is already running.\nOnly one instance can run at a time."
            )
            sys.exit(1)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                self.lock_fd.close()
                if self.lock_file.exists():
                    self.lock_file.unlink()
            except:
                pass

class WorkMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WorkMonitor")
        self.root.geometry("800x600")
        
        # Repository list (list of dicts with 'path' and 'selected')
        self.repositories = []
        
        # Load saved repositories
        self.load_repositories()
        
        # Create GUI
        self.create_widgets()
        
        # Update repository list display
        self.update_repo_list()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Repository management section
        repo_frame = ttk.LabelFrame(main_frame, text="Git Repositories", padding="10")
        repo_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        repo_frame.columnconfigure(0, weight=1)
        repo_frame.rowconfigure(1, weight=1)
        
        # Repository list with scrollbar
        list_frame = ttk.Frame(repo_frame)
        list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Treeview for repository list with checkboxes
        columns = ('selected', 'path')
        self.repo_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=10)
        self.repo_tree.heading('#0', text='')
        self.repo_tree.heading('selected', text='Selected')
        self.repo_tree.heading('path', text='Repository Path')
        self.repo_tree.column('#0', width=30, stretch=False)
        self.repo_tree.column('selected', width=80, stretch=False)
        self.repo_tree.column('path', width=500, stretch=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.repo_tree.yview)
        self.repo_tree.configure(yscrollcommand=scrollbar.set)
        
        self.repo_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind click events for checkbox toggling
        self.repo_tree.bind('<Button-1>', self.on_tree_click)
        
        # Repository management buttons
        repo_btn_frame = ttk.Frame(repo_frame)
        repo_btn_frame.grid(row=2, column=0, columnspan=2, pady=5)
        
        ttk.Button(repo_btn_frame, text="Add Repository", command=self.add_repository).pack(side=tk.LEFT, padx=5)
        ttk.Button(repo_btn_frame, text="Remove Selected", command=self.remove_repository).pack(side=tk.LEFT, padx=5)
        ttk.Button(repo_btn_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(repo_btn_frame, text="Deselect All", command=self.deselect_all).pack(side=tk.LEFT, padx=5)
        
        # Date input section
        date_frame = ttk.LabelFrame(main_frame, text="Date Range", padding="10")
        date_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(date_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.start_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(date_frame, textvariable=self.start_date_var, width=15).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(date_frame, text="End Date (YYYY-MM-DD):").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.end_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(date_frame, textvariable=self.end_date_var, width=15).grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Action buttons
        action_frame = ttk.LabelFrame(main_frame, text="Actions", padding="10")
        action_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(action_frame, text="Start Work", command=self.start_work, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Stop Work", command=self.stop_work, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Tabulate Work", command=self.tabulate_work, width=20).pack(side=tk.LEFT, padx=5)
    
    def on_tree_click(self, event):
        """Handle clicks on the treeview to toggle selection."""
        region = self.repo_tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.repo_tree.identify_row(event.x, event.y)
            column = self.repo_tree.identify_column(event.x, event.y)
            
            if item and column == "#1":  # Clicked on the 'selected' column
                # Get current selection state
                values = self.repo_tree.item(item, 'values')
                if values:
                    current_state = values[0]
                    new_state = "☐" if current_state == "☑" else "☑"
                    
                    # Update the tree
                    path = values[1]
                    self.repo_tree.item(item, values=(new_state, path))
                    
                    # Update the repository list
                    for repo in self.repositories:
                        if repo['path'] == path:
                            repo['selected'] = (new_state == "☑")
                            break
                    
                    # Save changes
                    self.save_repositories()
    
    def update_repo_list(self):
        """Update the treeview with current repository list."""
        # Clear existing items
        for item in self.repo_tree.get_children():
            self.repo_tree.delete(item)
        
        # Add repositories
        for repo in self.repositories:
            selected = "☑" if repo.get('selected', False) else "☐"
            self.repo_tree.insert('', tk.END, values=(selected, repo['path']))
    
    def add_repository(self):
        """Add a new repository path."""
        # Try to get path from file dialog first
        path = filedialog.askdirectory(title="Select Git Repository Directory")
        
        if not path:
            # Fallback to text input
            path = simpledialog.askstring("Add Repository", "Enter repository path:")
        
        if path:
            path = os.path.abspath(path)
            
            # Check if it's a git repository
            if not os.path.isdir(os.path.join(path, '.git')):
                messagebox.showerror("Error", f"'{path}' is not a git repository.")
                return
            
            # Check if already exists
            if any(r['path'] == path for r in self.repositories):
                messagebox.showwarning("Warning", "Repository already in list.")
                return
            
            # Add to list
            self.repositories.append({'path': path, 'selected': False})
            self.save_repositories()
            self.update_repo_list()
    
    def remove_repository(self):
        """Remove selected repository from list."""
        selected_items = self.repo_tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select a repository to remove.")
            return
        
        for item in selected_items:
            values = self.repo_tree.item(item, 'values')
            if values:
                path = values[1]
                self.repositories = [r for r in self.repositories if r['path'] != path]
        
        self.save_repositories()
        self.update_repo_list()
    
    def select_all(self):
        """Select all repositories."""
        for repo in self.repositories:
            repo['selected'] = True
        self.save_repositories()
        self.update_repo_list()
    
    def deselect_all(self):
        """Deselect all repositories."""
        for repo in self.repositories:
            repo['selected'] = False
        self.save_repositories()
        self.update_repo_list()
    
    def get_selected_repositories(self):
        """Get list of selected repository paths."""
        return [r['path'] for r in self.repositories if r.get('selected', False)]
    
    def validate_dates(self):
        """Validate date inputs."""
        try:
            start_date = self.start_date_var.get().strip()
            end_date = self.end_date_var.get().strip()
            
            # Validate format
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
            
            return start_date, end_date
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD format.")
            return None, None
    
    def start_work(self):
        """Execute startWork for selected repositories."""
        selected = self.get_selected_repositories()
        if not selected:
            messagebox.showwarning("Warning", "Please select at least one repository.")
            return
        
        for repo_path in selected:
            try:
                result = subprocess.run(
                    ['startWork', repo_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode != 0:
                    messagebox.showerror(
                        "Error",
                        f"Failed to start work on {repo_path}:\n{result.stderr}"
                    )
            except FileNotFoundError:
                messagebox.showerror(
                    "Error",
                    "startWork command not found. Please ensure it's installed and in your PATH."
                )
                return
            except subprocess.TimeoutExpired:
                messagebox.showerror("Error", f"Timeout starting work on {repo_path}")
        
        messagebox.showinfo("Success", f"Started work on {len(selected)} repository(ies).")
    
    def stop_work(self):
        """Execute stopWork for selected repositories."""
        selected = self.get_selected_repositories()
        if not selected:
            messagebox.showwarning("Warning", "Please select at least one repository.")
            return
        
        for repo_path in selected:
            try:
                result = subprocess.run(
                    ['stopWork', repo_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode != 0:
                    messagebox.showerror(
                        "Error",
                        f"Failed to stop work on {repo_path}:\n{result.stderr}"
                    )
            except FileNotFoundError:
                messagebox.showerror(
                    "Error",
                    "stopWork command not found. Please ensure it's installed and in your PATH."
                )
                return
            except subprocess.TimeoutExpired:
                messagebox.showerror("Error", f"Timeout stopping work on {repo_path}")
        
        messagebox.showinfo("Success", f"Stopped work on {len(selected)} repository(ies).")
    
    def tabulate_work(self):
        """Execute tabulateWork for selected repositories."""
        selected = self.get_selected_repositories()
        if not selected:
            messagebox.showwarning("Warning", "Please select at least one repository.")
            return
        
        start_date, end_date = self.validate_dates()
        if not start_date or not end_date:
            return
        
        # Ask for output file
        output_file = filedialog.asksaveasfilename(
            title="Save Work Report",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not output_file:
            return
        
        try:
            # Build command
            cmd = ['tabulateWork', '-o', output_file, start_date, end_date] + selected
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                messagebox.showerror(
                    "Error",
                    f"Failed to generate work report:\n{result.stderr}"
                )
            else:
                messagebox.showinfo("Success", f"Work report saved to {output_file}")
        except FileNotFoundError:
            messagebox.showerror(
                "Error",
                "tabulateWork command not found. Please ensure it's installed and in your PATH."
            )
        except subprocess.TimeoutExpired:
            messagebox.showerror("Error", "Timeout generating work report")
    
    def load_repositories(self):
        """Load repository list from file."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.repositories = data.get('repositories', [])
            except (json.JSONDecodeError, IOError):
                self.repositories = []
        else:
            self.repositories = []
    
    def save_repositories(self):
        """Save repository list to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({'repositories': self.repositories}, f, indent=2)
        except IOError as e:
            messagebox.showerror("Error", f"Failed to save repositories: {e}")
    
    def on_closing(self):
        """Handle window closing."""
        self.save_repositories()
        self.root.destroy()

def main():
    # Ensure single instance
    with SingleInstance(LOCK_FILE):
        root = tk.Tk()
        app = WorkMonitorGUI(root)
        root.mainloop()

if __name__ == "__main__":
    main()

