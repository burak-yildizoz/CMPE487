# https://realpython.com/python-gui-tkinter/
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter.simpledialog import askstring

from question import User, Answer, Question

# initialization
programName = 'I Have A Question'
questions = []
window = tk.Tk(className=programName)

# create the user
window.withdraw()
alias = askstring(programName, 'Your name:')
user = User(alias)
window.deiconify()

# program title label
frm_program = tk.Frame(master=window)
lbl_program = tk.Label(master=frm_program,
                       text=programName,
                       fg='white', bg='blue')
lbl_program.pack(fill=tk.BOTH)

# question title label
frm_title_lbl = tk.Frame(master=window)
lbl_title = tk.Label(master=frm_title_lbl,
                     text='Your question:')
lbl_title.pack()

# question title entry
frm_title_ent = tk.Frame(master=window)
ent_title = tk.Entry(master=frm_title_ent)
ent_title.pack(fill=tk.BOTH)

# question text box
frm_question = tk.Frame(master=window)
stxt_question = ScrolledText(master=frm_question)
stxt_question.pack(fill=tk.BOTH, expand=True)

# submit button
frm_submit = tk.Frame(master=window)
def fn_submit():
    title = ent_title.get()
    ent_title.delete(0, tk.END)
    text = stxt_question.get('1.0', tk.END)
    stxt_question.delete('1.0', tk.END)
    question = Question(user, title, text)
    questions.append(question)
    question.print()
btn_submit = tk.Button(master=frm_submit,
                       text='Submit question',
                       command=fn_submit)
btn_submit.pack(fill=tk.BOTH)

# display the frames
numcolumns = 50
frm_program.grid(row=0, columnspan=numcolumns, sticky='NSEW')
frm_title_lbl.grid(row=1, column=0, stick='NSW')
frm_title_ent.grid(row=1, column=1, columnspan=numcolumns-1, sticky='NSEW')
frm_question.grid(row=2, columnspan=numcolumns, sticky='NSEW')
frm_submit.grid(row=3, columnspan=numcolumns, sticky='NSEW')
tk.Grid.rowconfigure(window, 2, weight=1)
for i in range(numcolumns):
    tk.Grid.columnconfigure(window, i, weight=1)

# listen for events and run until window closes
window.mainloop()
