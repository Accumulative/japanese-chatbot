#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  9 17:09:56 2018

@author: kieranburke
"""
import yaml
import pymysql
import datetime


class WordType(object):
    def __init__(self, name, index):
        self.name = name
        self.index = index


class WordManager(object):
    def __init__(self, segmenter):
        self.segmenter = segmenter
        self.db = mysql_database()

        self.refresh_word_types()
        self.refresh_words()

    def refresh_words(self):
        self.words = self.db.getCommonWords()

    def refresh_word_types(self):
        self.word_types = []
        for t in self.db.getTypes():
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
        return -1

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
        if wordtype != -1:
            new_word = Word(word, wordtype, example)
            new_word.id = len(self.words)
            new_word.db_id = self.db.createWord(new_word)
            self.words.append(new_word)
            return new_word

        return None

    def save(self):
        self.db.createWords(self.words)


class Word(object):
    def __init__(self, word, word_type, example, db_id=None):
        self.db_id = db_id
        self.word = word
        self.type = word_type
        self.examples = [] if example is None else [example]
        self.descriptors = []


class mysql_database(object):
    def __init__(self):
        self.db_config = yaml.load(open('config.yml'))['mysql']

    def connection(self):
        return pymysql.connect(host=self.db_config['host'], port=self.db_config['port'], user=self.db_config['username'], passwd=self.db_config['password'], db=self.db_config['database'], use_unicode=True, charset="utf8")

    def getTypes(self):
        conn = self.connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM word_types")
        cur.close()
        conn.close()
        return cur

    def add_relationship_between_words(self, word_one_id, words):
        conn = self.connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO word_relationships (dep_word_id, rel_word_id) VALUES ({}) ON DUPLICATE KEY UPDATE frequency = frequency + 1".format("),(".join([f"{word_one_id},{word.db_id}" for word in words if word.db_id is not None])))
        cur.close()
        conn.close()
        return words

    def getCommonWords(self):
        conn = self.connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM words LIMIT 50")
        words = []
        for t in cur:
            word = Word(t[1], t[2], None, t[0])
            word.id = len(words)
            words.append(word)
        cur.execute("""
        SELECT words_sentences.word_id, sentence from words_sentences
        LEFT JOIN sentences on words_sentences.sentence_id = sentences.id
        inner join (select * from words LIMIT 50) words on words.id = words_sentences.word_id;""")

        for ex in cur:
            for i in range(len(words)):
                if words[i].db_id == ex[0]:
                    words[i].examples.append(ex[1])
                    break

        cur.execute("""
        SELECT dep_word_id, rel.* from word_relationships
        left join (select * from words LIMIT 50) dep on dep_word_id = dep.id
        left join words rel on rel_word_id = rel.id
        where dep.id is not NULL;""")

        for rel in cur:
            for i in range(len(words)):
                if words[i].db_id == rel[0]:
                    words[i].descriptors.append(
                        Word(rel[2], rel[3], None, rel[1]))
                    break

        cur.close()
        conn.close()
        return words

    def searchWords(self, term):
        conn = self.connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM words WHERE word like '%{}%'")
        cur.close()
        conn.close()
        return cur

    def createWord(self, word):
        conn = self.connection()
        cur = conn.cursor()
        try:
            q = "INSERT IGNORE INTO words (word,type,frequency) VALUES ('{}', {}, {})".format(
                word.word, word.type, 0)
            cur.execute(q)
            w_id = cur.execute("Select last_insert_id()")
            print(w_id)
            print(w_id[0])
            for ex in word.examples:
                q = "INSERT IGNORE INTO sentences (sentence) VALUES ('{0}')".format(
                    ex)
                cur.execute(q)
                q = "INSERT IGNORE INTO words_sentences (word_id, sentence_id) VALUES ({1},(SELECT id FROM sentences WHERE sentence = '{0}'))".format(
                    ex, w_id)
                cur.execute(q)
        except:
            print(w_id)

        conn.commit()
        cur.close()
        conn.close()
        return cur

    def createWords(self, words):
        conn = self.connection()
        cur = conn.cursor()
        try:
            q = "INSERT IGNORE INTO words (word,type,frequency) VALUES ({})".format(
                "),(".join([f"'{a.word}',{a.type},0" for a in words if a.db_id is None]))
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

    # def getAllOpenTrades(self):
    #     conn = self.connection()
    #     cur = conn.cursor()
    #     cur.execute("SELECT * FROM trades where close_date is NULL")
    #     cur.close()
    #     conn.close()

    #     output = []
    #     for r in cur:
    #         trade = BotTrade(self.parent,0,0 if r[3] is None else float(r[3]), 0 if r[1] is None else float(r[1]), 0, 0, float(r[6]), 0, 1)
    #         trade.externalId = r[0]
    #         output.append(trade);

    #     return output
