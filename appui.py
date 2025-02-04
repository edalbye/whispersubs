from pathlib import Path
import tkinter.filedialog as tkfd

import customtkinter as ctk

import subtitling
from constants import valid_video_file_types
from script_running import run_process

class appUI:

    def __init__(self):
        self.root = ctk.CTk()

        self.bigframe = ctk.CTkFrame(self.root)

        #UI elements for choosing file(s) to process
        self.location_frame = ctk.CTkFrame(self.bigframe)
        self.location_frame.columnconfigure(0, weight=2)

        self.path = ctk.StringVar(value=str(Path.cwd()))

        self.input_mode = ctk.StringVar(value = "Single File")

        #Open file explorer if looking for single file, and folder explorer otherwise
        def file_explore():
            if self.input_mode.get() == "Single File":
                location = tkfd.askopenfile(
                    title="Open File",
                    initialdir=self.path.get(),
                    filetypes = [("Video File", " ".join(valid_video_file_types))]
                )
                self.path.set(location.name)
            else:
                location = tkfd.askdirectory(
                    title="Open Folder",
                    initialdir=self.path.get()
                )
                print(location)
                self.path.set(location)

        self.input_mode_options = ["Single File", "Folder"]

        self.input_mode_selection = ctk.CTkComboBox(self.location_frame, values = self.input_mode_options, variable=self.input_mode)
        self.include_subfolders = ctk.IntVar()
        self.include_subfolders_checkbox = ctk.CTkCheckBox(self.location_frame, text = "Include all subfolders", variable = self.include_subfolders)

        self.video_location_lab = ctk.CTkLabel(self.location_frame, text="Please select Location:")
        self.video_location = ctk.CTkEntry(self.location_frame, textvariable=self.path)
        self.file_open = ctk.CTkButton(self.location_frame, text = "Browse", command=file_explore)


        self.video_location_lab.grid(row=0, column = 0, columnspan = 3)
        self.video_location.grid(row = 1, column = 0, sticky = "EW")
        self.file_open.grid(row = 1, column = 1)

        self.input_mode_selection.grid(row = 3, column = 0, sticky="nsew")
        self.include_subfolders_checkbox.grid(row = 3, column = 1, sticky="nsew")

        self.include_subfolders_checkbox.grid_forget()

        def toggle_include_subfolders_visablilty(*args):
            selected_item = self.input_mode.get()
            if selected_item == "Folder":
                self.include_subfolders_checkbox.grid(row = 3, column = 1, sticky="nsew")
            else:
                self.include_subfolders_checkbox.grid_forget()

        self.input_mode.trace_add("write", toggle_include_subfolders_visablilty)

        self.location_frame.pack(fill = "both", expand=1)

        #UI elements relating to language mode
        self.lang_frame = ctk.CTkFrame(self.bigframe)

        self.lang_selection = ctk.StringVar(value = "Auto-Detect Single Language")

        #Enable or disable elements based on currently selected language mode
        def lang_selction_switching():
            if self.lang_selection.get() == "Auto-Detect Single Language":
                self.replace_lang_checkbox.configure(state = ctk.NORMAL)
                self.lang_selection_choices.configure(state = ctk.DISABLED)
            elif self.lang_selection.get() == "Auto-Detect Multiple Language":
                self.replace_lang_checkbox.configure(state = ctk.DISABLED)
                self.lang_selection_choices.configure(state = ctk.DISABLED)
            elif self.lang_selection.get() == "Choose Language":
                self.replace_lang_checkbox.configure(state = ctk.DISABLED)
                self.lang_selection_choices.configure(state = ctk.NORMAL)

        #Radio Buttons to switch between language modes
        self.lang_selection_asingle = ctk.CTkRadioButton(self.lang_frame, text = "Auto-Detect Single Language", command = lang_selction_switching, variable = self.lang_selection, value = "Auto-Detect Single Language")
        self.lang_selection_amulti = ctk.CTkRadioButton(self.lang_frame, text = "Auto-Detect Multiple Language", command = lang_selction_switching, variable = self.lang_selection, value = "Auto-Detect Multiple Language")
        self.lang_selection_msingle = ctk.CTkRadioButton(self.lang_frame, text = "Choose Language", command = lang_selction_switching, variable = self.lang_selection, value = "Choose Language")

        self.replace_lang = ctk.IntVar()
        self.replace_lang_checkbox = ctk.CTkCheckBox(self.lang_frame, text = "Replace any previously generated language detections", variable = self.replace_lang)

        #Manual language selection, from list of available languages
        self.langs = ["English", "Spanish"]
        self.selected_lang = ctk.StringVar()
        self.lang_selection_choices = ctk.CTkComboBox(self.lang_frame, variable=self.selected_lang, values=self.langs, state=ctk.DISABLED)

        self.lang_frame.grid_rowconfigure(0, weight=1)
        self.lang_frame.grid_columnconfigure(0, weight=1)
        self.lang_frame.grid_rowconfigure(1, weight=1)
        self.lang_frame.grid_columnconfigure(1, weight=1)
        self.lang_frame.grid_rowconfigure(2, weight=1)

        self.lang_selection_asingle.grid(row=0, column=0, sticky="nsew")
        self.lang_selection_amulti.grid(row=1, column=0, sticky="nsew")
        self.lang_selection_msingle.grid(row=2, column=0, sticky="nsew")

        self.replace_lang_checkbox.grid(row=0, column=1, sticky="nsew")
        self.lang_selection_choices.grid(row=2,column=1, sticky="ew")

        self.lang_frame.pack(expand=True, fill='both')

        self.confirm_frame = ctk.CTkFrame(self.bigframe)

        self.replace = ctk.IntVar(value=0)
        self.replace_check = ctk.CTkCheckBox(self.confirm_frame, variable=self.replace, text="Overwrite any existing subtitle files")

        self.confirm_button = ctk.CTkButton(self.confirm_frame, text="Create Subtitles", command=lambda: run_process(self))

        self.replace_check.grid(row=0, column=0, sticky="nsew")
        self.confirm_button.grid(row=1, column=1, sticky="nsew")

        self.confirm_frame.pack(expand=True, fill='both')

        self.bigframe.pack(expand=True, fill='both')
        self.root.mainloop()

def set_input_mode(input_mode):
    """Translates selected input mode to correct internal string."""
    if input_mode == "Single File":
        return "file"
        
    elif input_mode == "Folder":
        return "folder"

if __name__ == "__main__":
    UI = appUI()
    