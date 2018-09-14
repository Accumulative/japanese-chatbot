# GREETINGS = ["こんにちは", "はい"]

from tinysegmenter import *
from mysql_connector import *
import string


class Bot(object):

    def check_mistake(self, input):
        if "" == input:
            return True
        return False

    def get_by_type(self, input, type):
        response = []
        for word_raw in self.segmenter.tokenize(input):
            word = self.manager.search(word_raw)
            if word != None:
                if self.manager.word_type_from_type_id(word.type) in type:
                    response.append(word)
            else:
                new_word = self.get_new_word(word_raw, None)
                if new_word is not None:
                    if self.manager.word_type_from_type_id(new_word.type) in type:
                        response.append(new_word)
        return response

    def get_new_word(self, token, example):
        print(f"<{token}>って言う言葉はどのタイプですか？", [
              a.name for a in self.manager.word_types])
        token_type = input()
        if not self.check_mistake(token_type):
            return self.manager.learn_word(token, token_type, example)
        else:
            print("すみません、別の話の方がね。もう一度チャットしてみよう")
        return None

    def clean_message(self, message):
        translator = str.maketrans('', '', string.punctuation)
        return message.translate(translator)

    def respond(self, message):
        cleaned = self.clean_message(message)
        tokens = self.segmenter.tokenize(cleaned)
        count = 0
        nouns = 0
        for token in tokens:
            word = self.manager.search(token)
            if word is None:
                word = self.get_new_word(token, message)
                if word is not None:
                    count = count + 1

            if word is not None:
                if self.manager.word_type_from_type_id(word.type) == "noun":
                    nouns = nouns + 1
                    if len(word.examples) > 3:
                        # make_response_from_examples(learntWords[word_pos].examples)
                        pass
                    else:
                        print(f"{token}に関して、もっと説明貰ってもいいですか？")
                        new_description = input()
                        rels = self.get_by_type(
                            new_description, ['adj', 'noun'])
                        self.manager.add_relationship_between_words(
                            word.id, rels)

                        if len(rels) > 0:
                            print("{}は{}ですね！ありがとうございます！".format(
                                token, "し".join([a.word for a in rels])))

        if nouns == 0:
            print("これはふつの話ではないですね")
        if count > 0 and nouns != 0:
            print("すみません、今分かりました。ありがとうございます。")

    def __init__(self):
        self.segmenter = TinySegmenter()
        self.manager = WordManager(self.segmenter)
        print("チャットは始まったよ。")
        msg_in = input()
        while(msg_in != "/end"):
            response = self.respond(msg_in)
            print(response)
            msg_in = input()

        self.manager.save()


bot = Bot()
