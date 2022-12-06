from twitter import Scraper
import pandas as pd
import pprint as pp
from sentiment import Sentiment
import pickle

def agragate_lyric_data(csv):
    lyric_df = pd.read_csv(csv)
    df = lyric_df.groupby("album").sum()
    df = df[["lyrics"]].copy()
    df.reset_index(inplace=True)
    print(df["lyrics"])
    return df

def process_taylor_lyrics(df):
    lyrics = []
    for i in range(0,len(df)):
        lyrics.append(df["lyric"][i])
    l = ' '.join(lyrics)
    return l

def make_drake():
    drake = pd.read_csv('drake.csv')
    drake = drake[["Album Name", "Release Date", "Sales_us"]].copy()
    drake["Sales_us"] = drake["Sales_us"].astype(int)
    drake_lyrics = agragate_lyric_data("drake_data.csv")
    drake_lyrics["Album Name"] = drake_lyrics["album"]
    new_drake = pd.merge(drake, drake_lyrics, on="Album Name")
    return drake, new_drake

def process_taylor():
    taylor = pd.read_csv('taylor.csv')
    taylor = taylor[["Album Name", "Release Date", "Sales_us"]].copy()
    taylor["Sales_us"] = taylor["Sales_us"].astype(int)
    print(taylor)
    taylor_swift = process_taylor_lyrics(pd.read_csv('01-taylor_swift.csv'))
    fearless = process_taylor_lyrics(pd.read_csv('02-fearless_taylors_version.csv'))
    speak_now = process_taylor_lyrics(pd.read_csv('03-speak_now_deluxe_package.csv'))
    red = process_taylor_lyrics(pd.read_csv('04-red_deluxe_edition.csv'))
    ninteeneightynine = process_taylor_lyrics(pd.read_csv('05-1989_deluxe.csv'))
    reputation = process_taylor_lyrics(pd.read_csv('06-reputation.csv'))
    lover = process_taylor_lyrics(pd.read_csv('07-lover.csv'))
    folkore = process_taylor_lyrics(pd.read_csv('08-folklore_deluxe_version.csv'))
    evermore = process_taylor_lyrics(pd.read_csv('09-evermore_deluxe_version.csv'))
    # midnights = ["no",  "lyric", "data"]
    taylor_lyrics = [taylor_swift, fearless, speak_now, red, ninteeneightynine, reputation, lover,
                     folkore, evermore]
    taylor["lyrics"] = taylor_lyrics
    print(taylor)
    return taylor


def main():
    drake, new_drake = make_drake()
    taylor = process_taylor()
    S = Scraper()
    S.add_artist(new_drake, "Drake")
    S.add_artist(taylor, "Taylor Swift")
    S.sankey(S.data["Drake"], "lyrics", 'Word', 'Count')
    S.sankey(S.data["Drake"], 'Word', 'Count', key1 = "tweets_after")
    S.sankey(S.data["Drake"], 'Word', 'Count', key1="tweets_before")
    Sent = Sentiment()
    Sent.plot_scores(S.data["Drake"], "tweets_after_raw", "tweets_after_raw")
    Sent.plot_scores(S.data["Drake"], "tweets_before_raw", "tweets_before_raw")
    sent_scores = Sent.sentiment_colors(new_drake, ["tweets_after_raw", "tweets_before_raw"])
    print(sent_scores)
    S.artist_wordcloud("Drake", sent_scores)
    Sent = Sentiment()
    Sent.plot_scores(S.data["Taylor Swift"], "tweets_after_raw", "tweets_after_raw")
    Sent.plot_scores(S.data["Taylor Swift"], "tweets_before_raw", "tweets_before_raw")
    sent_scores = Sent.sentiment_colors(taylor, ["tweets_after_raw", "tweets_before_raw"])
    print(sent_scores)
    S.artist_wordcloud("Taylor Swift", sent_scores)
    df = S.get_tsd(drake, "Drake")
    df.to_csv("drake_tsd_15")
    tdf = S.get_tsd(taylor, "Taylor Swift")
    tdf.to_csv("taylor_swift_tsd_15")

main()