import os
import sys
import threading
import subprocess
import io
import customtkinter as ctk
import tkinter as tk 
from tkinter import messagebox
from main import main as generate_owner_data

ctk.set_appearance_mode("dark")  # "dark" or "light"
ctk.set_default_color_theme("dark-blue")  # optional theme

class MinimalToolUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        with open("version.txt", "r") as f:
            version = f.read().strip()  # 'v1.0.0'

        self.title(f"Generate Owner Data {version}")
        self.geometry("620x480")
        self.configure(fg_color="#273946")  # dark charcoal background

        self.dots_running = False
        self.dots_count = 0

        self.wait_dots_running = False
        self.wait_popup_dots = 0

        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        self.database_folder = os.path.join(base_dir, "bu_database")
        self.input_folder = os.path.join(base_dir, "files_to_process")

        os.makedirs(self.database_folder, exist_ok=True)
        os.makedirs(self.input_folder, exist_ok=True)

        # Title label
        self.title_label = ctk.CTkLabel(self,
                                        text="Generate Owner Data",
                                        text_color="#fff6de",
                                        font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"))
        self.title_label.pack(pady=(20, 5))

        # Button frame
        btn_frame = ctk.CTkFrame(self, fg_color="#273946", corner_radius=0)
        btn_frame.pack(pady=5)

        # Buttons with rounded corners
        self.open_db_btn = ctk.CTkButton(btn_frame, text="Open database folder",
                                      fg_color="#CB1F47",
                                      hover_color="#ffab4c",
                                      command=self.open_database_folder)
        self.open_db_btn.pack(side="left", padx=5)

        self.open_input_btn = ctk.CTkButton(btn_frame, text="Open files_to_process folder",
                                      fg_color="#CB1F47",
                                      hover_color="#ffab4c",
                                      command=self.open_input_folder)
        self.open_input_btn.pack(side="left", padx=5)

        self.refresh_btn = ctk.CTkButton(btn_frame, text="Refresh",
                                         fg_color="#CB1F47",
                                         hover_color="#ffab4c",
                                         command=self.refresh_all)
        self.refresh_btn.pack(side="left", padx=5)


        self.list_container = ctk.CTkFrame(self, fg_color="#273946", corner_radius=0)
        self.list_container.pack(padx=20, pady=10, fill="x")

        self.file_text = tk.Text(self.list_container,
                                height=8,
                                bg="#fff6de",
                                fg="#273946",
                                font=("Segoe UI", 11),
                                highlightthickness=0,
                                relief="flat",
                                wrap="none")
        self.file_text.pack(side="left", fill="both", expand=True, padx=(5,0), pady=5)

        scrollbar = tk.Scrollbar(self.list_container, command=self.file_text.yview)
        scrollbar.pack(side="right", fill="y", padx=(0,5), pady=5)
        self.file_text.config(yscrollcommand=scrollbar.set)

        # Define font style tag
        self.file_text.tag_configure("header", font=("Segoe UI", 11, "bold"))
        self.file_text.tag_configure("italic", font=("Segoe UI", 11, "italic"))


        # Instruction label
        self.instruction_label = ctk.CTkLabel(self,
                                             text="",
                                             text_color="#BBB8A6",
                                             wraplength=550,
                                             justify="center",
                                             font=ctk.CTkFont(family="Segoe UI", size=12))
        self.instruction_label.pack(pady=5)

        # Message label
        self.message_label = ctk.CTkLabel(self,
                                          text="Waiting to start...",
                                          text_color="#BBB8A6",
                                          font=ctk.CTkFont(family="Segoe UI", size=12))
        self.message_label.pack(pady=5)

        # Progress bar
        self.progress = ctk.CTkProgressBar(
            self,
            width=500,
            fg_color="#444444",
            progress_color="#CB1F47"
            )
        self.progress.set(0)
        self.progress.pack(pady=10)

        # Run button
        self.run_btn = ctk.CTkButton(
            self,
            text="GENERATE RESULTS",
            width=120,
            height=40,  # fix height
            corner_radius=8,  # fix corner radius
            fg_color="#CB1F47",
            hover_color="#ffab4c",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self.run_tool
        )
        self.run_btn.pack(pady=15)

        self.refresh_all()

    def open_database_folder(self):
        folder = self.database_folder
        if os.path.isdir(folder):
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])
        else:
            messagebox.showerror("Error", f"Database folder not found:\n{folder}")

    def open_input_folder(self):
        folder = self.input_folder
        if os.path.isdir(folder):
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])
        else:
            messagebox.showerror("Error", f"Input folder not found:\n{folder}")

    def open_folder(self, folder):
        if os.path.isdir(folder):
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])
        else:
            messagebox.showerror("Error", f"Folder not found:\n{folder}")

    def load_folder_files(self, folder, exts):
        """Return a list of files in the folder with given extensions."""
        if not os.path.isdir(folder):
            return []
        return sorted(
            f for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith(exts)
        )

    def refresh_all(self):
    
        # Reset messages and progress
        self.message_label.configure(text="Waiting to start...")
        self.progress.set(0)
        self.dots_running = False
        
        # Clear any previous wait popup if somehow left open
        if hasattr(self, "wait_popup"):
            self.close_wait_popup()

        """Refresh input (.xlsx/.csv) and database (.db) folders, update listbox, and re-check."""
        self.file_text.configure(state="normal")  # <-- re-enable editing
        self.file_text.delete("1.0", "end")

        self.input_files = self.load_folder_files(self.input_folder, (".xlsx", ".csv"))
        self.db_files = self.load_folder_files(self.database_folder, (".db",))

        # Database section
        self.file_text.insert("end", "Bottoms-up Database File:\n", "header")
        if self.db_files:
            for f in self.db_files:
                self.file_text.insert("end", f + "\n")
        else:
            self.file_text.insert("end", "  No files found\n", "italic")
        self.file_text.insert("end", "\n")

        # Input section
        self.file_text.insert("end", "Files to Process:\n", "header")
        if self.input_files:
            for f in self.input_files:
                self.file_text.insert("end", f + "\n")
        else:
            self.file_text.insert("end", "  No files found\n", "italic")

        self.file_text.configure(state="disabled")  # <-- lock after finishing
        self.check_files_ready()


    def check_files_ready(self):
        input_ok = bool(self.input_files)
        db_ok = bool(self.db_files)

        if input_ok and db_ok:
            self.run_btn.configure(state="normal")
            self.instruction_label.configure(
                text="Ready! Click GENERATE RESULTS. Otherwise, update the folders."
            )
        else:
            self.run_btn.configure(state="disabled")
            if not input_ok and not db_ok:
                self.instruction_label.configure(
                    text="Add files to BOTH the input and database folders, then click Refresh."
                )
            elif not input_ok:
                self.instruction_label.configure(
                    text="Add the files to be processed in the input folder, then click Refresh."
                )
            elif not db_ok:
                self.instruction_label.configure(
                    text="Add the database file in the database folder, then click Refresh."
                )

    def log_message(self, message):
        self.message_label.configure(text=message)
        self.update_idletasks()
    
    # def update_progress(self, fraction, filename=None):
    #     self.progress.set(fraction)
    #     self.message_label.configure(text=f"{int(fraction*100)}% completed")
        
    #     if filename and hasattr(self, "wait_label"):
    #         # Store the filename in a dedicated attribute
    #         self.wait_popup_filename = filename
    #         # Update label immediately with current dots count
    #         dots = "." * self.wait_popup_dots
    #         self.wait_label.configure(text=f"Processing{dots}\n{self.wait_popup_filename}")

    def update_progress(self, fraction, filename=None):
        self.progress.set(fraction)
        self.message_label.configure(text=f"{int(fraction*100)}% completed")
        
        if filename and getattr(self, "wait_label", None) and self.wait_label.winfo_exists():
            # Update popup only if it exists
            self.wait_popup_filename = filename
            dots = "." * self.wait_popup_dots
            self.wait_label.configure(text=f"Processing{dots}\n{self.wait_popup_filename}")


    def run_tool(self):
        folder = self.input_folder
        if not os.path.exists(folder):
            messagebox.showerror("Error", f"Input folder not found:\n{folder}")
            return
        
        self.instruction_label.configure(
            text="In progress... Please do not close the window"
        )
        self.message_label.configure(text=f"Running on folder: {folder} ...")
        self.progress.set(0)
        self.run_btn.configure(state="disabled")
        first_file = self.input_files[0] if self.input_files else None
        self.show_wait_popup(filename=first_file)

        threading.Thread(target=self.run_main_process, daemon=True).start()

    def show_wait_popup(self, filename=None):
        self.wait_popup = ctk.CTkToplevel(self)
        self.wait_popup.title("Please Wait")
        self.wait_popup.geometry("300x100")
        self.wait_popup.resizable(False, False)
        self.wait_popup.transient(self)
        self.wait_popup.grab_set()

        # Store filename for animation
        self.wait_popup_filename = filename

        display_text = f"Processing\n{filename}" if filename else "Processing..."
        self.wait_label = ctk.CTkLabel(
            self.wait_popup,
            text=display_text,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            wraplength=250,
            justify="center"
        )
        self.wait_label.pack(expand=True, pady=20)

        self.wait_dots_running = True
        self.animate_wait_popup()


    def animate_wait_popup(self):
        if not getattr(self, "wait_dots_running", False):
            return
        self.wait_popup_dots = (self.wait_popup_dots + 1) % 4
        dots = "." * self.wait_popup_dots

        # Keep whatever text is already set (filename)
        current_text = self.wait_label.cget("text")
        if "\n" in current_text:
            parts = current_text.split("\n", 1)
            self.wait_label.configure(text=f"Processing{dots}\n{parts[1]}")
        else:
            self.wait_label.configure(text=f"Processing{dots}...")
        self.wait_label.after(500, self.animate_wait_popup)

    def animate_wait_popup(self):
        if not getattr(self, "wait_dots_running", False):
            return
        if not getattr(self, "wait_label", None) or not self.wait_label.winfo_exists():
            return  # popup was closed, stop animating

        self.wait_popup_dots = (self.wait_popup_dots + 1) % 4
        dots = "." * self.wait_popup_dots

        # Keep whatever text is already set (filename)
        current_text = self.wait_label.cget("text")
        if "\n" in current_text:
            parts = current_text.split("\n", 1)
            self.wait_label.configure(text=f"Processing{dots}\n{parts[1]}")
        else:
            self.wait_label.configure(text=f"Processing{dots}...")

        self.wait_label.after(500, self.animate_wait_popup)


    def close_wait_popup(self):
        if getattr(self, "wait_popup", None) is not None:
            try:
                if self.wait_popup.winfo_exists():
                    self.wait_popup.destroy()
            except Exception:
                pass
            finally:
                self.wait_popup = None

    def animate_dots(self):
            if not self.dots_running:
                return
            self.dots_count = (self.dots_count + 1) % 4
            dots = "." * self.dots_count
            base_text = f"Running on folder: {self.input_folder}"
            self.message_label.configure(text=base_text + dots)
            self.message_label.after(500, self.animate_dots)

    def run_main_process(self):
        try:
            if sys.stdout is None:
                sys.stdout = io.StringIO()
            if sys.stderr is None:
                sys.stderr = io.StringIO()

            base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            output_folder = os.path.join(base_dir, "results")

            generate_owner_data(
                INPUT_FOLDER=self.input_folder,
                OUTPUT_FOLDER=output_folder,
                BOTTOMS_UP_FOLDER=self.database_folder,
                logger=self.log_message,
                progress_callback=self.update_progress
            )

            self.dots_running = False
            self.close_wait_popup() 
            self.run_btn.configure(state="normal")
            self.update_message("Processing finished successfully!")
            self.progress.set(1.0)

            def ask_open_folder():
                if messagebox.askyesno("Done", "Processing finished!\nOpen output folder?"):
                    if not os.path.exists(output_folder):
                        os.makedirs(output_folder)
                    self.open_folder(output_folder)
            self.message_label.after(0, ask_open_folder)

        except Exception as e:
            self.dots_running = False
            self.wait_dots_running = False
            self.animate_wait_popup = False
            self.close_wait_popup()
            self.run_btn.configure(state="normal")

            # Check if popup was closed
            if getattr(self, "wait_popup", None) is None:
                message = "Processing failed: pop-up window was closed, causing the process to abort."
            else:
                message = f"Processing failed:\n{e}"

            self.update_message(f"Failed to generate results.\n\n{e}")
            messagebox.showerror("Error", f"Processing failed:\n{e}")
        
        finally:
            self.instruction_label.configure(
                text="Ready! Click GENERATE RESULTS. Otherwise, update the folders."
            )

    def update_message(self, text):
        self.message_label.after(0, lambda: self.message_label.configure(text=text))


if __name__ == "__main__":
    app = MinimalToolUI()
    app.mainloop()
