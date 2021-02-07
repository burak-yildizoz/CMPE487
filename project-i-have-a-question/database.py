from question import *

class Database(object):

    def __init__(self):
        self.questions = {} # type: Dict{str -> Question}

    def update_database(self, packet):
        # packet is already validated 
        if packet["TYPE"] == "QUESTION":
            # TODO username instead of ip
            user = User("alias", packet["ACTOR"])
            new_question = Question(user, packet["TITLE"], packet["CONTENT"])
            
            if not (packet["TITLE"] in self.questions):
                self.questions[packet["TITLE"]] = new_question

        elif packet["TYPE"] == "ANSWER":
            if packet["QUESTION_TITLE"] in self.questions:
                user = User("alias", packet["ACTOR"])
                answer_object = Answer(user, packet["CONTENT"])
                self.questions[packet["QUESTION_TITLE"]].answer(answer_object)

        elif packet["TYPE"] == "VOTE":
            assert packet["VOTE"] == "+" or packet["VOTE"] == "-"
            question_title = packet["QUESTION_TITLE"]
            if question_title in self.questions:
                user = User("alias", packet["ACTOR"])
                if packet["VOTE"] == "+":
                    self.questions[question_title].upvote(user)
                elif packet["VOTE"] == "-":
                    self.questions[question_title].downvote(user)

