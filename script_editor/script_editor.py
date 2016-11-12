#!/usr/bin/env python
__author__ = 'bapril'

import Tkinter as tk
import ttk
import tkFileDialog
import tkMessageBox
import os, sys
import shutil
from PIL import Image
from PIL import ImageTk
import pypdfocr.pypdfocr_gs as pdfImg
import glob
import script_render_engine
import script_parse_engine
from sys import platform


class ScriptEditor(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        #Variables.
        self.page = 1
        self.file_saved = True # Changes to false when a file has been changed but not saved.
        self.max_page = 0
        self.project = None # Name of the current project.
        self.dir_path = ""
        self.edit_page_path = ""

        self.menubar = tk.Menu(self)
        self.build_menubar()
        self.create_content_grid()

        self.page_list_frame = tk.LabelFrame(self.content, text="Pages")
        self.input_notebook = ttk.Notebook(self.content)
        self.render_frame = tk.LabelFrame(self.content, text="Rendered Script")
        self.page_control_frame = tk.Frame(self.content)
        self.input_control_frame = tk.Frame(self.content)
        self.render_control_frame = tk.Frame(self.content)

        #List of pages
        self.page_list_scrollbar = tk.Scrollbar(self.page_list_frame, orient=tk.VERTICAL)
        self.page_list_box = tk.Listbox(
            self.page_list_frame,
            yscrollcommand=self.page_list_scrollbar.set,
            selectmode=tk.SINGLE)
        self.page_list_box.bind('<<ListboxSelect>>', self.on_page_select)
        self.page_list_scrollbar.config(command=self.page_list_box.yview)
        self.page_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.page_list_box.pack(side=tk.LEFT, fill="both", expand="yes")

        #Tabs of Input
        self.pdf_tab = tk.Frame(self.input_notebook)   # first page, which would get widgets gridded into it
        self.tiff_tab = tk.Frame(self.input_notebook)   # second page
        self.ocr_tab = tk.Frame(self.input_notebook)
        self.text_tab = tk.Frame(self.input_notebook)
        self.input_notebook.add(self.pdf_tab, text='PDF')
        self.input_notebook.add(self.tiff_tab, text='TIFF')
        self.input_notebook.add(self.ocr_tab, text='OCR')
        self.input_notebook.add(self.text_tab, text='TXT')

        #PDF Input Tab
        self.pdf_canvas = tk.Canvas(self.pdf_tab, height=250, width=300 )
        self.pdf_image = self.pdf_canvas.create_image(0, 0)
        self.pdf_canvas.pack(fill="both", expand="yes")

        #TIFF Input Tab
        #tiff_label = Tkinter.Canvas(tiff_tab, height=250, width=300)
        self.tiff_label = tk.Label(self.tiff_tab, height=250, width=300)
        self.tiff_label.pack(fill="both", expand="yes")

        #OCR Input Tab
        self.ocr_text = tk.Text (self.ocr_tab)
        self.ocr_text.config(state=tk.DISABLED)
        self.ocr_text.pack(fill="both", expand="yes")

        #TXT Input Tab
        self.text_text = tk.Text (self.text_tab)
        self.text_text.focus()
        self.text_text.pack(fill="both", expand="yes")
        self.text_text.bind('<<Modified>>', self.change_callback)

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

        self.page_next_button = tk.Button(
            self.page_control_frame,
            text="Next Page",
            command=self.next_page).grid(row=0, column = 1)
        self.page_prev_button = tk.Button(
            self.page_control_frame,
            text="Prev. Page",
            command=self.prev_page).grid(row=0, column = 0)

        self.text_save_button = tk.Button(
            self.input_control_frame,
            text="Save",
            command=self.text_save).grid(row=0, column = 0)
        self.text_reload_button = tk.Button(
            self.input_control_frame,
            text="Reload",
            command=self.text_reload).grid(row=0, column = 1)
        self.render_update_button = tk.Button(
            self.render_control_frame,
            text="Update",
            command=self.text_render_engine.update).grid(row=0,column = 0)

        sticky_all=("N","S","E","W")
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


        self.parent = parent
        self.parent.config(menu=self.menubar)

    def create_content_grid(self):
        self.content = ttk.Frame(root)
        tk.Grid.rowconfigure(self.content, 0, weight=6)
        tk.Grid.rowconfigure(self.content, 1, weight=1)
        tk.Grid.columnconfigure(self.content, 0, weight=1)
        tk.Grid.columnconfigure(self.content, 1, weight=8)
        tk.Grid.columnconfigure(self.content, 2, weight=8)

    def build_menubar(self):
        filemenu = tk.Menu(self.menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.on_file_new)
        filemenu.add_command(label="Open", command=self.on_file_open)
        filemenu.add_command(label="Save", command=self.donothing)
        filemenu.add_command(label="Save as...", command=self.donothing)
        filemenu.add_command(label="Close", command=self.donothing)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        self.menubar.add_cascade(label="File", menu=filemenu)

    def on_page_select(self,evt):
        w = evt.widget
        if (w.curselection() != ()):
            index = int(w.curselection()[0])
            value = w.get(index)
            if self.page != (index + 1):
                self.page = index + 1
                self.update_page(self.page)

    def text_reload(self):
        self.update_page(self.page)
        print "Text Reload:"

    def text_save(self):
        page_text = self.text_text.get("1.0",tk.END)
        file = open(self.edit_page_path, 'w')
        file.write(page_text.encode('utf-8'))
        file.close()
        self.file_saved = True

    def change_callback(self,evt):
        self.file_saved = False

    def donothing(self):
       filewin = Toplevel(self)
       button = Button(filewin, text="Do nothing button")
       button.pack()

    def update_page(self,index):
        if self.dir_path != "":
            orig_file = "%s/text_pages/pg_%04d.txt.orig" % (self.dir_path, index)
            self.edit_page_path = ("%s/text_pages/pg_%04d.txt" % (self.dir_path, index))
            if os.path.isfile(orig_file) != True:
                shutil.copyfile(filename, orig_file)
            self.ocr_text.config(state=tk.NORMAL)
            self.ocr_text.delete('1.0',tk.END)
            self.text_text.delete('1.0', tk.END)
            file = open(self.edit_page_path, 'r')
            page_text = file.read()
            self.text_text.insert('1.0',page_text)
            ocr_file = open(orig_file, 'r')
            self.ocr_text.insert('1.0',ocr_file.read())
            self.ocr_text.config(state=tk.DISABLED)

            file.close()
            self.text_render_engine.update()

            tiff_file = "%s/tiff_pages/pg_%04d.tiff" % (self.dir_path, index)
            tiff_img = Image.open(tiff_file)
            self.tiff_im=ImageTk.PhotoImage(tiff_img,self.tiff_label)
            self.tiff_label.config(image = self.tiff_im)

            pdf_file = "%s/pdf_pages/pg_%04d.pdf" % (self.dir_path, index)
            pdf_fh=glob.glob(pdfImg.PyGs({}).make_img_from_pdf(pdf_file)[1])[0]
            pdf_img = Image.open(pdf_fh)
            tk_pdf_img=ImageTk.PhotoImage(pdf_img)
            self.pdf_canvas.itemconfig(self.pdf_image, image = tk_pdf_img)
            pdf_img.close()
            os.remove(pdf_fh)
            self.page = index

    def prev_page(self):
        if self.page > 1:
            page = self.page - 1
            self.page_list_box.see(page - 1)
            self.page_list_box.selection_clear(page)
            self.page_list_box.select_set(page - 1, last=None) #This only sets focus on the first item.
            self.update_page(page)

    def next_page(self):
        if self.page < self.max_page:
            page = self.page + 1
            self.page_list_box.see(page - 1)
            self.page_list_box.select_set(page - 1, last=None) #This only sets focus on the first item.
            self.page_list_box.selection_clear(page - 2)
            self.update_page(page)

    def load_dir(self):
        #Check for pdf_pages
        if os.path.isdir(self.dir_path+'/pdf_pages'):
            print "found PDF_Pages"
        else :
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
        for f in os.listdir(self.dir_path+'/tiff_pages'):
             if os.path.isfile(self.dir_path+'/tiff_pages/'+f):
                 self.page_list_box.insert(tk.END,i)
                 i = i + 1
        self.file_saved = True
        self.max_page = i - 1
        self.page = 1
        self.page_list_box.select_set(0) #This only sets focus on the first item.
        self.update_page(self.page)
        #self.page_prev_button.config(state="DISABLED")

    def on_file_new(self):
        print 'NewFile'

    def on_file_open(self):
        opts = {}
        opts['title'] = 'Open a new project'
        self.dir_path = tkFileDialog.askdirectory(**opts)
        if self.dir_path != "":
            self.load_dir()

if __name__ == '__main__':
    root = tk.Tk()
    root.title("ShowControl:ScriptEditor v0.0.1")
    ScriptEditor(root).pack(side="top", fill="both", expand=True)
    root.mainloop()
