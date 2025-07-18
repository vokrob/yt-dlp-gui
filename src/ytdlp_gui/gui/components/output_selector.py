"""
Output Selector Component - Handles output directory selection
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Callable, Optional
import os

class OutputSelectorFrame(ctk.CTkFrame):
    """Frame for selecting output directory"""
    
    def __init__(self, parent, settings_manager=None, on_output_change: Callable = None):
        super().__init__(parent)
        
        self.settings_manager = settings_manager
        self.on_output_change = on_output_change
        
        # Initialize with default or saved directory
        if settings_manager:
            self.current_path = settings_manager.get_output_directory()
        else:
            self.current_path = str(Path.home() / "Desktop")
            
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface"""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Output Directory",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20, 10), sticky="w")
        
        # Directory Label
        dir_label = ctk.CTkLabel(self, text="Save to:")
        dir_label.grid(row=1, column=0, padx=(20, 10), pady=5, sticky="w")
        
        # Directory Path Display
        self.path_var = ctk.StringVar(value=self.current_path)
        self.path_entry = ctk.CTkEntry(
            self,
            textvariable=self.path_var,
            state="readonly",
            font=ctk.CTkFont(size=11)
        )
        self.path_entry.grid(row=1, column=1, padx=(0, 10), pady=5, sticky="ew")
        
        # Browse Button
        browse_btn = ctk.CTkButton(
            self,
            text="Browse",
            width=80,
            command=self.browse_directory
        )
        browse_btn.grid(row=1, column=2, padx=(0, 20), pady=5)
        


        
    def browse_directory(self):
        """Open directory browser dialog"""
        try:
            selected_dir = filedialog.askdirectory(
                title="Select Download Directory",
                initialdir=self.current_path
            )
            
            if selected_dir:
                self.set_directory(selected_dir)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to browse directory: {str(e)}")
            
    def set_directory(self, path: str):
        """Set the output directory"""
        try:
            path_obj = Path(path)
            
            # Ensure directory exists
            path_obj.mkdir(parents=True, exist_ok=True)
            
            # Update current path
            self.current_path = str(path_obj)
            self.path_var.set(self.current_path)
            
            # Save to settings if available
            if self.settings_manager:
                self.settings_manager.set_output_directory(self.current_path)
                
            # Update status
            self.update_directory_status()
            
            # Notify parent
            if self.on_output_change:
                self.on_output_change(self.current_path)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set directory: {str(e)}")
            
    def set_quick_directory(self, path: Path):
        """Set directory using quick access buttons"""
        try:
            if path.exists() or path == Path.home() / "Desktop":
                self.set_directory(str(path))
            else:
                # Try to create the directory
                path.mkdir(parents=True, exist_ok=True)
                self.set_directory(str(path))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to access {path.name}: {str(e)}")
            
    def open_directory(self):
        """Open the current directory in file explorer"""
        try:
            path = Path(self.current_path)
            if path.exists():
                if os.name == 'nt':  # Windows
                    os.startfile(str(path))
                elif os.name == 'posix':  # macOS and Linux
                    if 'darwin' in os.uname().sysname.lower():  # macOS
                        os.system(f'open "{path}"')
                    else:  # Linux
                        os.system(f'xdg-open "{path}"')
            else:
                messagebox.showwarning("Warning", "Directory does not exist")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open directory: {str(e)}")
            
    def create_subfolder(self):
        """Create a new subfolder in the current directory"""
        try:
            # Simple input dialog
            dialog = ctk.CTkInputDialog(
                text="Enter subfolder name:",
                title="Create Subfolder"
            )
            folder_name = dialog.get_input()
            
            if folder_name:
                # Sanitize folder name
                folder_name = "".join(c for c in folder_name if c.isalnum() or c in (' ', '-', '_')).strip()
                
                if folder_name:
                    new_path = Path(self.current_path) / folder_name
                    new_path.mkdir(parents=True, exist_ok=True)
                    self.set_directory(str(new_path))
                else:
                    messagebox.showwarning("Warning", "Invalid folder name")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create subfolder: {str(e)}")
            
    def update_directory_status(self):
        """Update the directory status information"""
        try:
            path = Path(self.current_path)
            
            if path.exists():
                # Get directory info
                try:
                    files_count = len(list(path.iterdir()))
                    status = f"Directory exists ({files_count} items)"
                    color = "green"
                except PermissionError:
                    status = "Directory exists (no read permission)"
                    color = "orange"
            else:
                status = "Directory will be created when needed"
                color = "orange"
                
            self.status_label.configure(text=status, text_color=color)
            
        except Exception:
            self.status_label.configure(text="Invalid directory path", text_color="red")
            
    def get_output_path(self) -> str:
        """Get the current output path"""
        return self.current_path
        
    def validate_directory(self) -> bool:
        """Validate the current directory"""
        try:
            path = Path(self.current_path)
            
            # Try to create if it doesn't exist
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                
            # Check if writable
            test_file = path / ".test_write"
            test_file.touch()
            test_file.unlink()
            
            return True
            
        except Exception:
            return False
            
    def get_free_space(self) -> str:
        """Get free space in the current directory"""
        try:
            import shutil
            free_bytes = shutil.disk_usage(self.current_path).free
            
            # Convert to human readable
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if free_bytes < 1024.0:
                    return f"{free_bytes:.1f} {unit}"
                free_bytes /= 1024.0
            return f"{free_bytes:.1f} PB"
            
        except Exception:
            return "Unknown"
