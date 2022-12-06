from collections import defaultdict, Counter
import random as rnd
import pandas as pd
import plotly.express as px

class Sentiment():
    def __init__(self):
        self.scores = {}

    def read_sentiment(self, file):
        """reads the sentement txt files and returns a list of the words contained"""
        with open(file,'r') as file:
            list_words = []
            for line in file:
                word = line.strip()
                list_words.append(word)
        return list_words

    def get_scores(self, df, to_df = False):
        """reads the score files and compares each movie, getting counts of positive, negative, and neutral words"""
        pos = Sentiment.read_sentiment(self, "negative-words.txt")
        neg = Sentiment.read_sentiment(self, "positive-words.txt")
        posscore = 0
        negscore = 0
        print(df)
        for line in df["Tweet"]:
            print(line)
            if type(line) == str:
                line = line.split(" ")
                for word in line:
                    word = word.lower()
                    if word in pos:
                        posscore += 1
                    if word in neg:
                        negscore += 1
        print(posscore, negscore)
        if to_df:
            return int(posscore), int(negscore)
        return (posscore, negscore)

    def store_scores(self, df, subdict, album):
        """stores scores in the object"""
        posscore, negscore = Sentiment.get_scores(self, df[album][subdict])
        self.scores[album + subdict] = {"pos count": posscore, "neg count": negscore}

    def plot_scores(self, df, subdict, label):
        """makes a pie chart of the ratio of positive, negative, and neutral words"""
        for album in list(df.keys()):
            self.store_scores(df, subdict, album)
            if label == None:
                return None
            else:
                names = list(self.scores[album + subdict].keys())
                values = list(self.scores[album + subdict].values())
                """fig = px.pie(df, values=values, names=names, title=label)
                fig.update_traces(marker = dict(colors = ["green", "red"]))
                fig.show()"""

    def sentiment_colors(self, artist, lst):
        print(list(artist["Album Name"]))
        print(self.scores)
        colors = []
        for album in list(artist["Album Name"]):
            vals = []
            for i in lst:
                neg = self.scores[album+i]['neg count']
                pos = self.scores[album+i]['pos count']
                cnt = pos+neg
                if cnt == 0:
                    cnt = 1
                r = int((neg/(cnt)) * 255)
                g = int((pos/(cnt)) * 255)
                vals.append("rgb(" + str(r) + "," + str(g) + ",0)")
            colors.append(vals)
        artist["colors"] = colors
        return artist



