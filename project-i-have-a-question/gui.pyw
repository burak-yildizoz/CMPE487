# https://realpython.com/python-gui-tkinter/
import tkinter as tk

# create a GUI
window = tk.Tk()

# title label
frm_title = tk.Frame(master=window)
lbl_title = tk.Label(master=frm_title,
                     text='I Have A Question',
                     fg='white', bg='blue')
lbl_title.pack(fill=tk.BOTH)

# question text box
frm_text_box = tk.Frame(master=window)
txt_question = tk.Text(master=frm_text_box)
txt_question.pack(fill=tk.BOTH, expand=True)

# submit button
frm_submit = tk.Frame(master=window)
fn_submit = lambda : (
    print('Your question:'),
    print(txt_question.get('1.0', tk.END))
    )
btn_submit = tk.Button(master=frm_submit,
                       text='Submit question',
                       command=fn_submit)
btn_submit.pack(fill=tk.BOTH)

# display the frames
frm_title.pack(side=tk.TOP, fill=tk.X)
frm_submit.pack(side=tk.BOTTOM, fill=tk.X)
frm_text_box.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# listen for events and run until window closes
window.mainloop()
