import os
import sys
from io import BytesIO
import re

import pycdlib

import tkinter as tk
from tkinter import filedialog, messagebox


# =========================
# Core ISO builder
# =========================

def iso_safe_name(filename: str) -> str:
    """
    Create a basic ISO9660 8.3-style uppercase name from a filename.
    """
    name, ext = os.path.splitext(filename)
    name = name.upper()
    ext = ext[1:].upper()  # drop the dot

    # Keep only A-Z, 0-9, _
    name = re.sub(r'[^A-Z0-9_]', '_', name)
    ext = re.sub(r'[^A-Z0-9_]', '_', ext)

    if len(name) > 8:
        name = name[:8]
    if len(ext) > 3:
        ext = ext[:3]

    if not name:
        name = "FILE"
    if not ext:
        ext = "BIN"

    return f"/{name}.{ext};1"


def build_iso(file_list, output_iso, label=None):
    """
    Build a simple data ISO containing all files at the root.
    No autorun, no boot image.
    """
    if not file_list:
        raise ValueError("No input files specified.")

    abs_files = []
    for path in file_list:
        p = os.path.abspath(path)
        if not os.path.isfile(p):
            raise FileNotFoundError(f"File not found: {p}")
        abs_files.append(p)

    # Volume label
    if label:
        label_base = label
    else:
        label_base = os.path.splitext(os.path.basename(abs_files[0]))[0] or "EXE2ISO"

    vol_ident = label_base.upper().replace(" ", "_")[:32]

    iso = pycdlib.PyCdlib()
    iso.new(joliet=1, vol_ident=vol_ident)

    used_iso_names = set()

    for path in abs_files:
        fname = os.path.basename(path)

        # ISO9660 name
        base_iso = iso_safe_name(fname)

        # Ensure unique ISO name if there are duplicates
        original_base = base_iso
        idx = 1
        while base_iso in used_iso_names:
            # Insert a number before the ;1
            base_no_ver, ver = original_base.split(";")
            base_no_ext, ext = base_no_ver.rsplit(".", 1)
            mod = (base_no_ext[:7] + str(idx))  # keep <=8 chars
            base_iso = f"/{mod}.{ext};{ver}"
            idx += 1

        used_iso_names.add(base_iso)

        joliet_path = "/" + fname  # keep real filename for Joliet

        with open(path, "rb") as f:
            data = f.read()

        iso.add_fp(
            BytesIO(data),
            len(data),
            iso_path=base_iso,
            joliet_path=joliet_path,
        )

    iso.write(output_iso)
    iso.close()


# =========================
# CLI mode (still supports: one exe + iso)
# =========================

def cli_main():
    if len(sys.argv) != 3:
        print("Usage:")
        print("  python exe_to_iso.py input.exe output.iso")
        sys.exit(1)

    input_exe = os.path.abspath(sys.argv[1])
    output_iso = os.path.abspath(sys.argv[2])

    try:
        print(f"[+] Building ISO from: {input_exe}")
        build_iso([input_exe], output_iso)
        print(f"[+] ISO created: {output_iso}")
        print("[i] This ISO is a data ISO only (not bootable).")
    except Exception as e:
        print("[!] Error:", e)
        sys.exit(1)


# =========================
# GUI mode
# =========================

def launch_gui():
    root = tk.Tk()
    root.title("EXE → ISO Converter")
    root.resizable(False, False)

    files = []  # list of file paths

    iso_var = tk.StringVar()
    label_var = tk.StringVar()
    status_var = tk.StringVar(value="Add one or more files to include in the ISO.")

    # ---- Callbacks ----

    def add_files():
        new_files = filedialog.askopenfilenames(
            title="Select files to include",
            filetypes=[("All files", "*.*")]
        )
        if not new_files:
            return

        added = 0
        for f in new_files:
            if f not in files:
                files.append(f)
                file_listbox.insert(tk.END, f)
                added += 1

        if added > 0 and not iso_var.get():
            # Default output ISO path based on first file
            first = files[0]
            base = os.path.splitext(os.path.basename(first))[0]
            default_iso = os.path.join(os.path.dirname(first), base + ".iso")
            iso_var.set(default_iso)
            if not label_var.get():
                label_var.set(base)

    def clear_files():
        files.clear()
        file_listbox.delete(0, tk.END)

    def browse_iso():
        initial = iso_var.get()
        init_dir = ""
        init_file = ""

        if initial:
            init_dir = os.path.dirname(initial)
            init_file = os.path.basename(initial)
        elif files:
            first = files[0]
            init_dir = os.path.dirname(first)
            init_file = os.path.splitext(os.path.basename(first))[0] + ".iso"

        path = filedialog.asksaveasfilename(
            title="Save ISO as",
            defaultextension=".iso",
            filetypes=[("ISO files", "*.iso")],
            initialdir=init_dir,
            initialfile=init_file
        )
        if not path:
            return
        iso_var.set(path)

    def do_convert():
        if not files:
            messagebox.showerror("Error", "Please add at least one file.")
            return

        out_iso = iso_var.get().strip()
        if not out_iso:
            messagebox.showerror("Error", "Please choose where to save the ISO.")
            return

        label = label_var.get().strip() or None

        status_var.set("Creating ISO...")
        root.update_idletasks()

        try:
            build_iso(files, out_iso, label=label)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create ISO:\n{e}")
            status_var.set("Error creating ISO.")
            return

        status_var.set("ISO created successfully.")
        messagebox.showinfo("Done", f"ISO created:\n{out_iso}")

    # ---- Layout ----

    pad = 8
    frm = tk.Frame(root, padx=pad, pady=pad)
    frm.pack(fill="both", expand=True)

    # File list label
    tk.Label(frm, text="Files to include:").grid(row=0, column=0, sticky="w")

    # Listbox + scrollbar
    file_listbox = tk.Listbox(frm, width=60, height=8)
    file_listbox.grid(row=1, column=0, columnspan=3, sticky="we")

    btn_add = tk.Button(frm, text="Add files...", command=add_files)
    btn_add.grid(row=2, column=0, sticky="w", pady=(pad, 0))

    btn_clear = tk.Button(frm, text="Clear list", command=clear_files)
    btn_clear.grid(row=2, column=1, sticky="w", pady=(pad, 0))

    # Label field
    tk.Label(frm, text="Disc label:").grid(row=3, column=0, sticky="w", pady=(pad, 0))
    tk.Entry(frm, textvariable=label_var, width=30).grid(
        row=3, column=1, columnspan=2, sticky="we", pady=(pad, 0)
    )

    # ISO output
    tk.Label(frm, text="Output ISO:").grid(row=4, column=0, sticky="w", pady=(pad, 0))
    tk.Entry(frm, textvariable=iso_var, width=50).grid(
        row=4, column=1, sticky="we", padx=(0, pad), pady=(pad, 0)
    )
    tk.Button(frm, text="Browse...", command=browse_iso).grid(
        row=4, column=2, pady=(pad, 0)
    )

    # Convert button
    tk.Button(frm, text="Create ISO", command=do_convert).grid(
        row=5, column=0, columnspan=3, pady=(pad, 0)
    )

    # Status line
    tk.Label(frm, textvariable=status_var, anchor="w").grid(
        row=6, column=0, columnspan=3, sticky="we", pady=(pad, 0)
    )

    frm.columnconfigure(0, weight=0)
    frm.columnconfigure(1, weight=1)
    frm.columnconfigure(2, weight=0)

    root.mainloop()


if __name__ == "__main__":
    # With args → CLI (legacy single-file mode)
    if len(sys.argv) == 3:
        cli_main()
    else:
        # No args → GUI
        launch_gui()
