import pymysql
import yaml


class Sentence(object):
    def __init__(self, sentence_parts, is_question):
        self.sentence_parts = sentence_parts;
        self.is_question = is_question;


class SentencePart(object):
    def __init__(self, words, particle):
        self.words = words
        self.particle = particle

    def __str__(self):
        return " ".join([w.word + f" ({w.type})" for w in self.words]) + " " + \
               (self.particle.word if self.particle is not None else "")


class WordType(object):
    def __init__(self, name, index):
        self.name = name
        self.index = index


class WordManager(object):
    def __init__(self, segmenter):
        self.segmenter = segmenter
        self.db = Database()

        self.refresh_word_types()
        self.refresh_words()

    def getWord(self, word):
        res = self.search(word)
        if res is None:
            return self.db.get_word(word)
        return res

    def refresh_words(self):
        self.words = self.db.get_common_words()

    def refresh_word_types(self):
        self.word_types = []
        for t in self.db.get_types():
            self.word_types.append(WordType(t[1], t[0]))

    def search(self, word):
        for i in range(len(self.words)):
            if self.words[i].word == word:
                return self.words[i]
        return None

    def search_word_types(self, type):
        for wt in self.word_types:
            if wt.name == type:
                return wt.index
        return self.db.add_type(type)

    def create_structure(self, in_str, out_str):
        return self.db.create_structure(in_str, out_str)

    def get_structure(self, sentence):
        ret = []
        last_was_part = True
        for structure in self.db.get_structure(sentence):
            if last_was_part:
                ret.append(SentencePart([Word("", structure[0], None)], None))
                last_was_part = False
            else:
                ret[-1].words.append(Word("", structure[0], None))
            if structure[1] is not None:
                last_was_part = True
                ret[-1].particle = Word(structure[1], "particle", None)
        return ret if len(ret) > 0 else None

    def add_relationship_between_words(self, wordOneId, words):
        for word in words:
            self.words[wordOneId].descriptors.append(word)
        self.db.add_relationship_between_words(
            self.words[wordOneId].db_id, words)

    def word_type_from_type_id(self, type_id):
        for wt in self.word_types:
            if wt.index == type_id:
                return wt.name
        return -1

    def learn_word(self, word, word_type, example):
        wordtype = self.search_word_types(word_type)
        if wordtype == -1:
            new_type = self.db.add_type(word_type)
            self.word_types.append(WordType(word_type, new_type))
            wordtype = new_type

        new_word = Word(word, wordtype, example)
        new_word.id = len(self.words)
        new_word.db_id = self.db.create_word(new_word)
        self.words.append(new_word)
        return new_word

    def save(self):
        self.db.createWords(self.words)


class Word(object):
    def __init__(self, word, word_type, example, db_id=None):
        self.db_id = db_id
        self.word = word
        self.type = word_type
        self.examples = [] if example is None else [example]
        self.descriptors = []


class Database(object):
    def __init__(self):
        self.db_config = yaml.load(open('config.yml'))['mysql']

    def connection(self):
        return pymysql.connect(host=self.db_config['host'],
                               port=self.db_config['port'],
                               user=self.db_config['username'],
                               passwd=self.db_config['password'],
                               db=self.db_config['database'], use_unicode=True,
                               charset="utf8")

    def get_structure(self, sentence):

        conn = self.connection()
        cur = conn.cursor()
        q = """SELECT s_out_p.word_type_id, s_out_p.particle
            FROM structure_parts s_out_p
            LEFT JOIN structures s_out ON s_out_p.structure_id = s_out.id
            RIGHT JOIN structure_responses s_out_r ON s_out.id = s_out_r.out_id
            LEFT JOIN structures s_in ON s_out_r.in_id = s_in.id
            WHERE s_in.is_question = {} AND s_in.id IN
                (SELECT structure_id
                FROM structure_parts main
                WHERE """.format("TRUE" if sentence.is_question else "FALSE")
        count = 0
        for i in range(len(sentence.sentence_parts)):
            for j in range(len(sentence.sentence_parts[i].words)):
                q = q + """(SELECT count(*)
                        FROM structure_parts
                        WHERE `order` = {} and word_type_id = {} and main.structure_id = structure_parts.structure_id
                        and structure_parts.particle {}) > 0""".format(count,
                                                                       sentence.sentence_parts[
                                                                           i].words[
                                                                           j].type,
                                                                       "= '" +
                                                                       sentence.sentence_parts[
                                                                           i].particle.word + "'" if j == len(
                                                                           sentence.sentence_parts[
                                                                               i].words) - 1 and sentence.sentence_parts[
                                                                                                         i].particle is not None else " IS NULL")
                if not (i == len(sentence.sentence_parts) - 1 and j == len(
                        sentence.sentence_parts[i].words) - 1):
                    q = q + " and "
                count = count + 1
        q = q + ") order by s_out_p.order"
        print(q);
        cur.execute(q)
        cur.close()
        conn.close()
        return cur

    def create_structure(self, in_sentence, out_sentence):

        conn = self.connection()
        cur = conn.cursor()
        ids = []
        for p in [in_sentence, out_sentence]:
            q = """INSERT INTO structures (is_question) VALUES ({})""".format(
                "TRUE" if p.is_question else "FALSE")
            cur.execute(q)
            ids.append(cur.lastrowid)
            q = """INSERT INTO structure_parts (structure_id, word_type_id, `order`, particle) VALUES """
            count = 0
            for i in range(len(p.sentence_parts)):
                for j in range(len(p.sentence_parts[i].words)):
                    q = q + "(last_insert_id(), {}, {}, {}),".format(p.sentence_parts[i].words[j].type, count,
                                                                     ("'" + p.sentence_parts[i].particle.word + "'") if j == len(
                                                                         p.sentence_parts[i].words) - 1 and p.sentence_parts[
                                                                                                                i].particle is not None else "NULL")
                    count = count + 1
            cur.execute(q[:-1])
        q = """INSERT INTO structure_responses (in_id, out_id) VALUES ({}, {})""".format(
            ids[0], ids[1])
        cur.execute(q)
        conn.commit()
        cur.close()
        conn.close()

    def add_type(self, type):
        conn = self.connection()
        cur = conn.cursor()
        cur.execute(f"INSERT INTO word_types (type) VALUES ('{type}')")
        conn.commit()
        cur.execute(f"SELECT id FROM word_types where type = ('{type}')")
        res_id = cur.fetchone()[0]
        cur.close()
        conn.close()
        return res_id

    def get_types(self):
        conn = self.connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM word_types")
        cur.close()
        conn.close()
        return cur

    def add_relationship_between_words(self, word_one_id, words):
        conn = self.connection()
        cur = conn.cursor()
        try:
            q = "INSERT INTO word_relationships (dep_word_id, rel_word_id) VALUES ({}) ON DUPLICATE KEY UPDATE frequency = frequency + 1".format(
                "),(".join([f"{word_one_id},{word.db_id}" for word in words if
                            word.db_id is not None]))
            cur.execute(q)
        except:
            print(q)
        cur.close()
        conn.close()
        return words

    def get_common_words(self):
        conn = self.connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM words LIMIT 50")
        words = []
        for t in cur:
            word = Word(t[1], t[2], None, t[0])
            word.id = len(words)
            words.append(word)
        cur.execute("""
        SELECT words_sentences.word_id, sentence FROM words_sentences
        LEFT JOIN sentences ON words_sentences.sentence_id = sentences.id
        INNER JOIN (SELECT * FROM words LIMIT 50) words ON words.id = words_sentences.word_id;""")

        for ex in cur:
            for i in range(len(words)):
                if words[i].db_id == ex[0]:
                    words[i].examples.append(ex[1])
                    break

        cur.execute("""
        SELECT dep_word_id, rel.* FROM word_relationships
        LEFT JOIN (SELECT * FROM words LIMIT 50) dep ON dep_word_id = dep.id
        LEFT JOIN words rel ON rel_word_id = rel.id
        WHERE dep.id IS NOT NULL;""")

        for rel in cur:
            for i in range(len(words)):
                if words[i].db_id == rel[0]:
                    words[i].descriptors.append(
                        Word(rel[2], rel[3], None, rel[1]))
                    break

        cur.close()
        conn.close()
        return words

    def get_word(self, word):
        conn = self.connection()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM words WHERE word = '{word}'")
        try:
            res = cur.fetchone()
            word = Word(res[1], res[2], None, res[0])
            cur.execute(f"""
            SELECT words_sentences.word_id, sentence from words_sentences
            LEFT JOIN sentences on words_sentences.sentence_id = sentences.id
            WHERE words_sentences.word_id = {word.db_id}""")

            for ex in cur:
                word.examples.append(ex[1])

            cur.execute(f"""
            SELECT dep_word_id, rel.* from word_relationships
            left join words dep on dep_word_id = dep.id
            left join words rel on rel_word_id = rel.id
            where dep.id = {word.db_id}""")

            for rel in cur:
                word.descriptors.append(
                    Word(rel[2], rel[3], None, rel[1]))

            cur.close()
            conn.close()
            return word
        except:
            return None

    def create_word(self, word):
        conn = self.connection()
        cur = conn.cursor()
        try:
            q = "INSERT IGNORE INTO words (word,type,frequency) VALUES ('{}', {}, {})".format(
                word.word, word.type, 0)
            cur.execute(q)
            for ex in word.examples:
                q = "INSERT IGNORE INTO sentences (sentence) VALUES ('{0}')".format(
                    ex)
                cur.execute(q)
                q = "INSERT IGNORE INTO words_sentences (word_id, sentence_id) VALUES ((Select id from words where word = '{}'),(SELECT id FROM sentences WHERE sentence = '{}'))".format(
                    word.word, ex)
                cur.execute(q)
        except:
            print(q)

        conn.commit()
        cur.close()
        conn.close()
        return cur

    def createWords(self, words):
        conn = self.connection()
        cur = conn.cursor()
        try:
            q = "INSERT IGNORE INTO words (word,type,frequency) VALUES ({})".format(
                "),(".join([f"'{a.word}',{a.type},0" for a in words if
                            a.db_id is None]))
            cur.execute(q)
        except:
            print(q)

        for w in words:
            if w.db_id is None:
                for ex in w.examples:
                    try:
                        q = "INSERT IGNORE INTO sentences (sentence) VALUES ('{0}')".format(
                            ex)
                        cur.execute(q)
                        q = "INSERT IGNORE INTO words_sentences (word_id, sentence_id) VALUES ((SELECT id FROM words WHERE word = '{1}'),(SELECT id FROM sentences WHERE sentence = '{0}'))".format(
                            ex, w.word)
                        cur.execute(q)
                    except:
                        print(q)

        conn.commit()
        cur.close()
        conn.close()
        return cur
