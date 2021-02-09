# I Have A Question

**Authors:**
* Alperen Bağ [@alprnbg](https://github.com/alprnbg)
* Burak Yıldızöz [@burak-yildizoz](https://github.com/burak-yildizoz)

## Description

### Networking Algorithm

There are two type of users: a teacher and the students. The students wait for the teacher (host) to start the application.

Whenever a new user joins, that user informs others by broadcast over UDP, and the other users respond. The new user fetches the previous data from a randomly selected user over TCP.

In each change, (question, vote, answer), the author broadcasts this information.

- Information sent for a new question:
  - Author
  - Title
  - Question text
- Information sent for an answer to a question:
  - Author
  - Title of the question
  - Answer text
- Information sent for a vote:
  - Voter
  - Title of the question
  - Upvote or downvote
  - Answer text if answer is voted

**Notes:**
- The author or voter information is already available with *every* message.
- Each question should have a different title, which means there cannot be two question with the same title, with or without different question texts.

### User Interface

We used **Tkinter** module of Python for graphical user interface. Because, it is already installed with default Python, and it is cross-platform.

Overview:
- Submit your name over entry. Skip password empty you are not the host.
- You can access to other pages from home page.
  - Ask A Question
  - Answer Questions
  - Read Notifications
- Both the title and the text of  a question cannot be empty. *Tip:* You can return to home page and come back with your draft saved.
- Answer Questions button appears on home page whenever there first question is asked. Scroll the questions on the left. Click one to see its content and given answers. You can also scroll those answers if there are many of them. The sorting algorithm as follows:
  - The newest question appears at the top for the same voting score.
  - A question with a higher score appears at the top.
  - If a question has an answer whose score is positive, that question is considered to have an accepted answer. Accepted questions are listed below unanswered questions.
  - Similar rules apply for answers.
- If there is an update in the current state, the user is notified in the application at the bottom line. Depending on the importance of the change, that specific notification also appears in the Notification page as unread, or does not show up at the bottom line if it its type is debug.


## Deployment

### How To Run
1. Run ` $ python gui.pyw`. On Windows, just run the pyw file and it will open without a console.
2. Enter your name.
3. Enter the moderator password if you are the moderator. (Password is 'mod'.)
4. If you are a student, you can skip step 3 and just press enter. (If the room is not created yet, you will wait until the moderator create the room.)

### Manual
1. You can ask questions via "Ask A Question" button.
2. If there is a question in the room, you will see them under the "Answer Questions" button.
3. You can answer any question and vote other's question under the "Answer Questions" button.
4. You can see the latest notification at the bottom in any page, or you can go to notifications page for a full list.

### Tests
1. We tested our application with Ubuntu 18.04 and Rapsberry Pi.
