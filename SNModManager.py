import os
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox
import shutil
import subprocess
import time
import threading

SUBNAUTICA_EXE = "Subnautica.exe"
SUBNAUTICA_PATH_DEFAULT = r"C:\Program Files (x86)\Steam\steamapps\common\Subnautica"

def find_subnautica(max_search_time=120):
    if os.path.exists(os.path.join(SUBNAUTICA_PATH_DEFAULT, SUBNAUTICA_EXE)):
        return os.path.abspath(SUBNAUTICA_PATH_DEFAULT)

    loading_win = tk.Toplevel()
    loading_win.title("Searching for Subnautica...")
    loading_win.geometry("400x140")
    loading_win.resizable(False, False)
    status_label = tk.Label(loading_win, text="Searching for Subnautica...")
    status_label.pack(pady=10)
    drive_label = tk.Label(loading_win, text="Drive: -")
    drive_label.pack(pady=5)
    time_label = tk.Label(loading_win, text="Elapsed: 0.0s")
    time_label.pack(pady=5)
    loading_win.update()
    start_time = time.time()
    result = {"path": None}
    state = {
        "stop": False,
        "current_drive": "-"
    }

    drives = [f"{d}:\\" for d in "CDEFGHIJKLMNOPQRSTUVWXYZAB" if os.path.exists(f"{d}:\\")]
    def scan():
        for drive in drives:
            if state["stop"]:
                return
            state["current_drive"] = drive
            for root_dir, _, files in os.walk(drive):
                if state["stop"]:
                    return
                if SUBNAUTICA_EXE in files:
                    result["path"] = root_dir
                    state["stop"] = True
                    return
                if time.time() - start_time > max_search_time:
                    state["stop"] = True
                    return

    def update_ui():
        elapsed = time.time() - start_time
        time_label.config(text=f"Elapsed: {elapsed:.1f}/120s")
        drive_label.config(text=f"Scanning Drive: {state['current_drive']}")
        if not state["stop"]:
            loading_win.after(100, update_ui)
        else:
            loading_win.destroy()
    thread = threading.Thread(target=scan, daemon=True)
    thread.start()
    update_ui()
    loading_win.grab_set()
    loading_win.wait_window()
    if result["path"]:
        return os.path.abspath(result["path"])
    messagebox.showinfo(
        "Not Found",
        "SNModManager could not find Subnautica automatically.\nPlease select the Subnautica folder."
    )
    selected_folder = filedialog.askdirectory(title="Select Subnautica Folder")
    if selected_folder and os.path.exists(os.path.join(selected_folder, SUBNAUTICA_EXE)):
        return os.path.abspath(selected_folder)
    messagebox.showerror("Error", "Subnautica.exe not found. SNModManager cannot continue.")
    return None
root = tk.Tk()
root.title("SNModManager")
root.geometry("300x550")
root.withdraw()
SUBNAUTICA_PATH = find_subnautica()
if not SUBNAUTICA_PATH:
    root.destroy()
    exit()
root.deiconify()

last_enabled_mod = None
mod_index_map = {}
PLUGINS_PATH = os.path.join(SUBNAUTICA_PATH, "BepInEx", "plugins")
DISABLED_PATH = os.path.join(SUBNAUTICA_PATH, "SNModManager", "DisabledMods")
os.makedirs(PLUGINS_PATH, exist_ok=True)
os.makedirs(DISABLED_PATH, exist_ok=True)
def refresh_mod_list():
    mod_list.delete(0, tk.END)
    mod_index_map.clear()

    def is_mod(path):
        return os.path.isdir(path) or (
            os.path.isfile(path) and path.lower().endswith(".dll")
        )
    enabled_mods = [
        d for d in os.listdir(PLUGINS_PATH)
        if is_mod(os.path.join(PLUGINS_PATH, d))
    ]
    disabled_mods = [
        d for d in os.listdir(DISABLED_PATH)
        if is_mod(os.path.join(DISABLED_PATH, d))
    ]
    global last_enabled_mod
    if enabled_mods or disabled_mods:
        for mod in enabled_mods:
            idx = mod_list.size()

            if mod == "Tobey":
                display = "BepInEx"
            elif mod.lower().endswith(".dll"):
                display = os.path.splitext(mod)[0] + " (DLL)"
            else:
                display = mod

            mod_list.insert(tk.END, f"[ENABLED] - {display}")
            mod_index_map[idx] = mod

            mod_list.itemconfig(
                idx,
                {'fg': 'blue' if last_enabled_mod == mod else 'green'}
            )
        for mod in disabled_mods:
            idx = mod_list.size()
            if mod.lower().endswith(".dll"):
                display = os.path.splitext(mod)[0] + " (DLL)"
            else:
                display = mod
            mod_list.insert(tk.END, f"[DISABLED] - {display}")
            mod_index_map[idx] = mod
            mod_list.itemconfig(idx, {'fg': 'red'})
    else:
        mod_list.insert(tk.END, "(No mods installed)")
        mod_list.itemconfig(0, {'fg': 'gray'})
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
    selection = mod_list.curselection()
    if not selection:
        messagebox.showwarning("No selection", "Please select a mod to toggle.")
        return
    idx = selection[0]
    if idx not in mod_index_map:
        return
    mod_name = mod_index_map[idx]
    entry = mod_list.get(idx)
    global last_enabled_mod
    last_enabled_mod = None
    if entry.startswith("[ENABLED]"):
        src = os.path.join(PLUGINS_PATH, mod_name)
        dst = os.path.join(DISABLED_PATH, mod_name)
    else:
        src = os.path.join(DISABLED_PATH, mod_name)
        dst = os.path.join(PLUGINS_PATH, mod_name)
        last_enabled_mod = mod_name
    if not os.path.exists(src):
        messagebox.showerror("Error", f"Mod not found:\n{src}")
        return
    try:
        shutil.move(src, dst)
        refresh_mod_list()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to toggle mod:\n{e}")

def open_mods_folder():
    subprocess.Popen(f'explorer "{PLUGINS_PATH}"')

def launch_subnautica():
    exe_path = os.path.join(SUBNAUTICA_PATH, SUBNAUTICA_EXE)
    if os.path.exists(exe_path):
        subprocess.Popen(exe_path)
    else:
        messagebox.showerror("Error", "Subnautica.exe not found.")

tk.Label(root, text="Subnautica Mod Manager", font=("Arial", 14, "bold")).pack(pady=10)
tk.Button(root, text="Add Mod", command=select_and_install_mod, width=25, height=2).pack(pady=5)
tk.Button(root, text="Launch Subnautica", command=launch_subnautica, width=25, height=2).pack(pady=5)
tk.Label(root, text="Mods:", font=("Arial", 12, "bold")).pack(pady=5)
frame_list = tk.Frame(root)
frame_list.pack(pady=5, fill="both", expand=True)
scrollbar = tk.Scrollbar(frame_list)
scrollbar.pack(side="right", fill="y")
mod_list = tk.Listbox(frame_list, yscrollcommand=scrollbar.set)
mod_list.pack(side="left", fill="both", expand=True)
scrollbar.config(command=mod_list.yview)
tk.Button(root, text="Enable / Disable Selected Mod", command=toggle_mod, width=30).pack(pady=5)
frame_bottom = tk.Frame(root)
frame_bottom.pack(pady=5)
tk.Button(frame_bottom, text="Refresh Mods", command=refresh_mod_list, width=15).grid(row=0, column=0, padx=5)
tk.Button(frame_bottom, text="Open Mods Folder", command=open_mods_folder, width=20).grid(row=0, column=1, padx=5)
status_var = tk.StringVar()
tk.Label(root, textvariable=status_var, bd=1, relief="sunken", anchor="w").pack(side="bottom", fill="x")

refresh_mod_list()
root.mainloop()
