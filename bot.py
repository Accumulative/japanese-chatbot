from tinysegmenter import *
from mysql_connector import *
import string
from helper import *
from search import search

PARTICLES = ["は","ね","を","が","に","で","だ","の"]
ENDINGS = ["です","ます"]
QUESTIONS = ["か","ですか","の","のか"]
QUESTION_OTHER = ["だれ", "誰", "なに", "何", "どの", "いつ"]
POINTERS = ['それ','これ','あれ']
PEOPLE = ['私','あなた','わたし','彼','かれ','彼女']
PUNCTUATION = ["？", "。"]


class Bot(object):

    def ignorable(self, token):
        if token in PARTICLES or token in ENDINGS or token in QUESTIONS:
            return True

        return False

    def get_by_type(self, input, type):
        response = []
        for word_raw in self.segmenter.tokenize(input):
            word = self.manager.getWord(word_raw)
            if word is not None:
                if self.manager.word_type_from_type_id(word.type) in type:
                    response.append(word)
            else:
                new_word = self.get_new_word(word_raw, None)
                if new_word is not None:
                    if self.manager.word_type_from_type_id(new_word.type) in type:
                        response.append(new_word)
        return response

    def get_structure(self, sentence, is_question):
        matching_array = []
        last_particle = -1
        for i in range(len(sentence)):
            if sentence[i].type == "particle":
                matching_array.append(SentencePart(sentence[last_particle+1:i], sentence[i]))
                last_particle = i
        
        if last_particle != 0:
            matching_array.append(SentencePart(sentence[last_particle+1:], None))
            return Sentence(matching_array, is_question)
        else:
            return None

    def replace_str_arr(self, input_str, rep_array):
        ret = input_str
        for rep in rep_array:
            ret = ret.replace(rep, "")

        return ret

    def replace_arr_arr(self, input_array, rep_array):
        return [ch for ch in input_array if ch not in rep_array]

    def is_question(self, statement):
        for e in QUESTIONS:
            if statement[-len(e):] == e or statement[-len(e)-1:] == e + "？" or statement[-len(e)-1:] == e + "?":
                return True

    def set_subject(self, sentence):
        for part in sentence.sentence_parts:
            if part.particle == "は":
                self.current_subject = part
                return
        self.current_subject = None

    def is_command(self, statement):
        if "を検索して" in statement:
            to_search = statement.split("を")[0]
            self.add_reply(f"はい、今<{to_search}>検索しています。ちょっと待ってください。")
            word_info = search(to_search)
            if word_info is not None:
                self.update_dict(word_info)
                self.add_reply("見つかった。右の辺にを見えます。")
                if self.manager.getWord(to_search) is None:
                    self.add_reply("私も知らなかった。これを勉強しています。")
                    self.manager.learn_word(to_search, word_info.types[0], None)
            else:
                self.add_reply("すみません。見つからなかった。")
            return True
        return False

    def get_new_word(self, token, example):
        word_info = search(token)
        answer = "No"
        if word_info is not None:
            
            self.update_dict(word_info)
            answer = self.ask_func(f"{token}は分かりませんでした。検査したので、これは正解ですか？", ["Yes", "No"])

        if answer == "No":
            token_type = self.ask_func(f"<{token}>って言う言葉はどのタイプですか？", [
                a.name for a in self.manager.word_types]+["Skip"])
            if token_type != "Skip":
                return self.manager.learn_word(token, token_type, example)
            else:
                self.add_reply("すみません、別の話の方がね。もう一度チャットしてみよう")
        else:
            return self.manager.learn_word(token, word_info.types[0], example)
        return None

    def clean_message(self, tokens):
        ret = self.replace_arr_arr(tokens, PUNCTUATION + list(string.punctuation) + ENDINGS + QUESTIONS)
        return ret

    def check_basic_words(self, token):
        if token in PARTICLES:
            return Word(token, "particle", None)
        elif token in PEOPLE or token in POINTERS:
            return Word(token, self.manager.search_word_types("n"), None)
        elif token in QUESTION_OTHER:
            return Word(token, self.manager.search_word_types("qn"), None)

        return None
            
    def make_response(self, input_word_list, is_question):
        input_structure = self.get_structure(input_word_list, is_question)
        self.set_subject(input_structure)
        response_structure = self.manager.get_structure(input_structure)
        if response_structure is not None:
            return "/".join([str(a) for a in response_structure])
        else:
            result = self.add_reply("返事はどのフォーマットしてもいいですか？", True)
            if result == "じゃ、次":
                return
            word_list = self.get_word_list(result)
            out_is_question = self.is_question(word_list)
            res_structure = self.get_structure(word_list, out_is_question)
            self.manager.create_structure(input_structure, res_structure)
            return "了解です."

    def respond(self, message):
        
        if message == "":
            return

        if not self.is_command(message):
            
            sentence = self.get_word_list(message)
            is_question = self.is_question(message)
            if None in sentence:
                self.add_reply("全部わりませんから、返事できないです。")
            else:
                res = self.make_response(sentence, is_question)
                if res is None:
                    self.add_reply("これは普通な話ではないですね。")
                else:
                    self.add_reply(str(res))

    def get_word_list(self, message):
        tokens = self.segmenter.tokenize(message)
        tokens = self.clean_message(tokens)
        word_list = []
        count = 0
        for token in tokens:
            word = self.check_basic_words(token)
            print(word, token)
            if word is None:
                word = self.manager.getWord(token)
                if word is None:
                    word = self.get_new_word(token, message)
                    if word is not None:
                        count = count + 1

                if word is not None:
                    if self.manager.word_type_from_type_id(word.type) == "noun":
                            
                        new_description = self.add_reply(f"{token}に関して、もっと説明貰ってもいいですか？", True)
                        rels = self.get_by_type(
                            new_description, ['adj', 'noun'])
                        self.manager.add_relationship_between_words(
                            word.id, rels)

                        if len(rels) > 0:
                            self.add_reply("{}は{}ですね！ありがとうございます！".format(
                                token, "し".join([a.word for a in rels])))
            word_list.append(word)
        return word_list

    def __init__(self, add_reply, ask_func, update_dict):
        self.segmenter = TinySegmenter()
        self.manager = WordManager(self.segmenter)
        self.add_reply = add_reply
        self.ask_func = ask_func
        self.update_dict = update_dict
        self.current_subject = None