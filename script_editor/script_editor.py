#!/usr/bin/env python
'''
script_editor.py: GUI tool for parsing OCR'd script files into Script_markdown
'''

__author__ = 'bapril'

import Tkinter as tk
import ttk
import tkFileDialog
import tkMessageBox
import os
import shutil
import glob
from sys import platform
import pypdfocr.pypdfocr_gs as pdfImg
import script_render_engine
import script_parse_engine
import script_ck
from PIL import Image
from PIL import ImageTk

class ScriptEditor(tk.Frame):
    """Main GUI Class for ScriptEditor"""
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        #Variables.
        self.page = 1
        self.file_saved = True # Changes to false when a file has been changed but not saved.
        self.max_page = 0
        self.dir_path = ""
        self.edit_page_path = ""
        self.tiff_im = None

        self.menubar = tk.Menu(self)
        self.__build_menubar()
        self.parent = parent
        self.__create_content_grid()
        self.__create_frames()
        self.__build_page_list()
        self.__create_notebook()

        #PDF Input Tab
        self.pdf_label = tk.Label(self.pdf_tab, image=None)
        self.pdf_label.pack(fill="both", expand="yes")

        #TIFF Input Tab
        self.tiff_label = tk.Label(self.tiff_tab, image=None)
        self.tiff_label.pack(fill="both", expand="yes")

        #OCR Input Tab
        self.ocr_text = tk.Text(self.ocr_tab)
        self.ocr_text.config(state=tk.DISABLED)
        self.ocr_text.pack(fill="both", expand="yes")

        #TXT Input Tab
        self.text_text = tk.Text(self.text_tab)
        self.text_text.focus()
        self.text_text.pack(fill="both", expand="yes")
        self.text_text.bind('<Key>', self.change_callback)
        self.text_text.bind('<<Modified>>', self.change_callback)
        # attach popup to frame
        self.text_text.bind('<Button-2>', self.edit_menu_popup_event)

        #Rendered View
        self.rendered_text = tk.Text(self.render_frame)
        self.rendered_text.config(state=tk.DISABLED)
        self.rendered_text.pack(fill="both", expand="yes")
        self.text_parse_engine = script_parse_engine.ScriptParseEngine(
            self.text_text
        )
        self.text_render_engine = script_render_engine.ScriptRenderEngine(
            self.rendered_text,
            self.text_parse_engine)

        self.__build_buttons()

        sticky_all = ("N", "S", "E", "W")
        self.page_list_frame.grid(sticky=sticky_all, row=0, column=0)
        self.input_notebook.grid(sticky=sticky_all, row=0, column=1)
        self.render_frame.grid(sticky=sticky_all, row=0, column=2)
        self.page_control_frame.grid(sticky=sticky_all, row=1, column=0)
        self.input_control_frame.grid(sticky=sticky_all, row=1, column=1)
        self.render_control_frame.grid(sticky=sticky_all, row=1, column=2)

        self.content.pack(fill="both", expand="yes")

        # Check if we're on OS X, first.
        if platform == 'darwin':
            from Foundation import NSBundle
            bundle = NSBundle.mainBundle()
            if bundle:
                info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                if info and info['CFBundleName'] == 'Python':
                    info['CFBundleName'] = "ScriptEditor"

        self.parent.config(menu=self.menubar)

    def __build_buttons(self):
        self.page_next_button = tk.Button(
            self.page_control_frame,
            text="Next Page",
            command=self.next_page)
        self.page_next_button.grid(row=0, column=0)
        self.page_prev_button = tk.Button(
            self.page_control_frame,
            text="Prev. Page",
            command=self.prev_page)
        self.page_prev_button.grid(row=1, column=0)
        self.text_save_button = tk.Button(
            self.input_control_frame,
            text="Save",
            command=self.text_save)
        self.text_save_button.grid(row=0, column=0)
        self.text_reload_button = tk.Button(
            self.input_control_frame,
            text="Reload",
            command=self.text_reload)
        self.text_reload_button.grid(row=0, column=1)
        self.render_update_button = tk.Button(
            self.render_control_frame,
            text="Update",
            command=self.text_render_engine.update)
        self.render_update_button.grid(row=0, column=0)
        self.generate_output_button = tk.Button(
            self.render_control_frame,
            text="Output",
            command=self.render_output)
        self.generate_output_button.grid(row=1, column=0)

    def __create_notebook(self):
        #Tabs of Input
        self.pdf_tab = tk.Frame(self.input_notebook)
        self.tiff_tab = tk.Frame(self.input_notebook)
        self.ocr_tab = tk.Frame(self.input_notebook)
        self.text_tab = tk.Frame(self.input_notebook)
        self.input_notebook.add(self.pdf_tab, text='PDF')
        self.input_notebook.add(self.tiff_tab, text='TIFF')
        self.input_notebook.add(self.ocr_tab, text='OCR')
        self.input_notebook.add(self.text_tab, text='TXT')

    def __build_page_list(self):
        #List of pages
        self.page_list_scrollbar = tk.Scrollbar(self.page_list_frame, orient=tk.VERTICAL)
        self.page_list_box = tk.Listbox(
            self.page_list_frame,
            yscrollcommand=self.page_list_scrollbar.set,
            selectmode=tk.SINGLE,
            width=5)
        self.page_list_box.bind('<<ListboxSelect>>', self.on_page_select)
        self.page_list_scrollbar.config(command=self.page_list_box.yview)
        self.page_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.page_list_box.pack(side=tk.LEFT, fill="both", expand="yes")

    def __create_frames(self):
        self.page_list_frame = tk.LabelFrame(self.content, text="Pages")
        self.input_notebook = ttk.Notebook(self.content)
        self.render_frame = tk.LabelFrame(self.content, text="Rendered Script")
        self.page_control_frame = tk.Frame(self.content)
        self.input_control_frame = tk.Frame(self.content)
        self.render_control_frame = tk.Frame(self.content)

    def __create_content_grid(self):
        """Create the grid to layout the main window"""
        self.content = ttk.Frame(self.parent)
        tk.Grid.rowconfigure(self.content, 1, weight=0)
        tk.Grid.rowconfigure(self.content, 0, weight=1000)
        tk.Grid.columnconfigure(self.content, 0, weight=0)
        tk.Grid.columnconfigure(self.content, 1, weight=1)
        tk.Grid.columnconfigure(self.content, 2, weight=1)

    def __build_menubar(self):
        """Create the Menubar for the application"""
        filemenu = tk.Menu(self.menubar, tearoff=0)
        filemenu.add_command(label="Open", command=self.on_file_open)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        self.menubar.add_cascade(label="File", menu=filemenu)

        # create an edit popup menu
        self.edit_menu_popup = tk.Menu(self, tearoff=0)
        self.edit_menu_popup.add_command(label="Char", command=lambda: self.edit_swap_txt('char'))
        self.edit_menu_popup.add_command(label="Enter", command=lambda: self.edit_swap_txt('enter'))
        self.edit_menu_popup.add_command(label="Exit", command=lambda: self.edit_swap_txt('exit'))
        self.edit_menu_popup.add_command(label="Stage Direction", \
            command=lambda: self.edit_swap_txt('sd'))
        self.edit_menu_popup.add_command(label="Page", command=lambda: self.edit_swap_txt('page'))
        self.edit_menu_popup.add_command(label="Location", \
            command=lambda: self.edit_swap_txt('location'))
        self.edit_menu_popup.add_command(label="act", command=lambda: self.edit_swap_txt('act'))
        self.edit_menu_popup.add_command(label="scene", command=lambda: self.edit_swap_txt('scene'))

    def render_output(self):
        """Combine the set of .txt files in order into one output"""
        #TODO Setup license before output.
        # Select file to save as
        opts = {}
        opts['title'] = 'Select Output file to save.'
        opts['defaultextension'] = '.script'
        opts['initialfile'] = 'output.script'
        filename = tkFileDialog.asksaveasfilename(**opts)
        #open file:
        out_file = open(filename, 'w')
        # Walk txt files combine into one.
        for i in range(1, self.max_page + 1):
            read_file = "%s/text_pages/pg_%04d.txt" % (self.dir_path, i)
            f_read = open(read_file, "r")
            out_file.write(f_read.read())
            f_read.close()
        out_file.close()
        out_file = open(filename, 'r')
        file_parse_engine = script_parse_engine.ScriptParseEngine(out_file)
        file_sck_engine = script_ck.ScriptCk(
                    self.rendered_text,
                    file_parse_engine)
        file_sck_engine.update()
        out_file.close()

    def edit_menu_popup_event(self, event):
        """Link the edit menu"""
        self.edit_menu_popup.post(event.x_root, event.y_root)

    def on_page_select(self, evt):
        """Triggered when a page is selected from the page_list"""
        widget = evt.widget
        if widget.curselection() != ():
            index = int(widget.curselection()[0])
            if self.page != (index + 1):
                self.page = index + 1
                self.update_page(self.page)

    def text_reload(self):
        """replace the TEXT data with a fresh copy from the file"""
        self.update_page(self.page)
        self.file_saved = True
        self.file_saved_true()

    def text_save(self):
        """Save the current text in the file"""
        page_text = self.text_text.get("1.0", tk.END)
        t_file = open(self.edit_page_path, 'w')
        t_file.write(page_text.encode('utf-8'))
        t_file.close()
        self.file_saved = True
        self.file_saved_true()

    def change_callback(self, _evt):
        """Triggers when the text is changed"""
        self.file_saved = False
        self.file_saved_false()

    def edit_swap_txt(self, txt):
        """function to generate the replacement for an arbitrary tag name"""
        content = self.text_text.get(tk.SEL_FIRST, tk.SEL_LAST)
        self.text_text.delete(tk.SEL_FIRST, tk.SEL_LAST)
        self.text_text.insert(tk.CURRENT, "#"+txt+"("+content+")")

    def update_page(self, index):
        """Triggers when page is changed, displays images and text, renders output"""
        if self.dir_path != "":
            orig_file = "%s/text_pages/pg_%04d.txt.orig" % (self.dir_path, index)
            self.edit_page_path = ("%s/text_pages/pg_%04d.txt" % (self.dir_path, index))
            if os.path.isfile(orig_file) != True:
                shutil.copyfile(self.edit_page_path, orig_file)
            self.ocr_text.config(state=tk.NORMAL)
            self.ocr_text.delete('1.0', tk.END)
            self.text_text.delete('1.0', tk.END)
            txt_file = open(self.edit_page_path, 'r')
            self.page_list_box.itemconfig(index - 1, {'bg':'blue'})
            page_text = txt_file.read()
            self.text_text.insert('1.0', page_text)
            ocr_file = open(orig_file, 'r')
            self.ocr_text.insert('1.0', ocr_file.read())
            self.ocr_text.config(state=tk.DISABLED)

            txt_file.close()
            self.text_render_engine.update()

            tiff_file = "%s/tiff_pages/pg_%04d.tiff" % (self.dir_path, index)
            tiff_img = Image.open(tiff_file)
            tiff_img = tiff_img.resize((500, 600), Image.ANTIALIAS)
            tiff_im = ImageTk.PhotoImage(tiff_img)
            self.tiff_label.config(image=tiff_im)
            self.tiff_label.image = tiff_im

            pdf_file = "%s/pdf_pages/pg_%04d.pdf" % (self.dir_path, index)
            pdf_fh = glob.glob(pdfImg.PyGs({}).make_img_from_pdf(pdf_file)[1])[0]
            pdf_img = Image.open(pdf_fh)
            pdf_img = pdf_img.resize((500, 600), Image.ANTIALIAS)
            tk_pdf_img = ImageTk.PhotoImage(pdf_img)
            self.pdf_label.config(image=tk_pdf_img)
            self.pdf_label.image = tk_pdf_img
            pdf_img.close()
            os.remove(pdf_fh)
            self.page = index

    def prev_page(self):
        """Triggered when previous page button pressed"""
        if self.page > 1:
            page = self.page - 1
            self.page_list_box.see(page - 1)
            self.page_list_box.selection_clear(page)
            #This only sets focus on the first item.
            self.page_list_box.select_set(page - 1, last=None)
            self.update_page(page)

    def next_page(self):
        """Triggered when next_page button pressed"""
        if self.page < self.max_page:
            page = self.page + 1
            self.page_list_box.see(page - 1)
            #This only sets focus on the first item.
            self.page_list_box.select_set(page - 1, last=None)
            self.page_list_box.selection_clear(page - 2)
            self.update_page(page)

    def load_dir(self):
        """Load pages from the specified Directory"""
        #Check for pdf_pages
        if os.path.isdir(self.dir_path+'/pdf_pages'):
            print "found PDF_Pages"
        else:
            tkMessageBox.showinfo("Error loading project", self.dir_path+'/pdf_pages not found!')
            self.dir_path = ""
            return
        #check for tiff_pages
        if os.path.isdir(self.dir_path+'/tiff_pages'):
            print "found tiff_Pages"
        else:
            tkMessageBox.showinfo("Error loading project", self.dir_path+'/tiff_pages not found!')
            self.dir_path = ""
            return
        #check for text_pages
        if os.path.isdir(self.dir_path+'/text_pages'):
            print "found text_Pages"
        else:
            tkMessageBox.showinfo("Error loading project", self.dir_path+'/text_pages not found!')
            self.dir_path = ""
            return
        #walk tiff_pages and generate page_list.
        i = 1
        for tiff_pg in os.listdir(self.dir_path+'/tiff_pages'):
            if os.path.isfile(self.dir_path+'/tiff_pages/'+tiff_pg):
                self.page_list_box.insert(tk.END, i)
                orig_file = "%s/text_pages/pg_%04d.txt.orig" % (self.dir_path, i)
                if os.path.isfile(orig_file):
                    self.page_list_box.itemconfig(i - 1, {'bg':'blue'})

                i = i + 1
        self.file_saved = True
        self.max_page = i - 1
        self.page = 1
        self.page_list_box.select_set(0) #This only sets focus on the first item.
        self.update_page(self.page)
        self.file_saved_true()

    def file_saved_true(self):
        """Allow navigation to other pages now that we are saved."""
        self.page_next_button.config(state='normal')
        self.page_prev_button.config(state='normal')
        self.text_save_button.config(state='disabled')

    def file_saved_false(self):
        """Forbid navigation to new pages when the current text has changed"""
        self.page_next_button.config(state='disabled')
        self.page_prev_button.config(state='disabled')
        self.text_save_button.config(state='normal')

    def on_file_open(self):
        """Triggered on menu FILE->OPEN"""
        opts = {}
        opts['title'] = 'Open an existing project'
        self.dir_path = tkFileDialog.askdirectory(**opts)
        if self.dir_path != "":
            self.load_dir()

if __name__ == '__main__':
    ROOT = tk.Tk()
    ROOT.title("ShowControl:ScriptEditor v0.0.3")
    ScriptEditor(ROOT).pack(side="top", fill="both", expand=True)
    ROOT.mainloop()
