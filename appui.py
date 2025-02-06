from pathlib import Path
import tkinter.filedialog as tkfd

import customtkinter as ctk

import subtitling
from constants import valid_video_file_types
from script_running import run_on_button_press

class appUI:

    def __init__(self):
        self.root = ctk.CTk()

        self.bigframe = ctk.CTkFrame(self.root)

        #self.model_id = "openai/whisper-large-v3-turbo"

        #UI elements for choosing file(s) to process
        self.path = ctk.StringVar(value=str(Path.cwd()))
        self.input_mode = ctk.StringVar(value = "Single File")

        self.location_frame = LocationFrameUI(self.bigframe, self.path, self.input_mode)

        self.location_frame.pack(fill = "both", expand=1, padx = 20, pady = 20)

        self.model_name = ctk.StringVar()
        self.model_selection_frame = ModelSelectionFrameUI(self.bigframe, self.model_name)

        self.model_selection_frame.pack(expand=True, fill='both', padx = 20, pady = (0,20))

        #UI elements relating to language mode
        self.lang_selection = ctk.StringVar(value = "Auto-Detect Single Language")
        self.replace_lang = ctk.IntVar()
        self.selected_lang = ctk.StringVar()
        self.lang_frame = LangFrameUI(self.bigframe, self.lang_selection, self.replace_lang, self.selected_lang)

        self.lang_frame.pack(expand=True, fill='both', padx = 20)

        self.confirm_frame = ctk.CTkFrame(self.bigframe)

        self.replace = ctk.IntVar(value=0)
        self.replace_check = ctk.CTkCheckBox(self.confirm_frame, variable=self.replace, text="Overwrite any existing subtitle files")

        self.confirm_button = ctk.CTkButton(self.confirm_frame, text="Create Subtitles", command=lambda: run_on_button_press(self))

        self.replace_check.grid(row=0, column=0, sticky="nsew", padx = 10, pady = 5)
        self.confirm_button.grid(row=1, column=0, columnspan = 2, padx = 10, pady = 5)

        self.confirm_frame.pack(expand=True, fill='both', padx = 20, pady = 20)

        self.bigframe.pack(expand=True, fill='both')
        self.root.mainloop()

class  LocationFrameUI(ctk.CTkFrame):
    def __init__(self, master, path, input_mode):
        super().__init__(master)
        #UI elements for choosing file(s) to process
        self.columnconfigure(0, weight=2)

        #Open file explorer if looking for single file, and folder explorer otherwise
        def file_explore():
            if input_mode.get() == "Single File":
                location = tkfd.askopenfile(
                    title="Open File",
                    initialdir=path.get(),
                    filetypes = [("Video File", " ".join(valid_video_file_types))]
                )
                path.set(location.name)
            else:
                location = tkfd.askdirectory(
                    title="Open Folder",
                    initialdir=path.get()
                )
                path.set(location)

        self.input_mode_options = ["Single File", "Folder"]

        self.input_mode_selection = ctk.CTkComboBox(self, values = self.input_mode_options, variable=input_mode)
        self.include_subfolders = ctk.IntVar()
        self.include_subfolders_checkbox = ctk.CTkCheckBox(self, text = "Include all subfolders", variable = self.include_subfolders)

        self.video_location_lab = ctk.CTkLabel(self, text="Please select Location:")
        self.video_location = ctk.CTkEntry(self, textvariable=path)
        self.file_open = ctk.CTkButton(self, text = "Browse", command=file_explore)


        self.video_location_lab.grid(row=0, column = 0, padx = 5, pady = 5, columnspan = 3)
        self.video_location.grid(row = 1, column = 0, sticky = "EW", padx = 10, pady = 5)
        self.file_open.grid(row = 1, column = 1, padx = 10, pady = 5)

        self.input_mode_selection.grid(row = 3, column = 0, sticky="nsew", padx = 10, pady = 5)
        self.include_subfolders_checkbox.grid(row = 3, column = 1, sticky="nsew", padx = 10, pady = 5)

        self.include_subfolders_checkbox.grid_forget()

        def toggle_include_subfolders_visablilty(*args):
            selected_item = input_mode.get()
            if selected_item == "Folder":
                self.include_subfolders_checkbox.grid(row = 3, column = 1, sticky="nsew", padx = 10, pady = 5)
            else:
                self.include_subfolders_checkbox.grid_forget()

        input_mode.trace_add("write", toggle_include_subfolders_visablilty)

class ModelSelectionFrameUI(ctk.CTkFrame):
    def __init__(self, master, model_name):
        super().__init__(master)  

        self.models = ["WhisperLargeV3", "WhisperLargeV3-Turbo"]
        self.model_selection_choices = ctk.CTkComboBox(self, variable=model_name, values=self.models)

        self.model_label = ctk.CTkLabel(self, text = "Choose model:")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.model_label.grid(row = 0, column = 0, sticky = "EW", padx = 10, pady = 5)
        self.model_selection_choices.grid(row=0, column = 1, sticky = "EW", padx = 10, pady = 5)


class LangFrameUI(ctk.CTkFrame):
    def __init__(self, master, lang_selection, replace_lang, selected_lang):
        super().__init__(master)

        #Enable or disable elements based on currently selected language mode
        def lang_selction_switching():
            if lang_selection.get() == "Auto-Detect Single Language":
                self.replace_lang_checkbox.configure(state = ctk.NORMAL)
                self.lang_selection_choices.configure(state = ctk.DISABLED)
            elif lang_selection.get() == "Auto-Detect Multiple Language":
                self.replace_lang_checkbox.configure(state = ctk.DISABLED)
                self.lang_selection_choices.configure(state = ctk.DISABLED)
            elif lang_selection.get() == "Choose Language":
                self.replace_lang_checkbox.configure(state = ctk.DISABLED)
                self.lang_selection_choices.configure(state = ctk.NORMAL)

        #Radio Buttons to switch between language modes
        self.lang_selection_asingle = ctk.CTkRadioButton(self, text = "Auto-Detect Single Language", command = lang_selction_switching, variable = lang_selection, value = "Auto-Detect Single Language")
        self.lang_selection_amulti = ctk.CTkRadioButton(self, text = "Auto-Detect Multiple Language", command = lang_selction_switching, variable = lang_selection, value = "Auto-Detect Multiple Language")
        self.lang_selection_msingle = ctk.CTkRadioButton(self, text = "Choose Language", command = lang_selction_switching, variable = lang_selection, value = "Choose Language")

        #self.replace_lang = ctk.IntVar()
        self.replace_lang_checkbox = ctk.CTkCheckBox(self, text = "Replace any previously generated language detections", variable = replace_lang)

        #Manual language selection, from list of available languages
        self.langs = ["English", "Spanish"]

        self.lang_selection_choices = ctk.CTkComboBox(self, variable=selected_lang, values=self.langs, state=ctk.DISABLED)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.lang_selection_asingle.grid(row=0, column=0, sticky="nsew", padx = 10, pady = 5)
        self.lang_selection_amulti.grid(row=1, column=0, sticky="nsew", padx = 10, pady = 5)
        self.lang_selection_msingle.grid(row=2, column=0, sticky="nsew", padx = 10, pady = 5)

        self.replace_lang_checkbox.grid(row=0, column=1, sticky="nsew", padx = 10, pady = 5)
        self.lang_selection_choices.grid(row=2,column=1, sticky="ew", padx = 10, pady = 5)

def set_input_mode(input_mode):
    """Translates selected input mode to correct internal string."""
    if input_mode == "Single File":
        return "file"
        
    elif input_mode == "Folder":
        return "folder"

if __name__ == "__main__":
    UI = appUI()
