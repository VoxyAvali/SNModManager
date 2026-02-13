import os
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser
import shutil
import subprocess
import time

SUBNAUTICA_EXE = "Subnautica.exe"
SUBNAUTICA_PATH_DEFAULT = r"C:\Program Files (x86)\Steam\steamapps\common\Subnautica"
last_enabled_mod = None 

def find_subnautica(max_search_time=60):

    # Check default path first
    if os.path.exists(os.path.join(SUBNAUTICA_PATH_DEFAULT, SUBNAUTICA_EXE)):
        SUBNAUTICA_PATH = os.path.abspath(SUBNAUTICA_PATH_DEFAULT)
        return SUBNAUTICA_PATH

    loading_win = tk.Toplevel()
    loading_win.title("Searching...")
    tk.Label(loading_win, text=f"Searching for Subnautica install directory...").pack(padx=20, pady=20)
    loading_win.update()

    start_time = time.time()
    found_path = None

    drives = [f"{d}:\\" for d in "CDEFGHIJKLMNOPQRSTUVWXYZAB" if os.path.exists(f"{d}:\\")]
    for drive in drives:
        for root, dirs, files in os.walk(drive):
            if SUBNAUTICA_EXE in files:
                found_path = root
                break
            if time.time() - start_time > max_search_time:
                break
        if found_path or (time.time() - start_time > max_search_time):
            break

    loading_win.destroy()

    if found_path:
        SUBNAUTICA_PATH = os.path.abspath(found_path)
        return SUBNAUTICA_PATH

    messagebox.showinfo("Not Found", "SNModManager could not find Subnautica. Please select the Subnautica folder.")
    selected_folder = filedialog.askdirectory(title="Select Subnautica Folder")
    if selected_folder and os.path.exists(os.path.join(selected_folder, SUBNAUTICA_EXE)):
        SUBNAUTICA_PATH = os.path.abspath(selected_folder)
        return SUBNAUTICA_PATH

    # If still not found, exit
    messagebox.showerror("Error", "Subnautica.exe not found. SNModManager cannot continue.")
    return None


# --- Main SNMM logic ---
root = tk.Tk()
root.title("SNModManager")
root.geometry("300x550")

# Find Subnautica path before proceeding
root.withdraw()  # Hide main window while searching
SUBNAUTICA_PATH = find_subnautica()
if not SUBNAUTICA_PATH:
    root.destroy()
    exit()
root.deiconify()  # Show main window after search

PLUGINS_PATH = os.path.join(SUBNAUTICA_PATH, "BepInEx", "plugins")
DISABLED_PATH = os.path.join(SUBNAUTICA_PATH, "SNModManager", "DisabledMods")
os.makedirs(PLUGINS_PATH, exist_ok=True)
os.makedirs(DISABLED_PATH, exist_ok=True)

def refresh_mod_list():
    mod_list.delete(0, tk.END)

    enabled_mods = [d for d in os.listdir(PLUGINS_PATH) if os.path.isdir(os.path.join(PLUGINS_PATH, d))]
    disabled_mods = [d for d in os.listdir(DISABLED_PATH) if os.path.isdir(os.path.join(DISABLED_PATH, d))]

    global last_enabled_mod

    if enabled_mods or disabled_mods:
        for mod in enabled_mods:
            idx = mod_list.size()
            if mod == "Tobey": # display BepInEx properly, otherwise it displays as "Tobey"
                mod_list.insert(tk.END, f"[ENABLED] - BepInEx")
            else:
                mod_list.insert(tk.END, f"[ENABLED] - {mod}")

            if last_enabled_mod == mod:
                mod_list.itemconfig(idx, {'fg': 'blue'})
            else:
                mod_list.itemconfig(idx, {'fg': 'green'})

        for mod in disabled_mods:
            idx = mod_list.size()
            mod_list.insert(tk.END, f"[DISABLED] - {mod}")
            mod_list.itemconfig(idx, {'fg': 'red'})
    else:
        idx = mod_list.size()
        mod_list.insert(tk.END, "(No mods installed)")
        mod_list.itemconfig(idx, {'fg': 'gray'})

    # Update status bar
    status_var.set(f"Enabled: {len(enabled_mods)} | Disabled: {len(disabled_mods)}")



def select_and_install_mod():
    file_path = filedialog.askopenfilename(title="Add Mod (.zip)", filetypes=[("Zip Files", "*.zip")])
    if not file_path:
        return
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(PLUGINS_PATH)
        refresh_mod_list()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to install mod:\n{e}")


def toggle_mod():
    """Enable or disable the selected mod safely with '[ENABLED] - ModName' format."""
    selection = mod_list.curselection()
    if not selection:
        messagebox.showwarning("No selection", "Please select a mod to toggle.")
        return

    entry = mod_list.get(selection[0])
    if entry == "(No mods installed)":
        return

    global last_enabled_mod
    last_enabled_mod = None  # reset each time

    # Check if enabled or disabled based on prefix
    if entry.startswith("[ENABLED] - "):
        mod_name = entry.replace("[ENABLED] - ", "", 1).strip()
        source_path = os.path.join(PLUGINS_PATH, mod_name)
        target_path = os.path.join(DISABLED_PATH, mod_name)

        if not os.path.isdir(source_path):
            print(f"Error: Mod folder not found: {source_path}. Is BepInEx installed?")
            return

        try:
            shutil.move(source_path, target_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to disable mod:\n{e}")

    elif entry.startswith("[DISABLED] - "):
        mod_name = entry.replace("[DISABLED] - ", "", 1).strip()
        source_path = os.path.join(DISABLED_PATH, mod_name)
        target_path = os.path.join(PLUGINS_PATH, mod_name)

        if not os.path.isdir(source_path):
            print(f"Error: Disabled mod folder not found: {source_path}")
            return

        try:
            shutil.move(source_path, target_path)
            last_enabled_mod = mod_name  # highlight as newly enabled
        except Exception as e:
            messagebox.showerror("Error", f"Failed to enable mod:\n{e}")

    # Refresh the list and status bar
    refresh_mod_list()


def open_mods_folder():
    try:
        subprocess.Popen(f'explorer "{PLUGINS_PATH}"')
    except Exception as e:
        messagebox.showerror("Error", f"Could not open folder:\n{e}")


def launch_subnautica():
    exe_path = os.path.join(SUBNAUTICA_PATH, SUBNAUTICA_EXE)
    if os.path.exists(exe_path):
        subprocess.Popen(exe_path)
    else:
        messagebox.showerror("Error", "Subnautica.exe not found.")


tk.Label(root, text="Subnautica Mod Manager", font=("Arial", 14, "bold")).pack(pady=10)

btn_install = tk.Button(root, text="Add Mod", command=select_and_install_mod, width=25, height=2)
btn_install.pack(pady=5)

btn_launch = tk.Button(root, text="Launch Subnautica", command=launch_subnautica, width=25, height=2)
btn_launch.pack(pady=5)

tk.Label(root, text="Mods:", font=("Arial", 12, "bold")).pack(pady=5)

frame_list = tk.Frame(root)
frame_list.pack(pady=5, fill="both", expand=True)

scrollbar = tk.Scrollbar(frame_list)
scrollbar.pack(side="right", fill="y")

mod_list = tk.Listbox(frame_list, width=60, height=15, yscrollcommand=scrollbar.set)
mod_list.pack(side="left", fill="both", expand=True)
scrollbar.config(command=mod_list.yview)

btn_toggle = tk.Button(root, text="Enable / Disable Selected Mod", command=toggle_mod, width=30)
btn_toggle.pack(pady=5)

frame_bottom = tk.Frame(root)
frame_bottom.pack(pady=5)

btn_refresh = tk.Button(frame_bottom, text="Refresh Mods", command=refresh_mod_list, width=15)
btn_refresh.grid(row=0, column=0, padx=5)

btn_open_folder = tk.Button(frame_bottom, text="Open Mods Folder", command=open_mods_folder, width=20)
btn_open_folder.grid(row=0, column=1, padx=5)

status_var = tk.StringVar()
status_label = tk.Label(root, textvariable=status_var, bd=1, relief="sunken", anchor="w")
status_label.pack(side="bottom", fill="x")

refresh_mod_list()
root.mainloop()
