#!/usr/bin/env python
__author__ = 'bapril'

import Tkinter
import ttk
import tkFileDialog
import tkMessageBox
import os
import shutil
from PIL import Image
from PIL import ImageTk
import pypdfocr.pypdfocr_gs as pdfImg
import glob

# Setup some globals
file_saved = True # Changes to false when a file has been changed but not saved.
page = 0 # Indicates the current page.
max_page = 0
project = None # Name of the current project.
dir_path = ""
page_list_box = None
text_entry = None
ocr_entry = None
tiff_canvas = None
tiff_image = None
pdf_canvas = None
pdf_image = None
page_next_button = None
page_prev_button = None

def change_callback(evt):
    global file_saved
    print "Change detected"
    file_saved = False

def donothing():
   filewin = Toplevel(root)
   button = Button(filewin, text="Do nothing button")
   button.pack()

def update_page(index):
    global dir_path
    global text_entry
    global ocr_entry
    global tiff_canvas
    if dir_path != "":
        orig_file = "%s/text_pages/pg_%04d.txt.orig" % (dir_path, index)
        filename = ("%s/text_pages/pg_%04d.txt" % (dir_path, index))
        if os.path.isfile(orig_file) != True:
            shutil.copyfile(filename, orig_file)
        ocr_text.config(state=Tkinter.NORMAL)
        ocr_text.delete('1.0',Tkinter.END)
        text_text.delete('1.0', Tkinter.END)
        file = open(filename, 'r')
        text_text.insert('1.0',file.read())
        ocr_file = open(orig_file, 'r')
        ocr_text.insert('1.0',ocr_file.read())
        ocr_text.config(state=Tkinter.DISABLED)

        tiff_file = "%s/tiff_pages/pg_%04d.tiff" % (dir_path, index)
        print "Loading TIFF: "+tiff_file
        tiff_img = Image.open(tiff_file)
        tiff_im=ImageTk.PhotoImage(tiff_img)
        tiff_canvas.config(image = tiff_im)

        pdf_file = "%s/pdf_pages/pg_%04d.pdf" % (dir_path, index)
        print "Loading PDF: "+pdf_file
        pdf_fh=glob.glob(pdfImg.PyGs({}).make_img_from_pdf(pdf_file)[1])[0]
        print "PDF_FH "+pdf_fh
        pdf_img = Image.open(pdf_fh)
        tk_pdf_img=ImageTk.PhotoImage(pdf_img)
        pdf_canvas.itemconfig(pdf_image, image = tk_pdf_img)
        pdf_img.close()
        os.remove(pdf_fh)

def prev_page():
    global page
    global page_list_box
    print "Prev: %d" % (page)
    if page > 1:
        page = page - 1
        print "Prev: %d" % (page)
        page_list_box.see(page - 1)
        page_list_box.selection_clear(page)
        page_list_box.select_set(page - 1, last=None) #This only sets focus on the first item.
        update_page(page)

def next_page():
    global page
    global max_page
    global page_list_box
    print "Next: %d" % (page)
    if page < max_page:
        page = page + 1
        print "Next: %d" % (page)
        page_list_box.see(page - 1)
        page_list_box.select_set(page - 1, last=None) #This only sets focus on the first item.
        page_list_box.selection_clear(page - 2)
        update_page(page)

def on_page_select(evt):
    global page
    w = evt.widget
    if (w.curselection() != ()):
        index = int(w.curselection()[0])
        value = w.get(index)
        if page != (index + 1):
            page = index + 1
            update_page(page)
        else:
            print "Don't update we are on the same page. "

def load_dir():
    global dir_path
    global file_saved
    global max_page
    global page
    #Check for pdf_pages
    if os.path.isdir(dir_path+'/pdf_pages'):
        print "found PDF_Pages"
    else :
        tkMessageBox.showinfo("Error loading project", dir_path+'/pdf_pages not found!')
        dir_path = ""
        return
    #check for tiff_pages
    if os.path.isdir(dir_path+'/tiff_pages'):
        print "found tiff_Pages"
    else:
        tkMessageBox.showinfo("Error loading project", dir_path+'/tiff_pages not found!')
        dir_path = ""
        return
    #check for text_pages
    if os.path.isdir(dir_path+'/text_pages'):
        print "found text_Pages"
    else:
        tkMessageBox.showinfo("Error loading project", dir_path+'/text_pages not found!')
        dir_path = ""
        return
    #walk tiff_pages and generate page_list.
    i = 1
    for f in os.listdir(dir_path+'/tiff_pages'):
         if os.path.isfile(dir_path+'/tiff_pages/'+f):
             page_list_box.insert(Tkinter.END,i)
             i = i + 1
    file_saved = True
    max_page = i - 1
    page = 1
    page_list_box.select_set(0) #This only sets focus on the first item.
    update_page(page)

def on_file_new():
    print 'NewFile'

def on_file_open():
    global dir_path
    opts = {}
    opts['title'] = 'Open a new project'
    dir_path = tkFileDialog.askdirectory(**opts)
    if dir_path != "":
        print 'LoadDir '+dir_path
        load_dir()

if __name__ == '__main__':
    root = Tkinter.Tk()
    menubar = Tkinter.Menu(root)
    root.title("ShowControl:ScriptEditor v0.0.1")
    filemenu = Tkinter.Menu(menubar, tearoff=0)
    filemenu.add_command(label="New", command=on_file_new)
    filemenu.add_command(label="Open", command=on_file_open)
    filemenu.add_command(label="Save", command=donothing)
    filemenu.add_command(label="Save as...", command=donothing)
    filemenu.add_command(label="Close", command=donothing)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)

    content = ttk.Frame(root)
    Tkinter.Grid.rowconfigure(content, 0, weight=4)
    Tkinter.Grid.rowconfigure(content, 1, weight=1)
    Tkinter.Grid.columnconfigure(content, 0, weight=1)
    Tkinter.Grid.columnconfigure(content, 1, weight=4)
    Tkinter.Grid.columnconfigure(content, 2, weight=4)

    page_list_frame = Tkinter.LabelFrame(content, text="Pages")
    input_notebook = ttk.Notebook(content)
    render_frame = Tkinter.LabelFrame(content, text="Rendered Script")
    page_control_frame = Tkinter.Frame(content)
    input_control_frame = Tkinter.Frame(content)
    render_control_frame = Tkinter.Frame(content)

    #List of pages
    page_list_scrollbar = Tkinter.Scrollbar(page_list_frame, orient=Tkinter.VERTICAL)
    page_list_box = Tkinter.Listbox(
        page_list_frame,
        yscrollcommand=page_list_scrollbar.set,
        selectmode=Tkinter.SINGLE)
    page_list_box.bind('<<ListboxSelect>>', on_page_select)
    page_list_scrollbar.config(command=page_list_box.yview)
    page_list_scrollbar.pack(side=Tkinter.RIGHT, fill=Tkinter.Y)
    page_list_box.pack(side=Tkinter.LEFT, fill="both", expand="yes")

    #Tabs of Input
    pdf_tab = Tkinter.Frame(input_notebook)   # first page, which would get widgets gridded into it
    tiff_tab = Tkinter.Frame(input_notebook)   # second page
    ocr_tab = Tkinter.Frame(input_notebook)
    text_tab = Tkinter.Frame(input_notebook)
    input_notebook.add(pdf_tab, text='PDF')
    input_notebook.add(tiff_tab, text='TIFF')
    input_notebook.add(ocr_tab, text='OCR')
    input_notebook.add(text_tab, text='TXT')

    #PDF Input Tab
    pdf_canvas = Tkinter.Canvas( pdf_tab, height=250, width=300 )
    pdf_image = pdf_canvas.create_image(0, 0)
    pdf_canvas.pack(fill="both", expand="yes")
    #TIFF Input Tab
    #tiff_canvas = Tkinter.Canvas(tiff_tab, height=250, width=300)
    tiff_canvas = Tkinter.Label(tiff_tab, height=250, width=300)
    tiff_canvas.pack(fill="both", expand="yes")

    #OCR Input Tab
    ocr_text = Tkinter.Text (ocr_tab)
    ocr_text.config(state=Tkinter.DISABLED)
    ocr_text.pack(fill="both", expand="yes")

    #TXT Input Tab
    text_text = Tkinter.Text (text_tab)
    text_text.pack(fill="both", expand="yes")
    text_text.bind('<<Modified>>', change_callback)

    #Rendered View
    rendered_canvas = Tkinter.Canvas ( render_frame, bg="green", height=250, width=300 )
    rendered_canvas.pack(fill="both", expand="yes")

    page_next_button = Tkinter.Button(page_control_frame, text="Next Page", command=next_page).grid(row=0, column = 1)
    page_prev_button = Tkinter.Button(page_control_frame, text="Prev. Page", command=prev_page).grid(row=0, column = 0)

    sticky_all=("N","S","E","W")
    page_list_frame.grid(sticky=sticky_all, row=0, column=0)
    input_notebook.grid(sticky=sticky_all, row=0, column=1)
    render_frame.grid(sticky=sticky_all, row=0, column=2)
    page_control_frame.grid(sticky=sticky_all, row=1, column=0)
    input_control_frame.grid(sticky=sticky_all, row=1, column=1)
    render_control_frame.grid(sticky=sticky_all, row=1, column=2)

    content.pack(fill="both", expand="yes")

    root.config(menu=menubar)
    root.mainloop()
