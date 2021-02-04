# https://realpython.com/python-gui-tkinter/
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter.simpledialog import askstring

from question import User, Answer, Question

class Application(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = self.get_username()
        self.questions = []
        # program title label
        self.frm_program = tk.Frame(master=self)
        self.lbl_program = tk.Label(master=self.frm_program,
                                    text=self.title(),
                                    fg='white', bg='blue')
        self.lbl_program.pack(fill=tk.BOTH)
        self.frm_program.pack(fill=tk.X)
        # stack pages on container
        container = tk.Frame(self)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        # only one frame will be visible at once
        self.frames = {}
        for F in (StartPage, AskPage):
            page_name = F.__name__
            frame = F(root=container, app=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky='NSEW')
        # default page
        self.show_frame('StartPage')

    def get_username(self):
        self.withdraw()
        alias = askstring(self.title(), 'Your name:')
        user = User(alias)
        self.deiconify()
        return user

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()


class StartPage(tk.Frame):
    def __init__(self, root, app):
        super().__init__(master=root)
        assert type(app) is Application
        self.app = app
        label = tk.Label(self, text='Welcome %s' % self.app.user.get_alias())
        label.pack(side=tk.TOP, fill=tk.X, pady=10)
        button1 = tk.Button(self, text='Ask A Question',
                            command=lambda: app.show_frame('AskPage'))
        button1.pack()


class AskPage(tk.Frame):
    def __init__(self, root, app):
        super().__init__(master=root)
        assert type(app) is Application
        self.app = app
        # question title label
        self.frm_title_lbl = tk.Frame(master=self)
        self.lbl_title = tk.Label(master=self.frm_title_lbl,
                                  text='Your question:')
        self.lbl_title.pack()
        # question title entry
        self.frm_title_ent = tk.Frame(master=self)
        self.ent_title = tk.Entry(master=self.frm_title_ent)
        self.ent_title.pack(fill=tk.BOTH)
        # question text box
        self.frm_question = tk.Frame(master=self)
        self.stxt_question = ScrolledText(master=self.frm_question)
        self.stxt_question.pack(fill=tk.BOTH, expand=True)
        # submit button
        self.frm_submit = tk.Frame(master=self)
        self.btn_submit = tk.Button(master=self.frm_submit,
                                    text='Submit question',
                                    command=self.fn_submit)
        self.btn_submit.pack(fill=tk.BOTH)
        # return button
        self.frm_return = tk.Frame(master=self)
        self.btn_return = tk.Button(master=self.frm_return,
                                    text='Return to main page',
                                    command=self.fn_return)
        self.btn_return.pack(fill=tk.BOTH)
        # display the frames
        cols = 50
        self.frm_title_lbl.grid(row=0, column=0, stick='NSW')
        self.frm_title_ent.grid(row=0, column=1, columnspan=cols-1, sticky='NSEW')
        self.frm_question.grid(row=1, columnspan=cols, sticky='NSEW')
        self.frm_submit.grid(row=2, columnspan=cols, sticky='NSEW')
        self.frm_return.grid(row=3, columnspan=cols, sticky='NSEW')
        tk.Grid.rowconfigure(self, 1, weight=1)
        for i in range(cols):
            tk.Grid.columnconfigure(self, i, weight=1)

    def fn_submit(self):
        title = self.ent_title.get()
        self.ent_title.delete(0, tk.END)
        text = self.stxt_question.get('1.0', tk.END)
        self.stxt_question.delete('1.0', tk.END)
        question = Question(self.app.user, title, text)
        self.app.questions.append(question)
        question.print()
        self.fn_return()

    def fn_return(self):
        self.app.show_frame('StartPage')


if __name__ == '__main__':
    app = Application(className='I Have A Question')
    app.mainloop()
