from copy import deepcopy
import socket

from utils import get_my_ip

class User:
    def __init__(self, alias, ip_address=None):
        assert type(alias) is str
        if not alias or alias.isspace():
            alias = "N/A"
        self._ip = get_my_ip() if ip_address is None else ip_address
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
        return '%s (%s)'%(self._alias, self._ip)



class BaseText:
    def __init__(self, author, text):
        assert type(author) is User
        assert type(text) is str
        if not text or text.isspace():
            text = "N/A"
        self._text = text
        self.author = author
        self._upvoters = []
        self._downvoters = []

    def eligible_vote(self, voter):
        assert type(voter) is User
        if voter == self.author:
            print('You cannot vote your own %s'%type(self).__name__)
            return False
        if voter in self._upvoters:
            print('%s already upvoted this %s'%(
                voter.fullname(), type(self).__name__))
            return False
        if voter in self._downvoters:
            print('%s already downvoted this %s'%(
                voter.fullname(), type(self).__name__))
            return False
        return True

    def upvote(self, voter):
        if self.eligible_vote(voter):
            self._upvoters.append(voter)

    def downvote(self, voter):
        if self.eligible_vote(voter):
            self._downvoters.append(voter)

    def get_vote_status(self):
        return len(self._upvoters) - len(self._downvoters)

    def get_user_reaction(self, user):
        assert type(user) is User
        if user in self._upvoters:
            return 1
        if user in self._downvoters:
            return -1
        return 0

    def get_title(self):
        return deepcopy(self._title)

    def get_text(self):
        return deepcopy(self._text)



class Answer(BaseText):
    def __init__(self, author, text):
        super().__init__(author, text)

    def __eq__(self, other):
        return (self._title == other.get_title()
                and self._text == other.get_text())

    def __lt__(self, other):
        return self.get_vote_status() < other.get_vote_status()

    def print(self):
        print('Answer (%d votes): \n%s'%(
            self.get_vote_status(),
            self.get_text()))
        print('answered by %s\n'%self.author.fullname())



class Question(BaseText):
    def __init__(self, author, title, text):
        assert type(title) is str
        if not title or title.isspace():
            title = "N/A"
        super().__init__(author, text)
        self._title = title
        self._answers = []

    def answer(self, answer):
        assert type(answer) is Answer
        answer._title = self._title
        if answer in self._answers:
            print('The same answer exists')
        else:
            self._answers.append(answer)

    def has_accepted_answer(self):
        for answer in self._answers:
            if answer.get_vote_status() > 0:
                return True
        return False

    def __eq__(self, other):
        return self._title == other.get_title()

    def __lt__(self, other):
        self_answered = self.has_accepted_answer()
        other_answered = other.has_accepted_answer()
        if self_answered == other_answered:
            return self.get_vote_status() < other.get_vote_status()
        else:
            return self_answered

    def get_problem(self):
        title = self.get_title()
        text = self.get_text()
        return (title, text)

    def get_answers(self):
        return sorted(self._answers, reverse=True)

    def answers_size(self):
        return len(self._answers)

    def print(self, print_answers=True):
        print('Question (%d votes): %s\n%s'%(
            self.get_vote_status(),
            *self.get_problem()))
        print('asked by %s'%self.author.fullname())
        print('Answers: %d total\n'%self.answers_size())
        if print_answers:
            for i, answer in enumerate(self.get_answers(), start=1):
                print('[%d/%d]'%(i, self.answers_size()), end=' ')
                answer.print()



if __name__ == '__main__':
    print('Change User.__eq__ method first!')
    u1 = User('me')
    u2 = User('someone else')
    q1 = Question(u1, 'My Title',
                  ('My question text\n'
                   'It is multiline'))
    q1.upvote(u2)
    a1 = Answer(u1, 'This is my answer')
    q1.answer(a1)
    a2 = Answer(u2, ('This is another answer\n'
                     'This answer is multiline'))
    q1.answer(a2)
    a2.upvote(u1)
    q1.print()
    a2.get_title()  # 'My Title'
    q1.answer(Answer(u2, 'This is my answer'))  # this line should throw
