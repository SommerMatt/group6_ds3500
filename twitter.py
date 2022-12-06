import snscrape.modules.twitter as sntwitter
import pandas as pd
from collections import defaultdict, Counter, OrderedDict
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, RegexpTokenizer
import pandas as pd
import sankey as sk
from sentiment import Sentiment
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime as dt
import datetime as datetime
from datetime import timedelta
import sankey2 as sk
from wordcloud import WordCloud, STOPWORDS
import multiprocessing.sharedctypes as mt
from sentiment import Sentiment


class Scraper():
    def __init__(self):
        """ Constructor """
        self.data = defaultdict(dict)  # extracted data (state)

    def scrape_twitter(self, initial_d, final_d, str_querry, numtweets = 1000):
        string = str(str_querry + ' since:' + initial_d + ' until:' + final_d)

        # Creating list to append tweet data to
        attributes_container = []

        # Using TwitterSearchScraper to scrape data and append tweets to list
        for i, tweet in enumerate(
                sntwitter.TwitterSearchScraper(string).get_items()):
            if i > numtweets:
                break
            attributes_container.append([tweet.user.username, tweet.date, tweet.likeCount, tweet.sourceLabel, tweet.content])

        # Creating a dataframe to load the list
        tweets_df = pd.DataFrame(attributes_container,
                                 columns=["User", "Date Created", "Number of Likes", "Source of Tweet", "Tweet"])
        return tweets_df

    def find_date_range(self, release_date, num_days = 7):
        release_date = dt.strptime(release_date, '%Y-%m-%d')
        initial_d = release_date - datetime.timedelta(days=num_days)
        final_d = release_date + datetime.timedelta(days=num_days)
        return initial_d, final_d

    def clean_sentence(self, sent, lyrics = False):
        lyrics_filter = ['Intro', 'Verse','Chorus','Produced']
        """removes stopwords from each sentence"""
        stop_words = set(stopwords.words('english'))
        tokenizer = RegexpTokenizer(r'\w+')
        word_tokens = tokenizer.tokenize(sent)
        filt = [w for w in word_tokens if not w.lower() in stop_words and not w.isdigit()]
        if lyrics:
            filtered_sentence = [w for w in word_tokens if not w.lower() in lyrics_filter]
            return filtered_sentence
        else:
            return filt

    def count_word_freq(self, words, album):
        """counts the words in each sentence"""
        for word in words:
            if word not in album.keys():
                album[word] = 1
            else:
                album[word] += 1
        return album

    def process_raw(self, df):
        words = {}
        for i in range(len(df)):
            clean_sent = self.clean_sentence(df["Tweet"][i])
            self.count_word_freq(clean_sent, words)
        return dict(reversed(sorted(words.items(), key=lambda item: item[1])))

    def clean_lyrics(self, lyrics):
        words = {}
        clean_sent = self.clean_sentence(lyrics)
        self.count_word_freq(clean_sent, words)
        return dict(reversed(sorted(words.items(), key=lambda item: item[1])))

    def pull_album(self, artist_csv, name):
        artist_dict = {}
        for i in range(len(artist_csv)):
            album = {}
            album["sales"] = artist_csv["Sales_us"][i]
            initial_d, final_d = self.find_date_range(artist_csv["Release Date"][i])
            twitterafter = self.scrape_twitter(artist_csv["Release Date"][i], str(final_d), \
                                                        str(name), numtweets=1000)
            twitterbefore = self.scrape_twitter(str(initial_d), artist_csv["Release Date"][i], \
                                                         str(name), numtweets = 1000)
            album["tweets_after_raw"] = twitterafter
            album["tweets_before_raw"] = twitterbefore
            album["tweets_after"] = self.process_raw(twitterafter)
            album["tweets_before"] = self.process_raw(twitterbefore)
            album["lyrics"] = self.clean_lyrics(artist_csv["lyrics"][i])
            artist_dict[artist_csv["Album Name"][i]] = album
        return artist_dict

    def list_dict(self, d, key1, n=15):
        ''' creats lists based off a dictionary and compiles then into a dataframe'''
        ls1 = []
        ls2 = []
        ls3 = []
        for key in list(d.keys()):
            j = 0
            for k in d[key][key1]:
                if j < n:
                    ls1.append(key)
                    ls2.append(k)
                    ls3.append(d[key][key1][k])
                    j += 1

        dictionary = {'Album': ls1, 'Word': ls2, 'Count': ls3}
        return pd.DataFrame(dictionary)

    def sankey(self, d, *args , n = 15, key1 = 'lyrics'):
        ''' makes a sankey diagram'''
        lst = list(args)
        df = self.list_dict(d, key1, n)
        sk.make_sankey(df, 'Album', 'Word', vals='Count')

    def create_wordcloud(self, df, background_color):
        '''creates basis for a wordcould'''
        df['line'] = [str(i) for i in df['Tweet']]
        text = ' '.join(i for i in df['Tweet'])
        if len(text) == 0:
            text = "no text available album before twitter creation"
        wordcloud = WordCloud(stopwords=STOPWORDS,
                              width=480,
                              height=480,
                              background_color=background_color,
                              max_words=60).generate(text)

        return wordcloud

    def wc_subplot(self, texts, colors, n, album):
        '''plots user generated number of wordclouds into a subplot'''
        fig = plt.figure()
        for i in range(len(texts)):
            ax = fig.add_subplot(1, n, i + 1)
            wordcloud = self.create_wordcloud(texts[i], colors[i])

            ax.imshow(wordcloud)
            ax.axis('off')

        fig.savefig(album + "wordcloud.jpg")

    def artist_wordcloud(self, name, colors):
        for i in range(0, len(list(self.data[name].keys()))):
            album = list(self.data[name].keys())[i]
            self.wc_subplot([self.data[name][album]["tweets_before_raw"], self.data[name][album]["tweets_after_raw"]],
                            colors["colors"][i], 2, album)

    def add_artist(self, artist_csv, name):
        self.data[name] = self.pull_album(artist_csv, name)

    def get_tsd(self, artist_data, name):
        Sent = Sentiment()
        oldest = dt.strptime(artist_data["Release Date"][0], '%Y-%m-%d')
        newest = dt.strptime(artist_data["Release Date"][len(artist_data)-1], '%Y-%m-%d')
        timeframe = newest - oldest
        print(timeframe.days)
        days = []
        pscores = []
        nscores = []
        max = timeframe.days
        i = 0
        while i <= max+1:
            tweets = self.scrape_twitter(str(oldest+timedelta(days = i)), str(oldest+timedelta(days = i+1)),
                                         name, numtweets = 100)
            days.append(str(oldest+timedelta(days = i)))
            pos, neg = Sent.get_scores(tweets)
            pscores.append(pos)
            nscores.append(neg)
            i += 15
        d = {"days": days, "pos_scores":pscores, "neg_scores":nscores}
        return pd.DataFrame(d)






