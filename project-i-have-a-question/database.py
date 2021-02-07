from question import *

class Database(object):

    def __init__(self):
        self.questions = {} # type: Dict{str -> Question}

    def update_database(self, packet):
        # packet is already validated 
        if packet["TYPE"] == "QUESTION":
            # TODO username instead of ip
            new_question = Question(packet["ACTOR"], packet["TITLE"], packet["CONTENT"])
            
            if not (packet["TITLE"] in self.questions):
                self.questions[packet["TITLE"]] = new_question

        elif packet["TYPE"] == "ANSWER":
            if packet["QUESTION_TITLE"] in self.questions:
                answer_object = Answer(packet["ACTOR"], packet["CONTENT"])
                self.questions[packet["QUESTION_TITLE"]].answer(answer_object)

        elif packet["TYPE"] == "VOTE":
            assert packet["VOTE"] == "+" or packet["VOTE"] == "-"
            question_title = packet["QUESTION_TITLE"]
            if question_title in self.questions:
                if packet["VOTE"] == "+":
                    self.questions[question_title].upvote(packet["ACTOR"])
                elif packet["VOTE"] == "-":
                    self.questions[question_title].downvote(packet["ACTOR"])

