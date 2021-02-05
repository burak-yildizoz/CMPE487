from copy import deepcopy
import socket

class User:
    def get_my_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    def __init__(self, alias):
        assert type(alias) is str
        self._ip = User.get_my_ip()
        self._alias =  alias
    def __eq__(self, other):
        return self.get_ip() == other.get_ip()
        # use the following for test purposes
        return self.fullname() == other.fullname()
    def get_ip(self):
        return deepcopy(self._ip)
    def get_alias(self):
        return deepcopy(self._alias)
    def fullname(self):
        return '%s (%s)' % (self._alias, self._ip)



class Answer:
    def __init__(self, author, text):
        assert type(author) is User
        assert type(text) is str
        self._text = text
        self._vote = 0
        self._author = author
        self._voters = [author]

    def upvote(self, voter):
        assert type(voter) is User
        if voter in self._voters:
            return False
        self._voters.append(voter)
        self._vote += 1
        return True

    def downvote(self, voter):
        assert type(voter) is User
        if voter in self._voters:
            return False
        self._voters.append(voter)
        self._vote -= 1
        return True

    def __eq__(self, other):
        return (self._vote == other.get_vote_status()
                and self._author == other.get_author()
                and self._text == other.get_text())

    def __lt__(self, other):
        return self._vote < other.get_vote_status()

    def get_vote_status(self):
        return deepcopy(self._vote)

    def get_author(self):
        return deepcopy(self._author)

    def get_text(self):
        return deepcopy(self._text)

    def print(self):
        print('Answer (%d votes): \n%s' % (
            self.get_vote_status(),
            self.get_text()))
        print('answered by %s\n' % self.get_author().fullname())



class Question(Answer):
    def __init__(self, author, title, text):
        assert type(author) is User
        assert type(title) is str
        assert type(text) is str
        super().__init__(author, text)
        self._title = title
        self._answers = []

    def answer(self, answer):
        assert type(answer) is Answer
        if answer in self._answers:
            return False
        self._answers.append(answer)
        return True

    def __eq__(self, other):
        return (self._vote == other.get_vote_status()
                and self._author == other.get_author()
                and self._title == other.get_title())

    def get_title(self):
        return deepcopy(self._title)

    def get_problem(self):
        title = self.get_title()
        text = self.get_text()
        return (title, text)

    def get_answers(self):
        return sorted(self._answers, reverse=True)

    def answers_size(self):
        return len(self._answers)

    def print(self, print_answers=True):
        print('Question (%d votes): %s\n%s' % (
            self.get_vote_status(),
            *self.get_problem()))
        print('asked by %s' % self.get_author().fullname())
        print('Answers: %d total\n' % self.answers_size())
        if print_answers:
            for i, answer in enumerate(self.get_answers(), start=1):
                print('[%d/%d]' % (i, self.answers_size()), end=' ')
                answer.print()



if __name__ == '__main__':
    print('Change User.__eq__ method first!')
    u1 = User('me')
    u2 = User('someone else')
    q1 = Question(u1, 'My Title',
                  ('My question text\n'
                   'It is multiline'))
    assert q1.upvote(u2)
    a1 = Answer(u1, 'This is my answer')
    assert q1.answer(a1)
    a2 = Answer(u2, ('This is another answer\n'
                     'This answer is multiline'))
    assert q1.answer(a2)
    assert a2.upvote(u1)
    q1.print()
