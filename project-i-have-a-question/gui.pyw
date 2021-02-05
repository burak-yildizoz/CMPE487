# https://realpython.com/python-gui-tkinter/
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter.simpledialog import askstring
from copy import deepcopy
from question import User, Answer, Question

class Notification:
    def error_levels():
        return ['debug', 'info', 'warn', 'success', 'error', 'request']

    def error_colors():
        return ['light blue', 'white', 'orange', 'green', 'red', 'purple']

    verbosity_level = 1    # info
    important_level = 4    # error

    def __init__(self, msg, level):
        levels = Notification.error_levels()
        assert level in levels
        assert type(msg) is str
        assert msg and not msg.isspace()
        self.msg = msg
        self._level = levels.index(level)
        self.read = False

    def verbose(self):
        return self._level >= Notification.verbosity_level

    def important(self):
        return self._level >= Notification.important_level

    def unread(self):
        return not self.read and self.important()

    def color(self):
        return Notification.error_colors()[self._level]



class Application(tk.Tk):
    def __init__(self, root=None, user=None, questions=[]):
        assert (type(questions) is list
                and all(type(q) is Question for q in questions))
        super().__init__(root)
        if root is None:
            self.title('I Have A Question')
        if user is None:
            user = self.get_username()
        assert type(user) is User
        self.user = user
        self._questions = deepcopy(questions)
        # program title label
        self.frm_program = tk.Frame(master=self)
        self.lbl_program = tk.Label(master=self.frm_program,
                                    text=self.title(),
                                    fg='white', bg='blue')
        self.lbl_program.pack(fill=tk.BOTH)
        self.frm_program.pack(fill=tk.X)
        # notifications label
        self.notifications = []
        self.frm_notify = tk.Frame(master=self)
        self.lbl_notify = tk.Label(master=self.frm_notify, fg='gray')
        self.lbl_notify.pack(fill=tk.BOTH)
        self.frm_notify.pack(side=tk.BOTTOM, fill=tk.X)
        # home button
        self.frm_home = tk.Frame(master=self)
        self.btn_home = tk.Button(master=self.frm_home,
                                  text='Return to home page',
                                  command=lambda:self.show_frame('HomePage'))
        self.btn_home.pack(fill=tk.BOTH)
        self.frm_home.pack(side=tk.BOTTOM, fill=tk.X)
        # stack pages on container
        container = tk.Frame(self)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        # only one frame will be visible at once
        self.frames = {}
        for F in (HomePage, AskPage, AnswerPage, NotificationsPage):
            page_name = F.__name__
            frame = F(root=container, app=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky='NSEW')
        # default page
        self.show_frame('HomePage')
        self.new_notification(Notification(
            'Notifications will appear here', 'info'))

    def update_notification(self):
        for i in range(len(self.notifications)):
            if self.notifications[i].verbose():
                self.lbl_notify.config(text=self.notifications[i].msg,
                                       bg=self.notifications[i].color())
                break

    def new_notification(self, notification):
        assert type(notification) is Notification
        self.notifications.insert(0, notification)
        self.update_notification()
        self.show_frame(self.current_page)

    def unreads_size(self):
        return sum([n.unread() for n in self.notifications])

    def get_username(self):
        self.withdraw()
        alias = askstring(self.title(), 'Your name:')
        user = User(alias)
        self.deiconify()
        return user

    def show_frame(self, page_name):
        self.current_page = page_name
        frame = self.frames[page_name]
        frame.update()
        frame.tkraise()

    def add_question(self, question):
        if question in self._questions:
            raise Exception('The same question exists')
        self._questions.insert(0, question)

    def get_questions(self):
        return sorted(self._questions, reverse=True)

    def questions_size(self):
        return len(self._questions)



class CustomPage(tk.Frame):
    def __init__(self, root, app):
        super().__init__(master=root)
        assert type(app) is Application
        self.app = app

    def update(self):
        pass



class HomePage(CustomPage):
    def __init__(self, root, app):
        super().__init__(root, app)
        self.lbl_welcome = tk.Label(self, text='Welcome %s'%(
            self.app.user.get_alias()))
        self.btn_ask = tk.Button(
            self, text='Ask A Question',
            command=lambda:self.app.show_frame('AskPage'))
        self.btn_answer = tk.Button(
            self, text='Answer Questions',
            command=lambda:self.app.show_frame('AnswerPage'))
        self.btn_notify = tk.Button(
            self, command=lambda:app.show_frame('NotificationsPage'))
        self.lbl_welcome.grid(row=0, sticky='EW', pady=10)
        self.btn_ask.grid(row=1)
        self.btn_notify.grid(row=3)
        tk.Grid.columnconfigure(self, 0, weight=1)

    def update(self):
        self.btn_notify.config(
            text='Read Notifications (%d unread)'%self.app.unreads_size())
        if self.app.questions_size():
            self.btn_answer.grid(row=2)



class AskPage(CustomPage):
    def __init__(self, root, app):
        super().__init__(root, app)
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
        # display the frames
        cols = 50
        self.frm_title_lbl.grid(row=0, column=0, stick='NSW')
        self.frm_title_ent.grid(row=0, column=1,
                                columnspan=cols-1, sticky='NSEW')
        self.frm_question.grid(row=1, columnspan=cols, sticky='NSEW')
        self.frm_submit.grid(row=2, columnspan=cols, sticky='NSEW')
        tk.Grid.rowconfigure(self, 1, weight=1)
        for i in range(cols):
            tk.Grid.columnconfigure(self, i, weight=1)

    def fn_submit(self):
        title = self.ent_title.get()
        self.ent_title.delete(0, tk.END)
        text = self.stxt_question.get('1.0', tk.END)
        self.stxt_question.delete('1.0', tk.END)
        question = Question(self.app.user, title, text)
        if self.app.add_question(question):
            question.print()
        self.app.show_frame('HomePage')



class AnswerPage(CustomPage):
    def __init__(self, root, app):
        super().__init__(root, app)
        # scrollbar at the left to select questions
        self.scrb = tk.Scrollbar(master=self)
        self.qlist = tk.Listbox(master=self, width=48,
                                yscrollcommand=self.scrb.set)
        self.scrb.config(command=self.qlist.yview)
        # another page at the right to inspect the selected question
        self.frame = tk.Frame(master=self)
        self.qlist.bind('<<ListboxSelect>>', self.fn_select)
        # layout of the page
        self.qlist.pack(side=tk.LEFT, fill=tk.BOTH)
        self.scrb.pack(side=tk.LEFT, fill=tk.Y)
        self.frame.pack(side=tk.RIGHT, fill=tk.BOTH)

    def update(self):
        self.questions = self.app.get_questions()
        self.titles = [q.get_title() for q in self.questions]
        self.qlist.delete(0, tk.END)
        for title in self.titles:
            self.qlist.insert(tk.END, title)

    def fn_select(self, event):
        idx = self.qlist.curselection()[0]
        question = self.questions[idx]
        question.print()



class NotificationsPage(CustomPage):
    def __init__(self, root, app):
        super().__init__(root, app)
        # scrollbar to read notifications
        self.scrb = tk.Scrollbar(master=self)
        self.nlist = tk.Listbox(master=self, fg='gray',
                                yscrollcommand=self.scrb.set)
        self.scrb.config(command=self.nlist.yview)
        self.nlist.bind('<<ListboxSelect>>', self.fn_select)
        self.scrb.pack(side=tk.RIGHT, fill=tk.Y)
        self.nlist.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.update()

    def update(self):
        self.colors = []
        self.unreads = []
        self.nlist.delete(0, tk.END)
        for i, notification in enumerate(self.app.notifications):
            self.colors.append(notification.color())
            self.unreads.append(notification.unread())
            self.nlist.insert(i, notification.msg)
            self.nlist.itemconfig(i, bg=self.colors[i])
            if self.unreads[i]:
                self.nlist.itemconfig(i, fg='blue')

    def fn_select(self, event):
        idx = self.nlist.curselection()[0]
        if self.unreads[idx]:
            self.app.notifications[idx].read = True
            self.update()



if __name__ == '__main__':
    user = User('me')
    questions = [Question(user, 'Title %d'%i, 'text %d'%i)
                 for i in range(100, 0, -1)]
    app = Application(user=user, questions=questions)
    app.mainloop()
