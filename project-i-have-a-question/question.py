from copy import deepcopy

class User:
    def __init__(self, ip_address, alias):
        assert type(ip_address) is str
        assert type(alias) is str
        self._ip = ip_address
        self._alias =  alias
    def get_ip(self):
        return deepcopy(self._ip)
    def get_alias(self):
        return deepcopy(self_alias)
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
        return self._vote == other.get_vote_status()

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
        self._answers.append(answer)

    def get_problem(self):
        title = deepcopy(self._title)
        text = deepcopy(self._text)
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
    u1 = User('127.0.0.1', 'me')
    u2 = User('192.168.1.1', 'someone else')
    q1 = Question(u1, 'My Title',
                  ('My question text\n'
                   'It is multiline'))
    assert q1.upvote(u2)
    a1 = Answer(u1, 'This is my answer')
    q1.answer(a1)
    a2 = Answer(u2, ('This is another answer\n'
                     'This answer is multiline'))
    q1.answer(a2)
    assert a2.upvote(u1)
    q1.print()
