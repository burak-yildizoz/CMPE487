# https://realpython.com/python-gui-tkinter/
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter.simpledialog import askstring
from tkinter import ttk
from copy import deepcopy
import time
import atexit

from question import User, Answer, Question
from CommAPI import CommunicationModule

class Notification:
    def error_levels():
        return ['debug', 'info', 'warn', 'success',
                'personal', 'error', 'request']

    def error_colors():
        return ['light blue', 'white', 'orange', 'green',
                'gold', 'red', 'purple']

    verbosity_level = 1    # info
    important_level = 4    # personal

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



# https://blog.tecladocode.com/tkinter-scrollable-frames/
class ScrollableFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind('<Configure>', lambda e: canvas.configure(
            scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)



class TextFrame(tk.Frame):
    def __init__(self, master, answer, user):
        assert type(user) is User
        super().__init__(master)
        self.answer = answer
        self.user = user
        # text and author labels
        self.lbl_text = tk.Label(master=self, text=answer.get_text())
        self.lbl_user = tk.Label(master=self, text=answer.author.get_alias())
        # voting scheme
        user_reaction = answer.get_user_reaction(self.user)
        self.w = 30
        self.pady = 5
        # upvote
        self.cnv_up = tk.Canvas(master=self, height=self.w/2, width=self.w)
        up_fill = 'orange' if user_reaction == 1 else 'gray'
        self.cnv_up.create_polygon(0, 0, self.w, 0, self.w/2, self.w/2,
                                   fill=up_fill)
        self.cnv_up.bind('<Button-1>', self.fn_upvote)
        # vote count
        self.lbl_count = tk.Label(master=self, text=answer.get_vote_status())
        raise 'to be implemented'

    def fn_upvote(self, event):
        x, y = event.x, event.y

        if x < 0 or x > self.w or y < 0 or y > self.w:
            return False

        if x < (self.w / 2):
            return y > (2*x+self.w)
        else:
            return y > 2*(x-self.w/2)

        return False

    def fn_downvote(self, event):
        x, y = event.x, (self.w - event.y)

        if x < 0 or x > self.w or y < 0 or y > self.w:
            return False

        if x < (self.w / 2):
            return y > (2*x+self.w)
        else:
            return y > 2*(x-self.w/2)

        return False


class Application(tk.Tk):
    def __init__(self, root=None):
        super().__init__(root)
        if root is None:
            self.title('I Have A Question')

        test = True
        alias = 'me'
        passwd = 'mod'
        if not test:
            alias = self.get_input('Your name:')
            passwd = self.get_input('Password (for teachers):')
        self.user = User(alias=alias)
        is_mod = passwd == 'mod'

        lbl_wait = tk.Label(self, text='Waiting for the room ...')
        lbl_wait.pack()
        self.refresh()
        self.comm_module = CommunicationModule(self.user.get_alias(),
                                               is_mod, 12345)
        self.refresh()
        self.protocol('WM_DELETE_WINDOW', self.cleanup)
        self.comm_module.init()
        if not is_mod:
            lbl_wait.config(text='Waiting for host ...')
            while self.comm_module.is_requesting:
                self.comm_module.init_database_after_login()
                time.sleep(2)
        lbl_wait.destroy()

        self.current_page = 'HomePage'
        self.comm_module.set_application(self)
        self._questions = self.comm_module.database.questions
        if test:
            q = Question(self.user, 'Test Question', 'text')
            self._questions[q.get_title()] = q
        assert (type(self._questions) is dict
                and all(type(self._questions[title]) is Question
                        for title in self._questions))

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
                                  command=lambda: self.show_frame('HomePage'))
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
        self.show_frame(self.current_page)
        self.new_notification(Notification(
            'Notifications will appear here', 'info'))
        self.mainloop()

    def refresh(self):
        self.update_idletasks()
        self.update()

    def cleanup(self):
        print('Cleanup in progress ...')
        self.comm_module.kill()
        self.destroy()
        print('Cleanup done!')

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

    def get_input(self, prompt):
        self.withdraw()
        reply = askstring(self.title(), prompt)
        self.deiconify()
        return reply

    def show_frame(self, page_name):
        self.current_page = page_name
        frame = self.frames[page_name]
        frame.tkraise()
        frame.update()

    def add_question(self, question):
        title, content = question.get_problem()
        if title in self._questions:
            raise Exception('The same question exists')
        self.comm_module.add_question(title, content)

    def get_questions(self):
        questions = sorted(list(self._questions.values()), reverse=True)
        return questions

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
            command=lambda: self.app.show_frame('AskPage'))
        self.btn_answer = tk.Button(
            self, text='Answer Questions',
            command=lambda: self.app.show_frame('AnswerPage'))
        self.btn_notify = tk.Button(
            self, command=lambda: app.show_frame('NotificationsPage'))
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
        text = self.stxt_question.get('1.0', tk.END)
        try:
            question = Question(self.app.user, title, text)
        except Exception as e:
            self.app.new_notification(Notification(str(e), 'warn'))
            return
        try:
            self.app.add_question(question)
        except Exception as e:
            self.app.new_notification(Notification(
                '%s: %s'%(e, title), 'error'))
            return
        self.app.new_notification(Notification(
                'You asked a new question: %s'%title, 'success'))
        self.ent_title.delete(0, tk.END)
        self.stxt_question.delete('1.0', tk.END)
        self.app.show_frame('HomePage')



class AnswerPage(CustomPage):
    def __init__(self, root, app):
        super().__init__(root, app)
        # scrollbar at the left to select questions
        self.scrb = tk.Scrollbar(master=self)
        self.qlist = tk.Listbox(master=self, width=48,
                                yscrollcommand=self.scrb.set)
        self.scrb.config(command=self.qlist.yview)
        self.qlist.bind('<<ListboxSelect>>', self.fn_select)
        self.qlist.pack(side=tk.LEFT, fill=tk.BOTH)
        self.scrb.pack(side=tk.LEFT, fill=tk.Y)
        self.selected_question = None

    def update(self):
        self.questions = self.app.get_questions()
        self.titles = [q.get_title() for q in self.questions]
        self.qlist.delete(0, tk.END)
        for title in self.titles:
            self.qlist.insert(tk.END, title)
        self.show()

    def fn_select(self, event):
        sel = self.qlist.curselection()
        # in case () is returned, bug of ListboxSelect callback
        if not sel:
            return
        idx = sel[0]
        self.selected_question = self.questions[idx]
        self.show()

    def show(self):
        # another page at the right to inspect the selected question
        self.frame = tk.Frame(master=self)
        self.frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        if self.selected_question is None:
            return
        try:
            idx = self.questions.index(self.selected_question)
        except ValueError:
            self.app.new_notification(Notification(
                'Could not find previously selected question: %s'%(
                    self.selected_question.get_title()), 'error'))
            return
        self.lbl_title = tk.Label(master=self.frame,
                                  text=self.selected_question.get_title())
        self.lbl_title.pack()
        self.sfrm = ScrollableFrame(master=self.frame)
        self.sfrm.pack()
        self.tfrm_question = TextFrame(master=self.sfrm,
                                       answer=self.selected_question,
                                       user=self.app.user)
        self.tfrm_question.pack()
        self.lbl_answer = tk.Label(master=self.sfrm, text='Answers (%d)'%(
            self.selected_question.answers_size()))
        self.lbl_answer.pack()
        for answer in self.selected_question.get_answers():
            TextFrame(master=self.sfrm, answer=answer).pack()



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
        self.colors = [n.color() for n in self.app.notifications]
        self.unreads = [n.unread() for n in self.app.notifications]
        self.nlist.delete(0, tk.END)
        for i, notification in enumerate(self.app.notifications):
            self.nlist.insert(i, notification.msg)
            self.nlist.itemconfig(i, bg=self.colors[i])
            if self.unreads[i]:
                self.nlist.itemconfig(i, fg='blue')

    def fn_select(self, event):
        sel = self.nlist.curselection()
        # in case () is returned, bug of ListboxSelect callback
        if not sel:
            return
        idx = sel[0]
        if self.unreads[idx]:
            self.app.notifications[idx].read = True
            self.update()



if __name__ == '__main__':
    app = Application()
