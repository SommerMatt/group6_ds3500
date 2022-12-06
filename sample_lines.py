'''

'''

import random
import string
import pandas as pd
from unidecode import unidecode



def read_file(file):
    '''takes in a file name and returns a list of all the lines in the file
    cleaned, punctuation removed, and all turned to lowercase'''
    df = pd.read_csv(file)
    lines = list(df['lyric'])
    for i in range(len(lines)):
        lines[i] = ''.join([s for s in lines[i] if s not in string.punctuation])
        lines[i] = lines[i].replace("’", "")
        lines[i] = lines[i].replace("“", "")
        lines[i] = unidecode(lines[i])

    return lines

def begin_end(lines):
    '''finds the beginning and ending words of lines and puts them in a list'''
    begin = []
    ending = []
    for line in lines:
        begin.append(line.split()[0])
        ending.append(line.split()[-1])

    return begin, ending

def make_ngrams(lines):
    ''' Function: make_ngrams
        Parameters: list of lines (strings)
        Returns: dictionary of key = word, value = list of words that follow
    '''
    ngrams = {}
    for line in lines:
        wordlist = line.split()
        for i in range(len(wordlist) - 1):
            if wordlist[i] not in ngrams:
                ngrams[wordlist[i]] = []
            ngrams[wordlist[i]].append(wordlist[i + 1])
    return ngrams
    
def generate_line(begin, ending, ngrams):
    ''' Function: line
        Parameters: list of begin-words, list of end-words,
                    dictionary of key = word, value = list of followed-by
        Returns: one line of an announcement
    '''
    curr_word = random.choice(begin)
    sentence = curr_word
    while not curr_word in ending:
        curr_word = random.choice(ngrams[curr_word])
        sentence += " " + curr_word
    return sentence


def sample_lines(file):
    # read and clean file
    lines = lines = read_file('07-lover.csv')
    begin, end = begin_end(lines)

    # Generate a dictionary of 2-grams
    ngrams = make_ngrams(lines)

    # generate sample lines
    sample_lines = []
    for i in range(50):
        line = generate_line(begin, end, ngrams)
        if line != 'I':
            sample_lines.append(line + ".")

    return sample_lines

def ml():
    file_lst = ['01-taylor_swift.csv' , '02-fearless_taylors_version.csv', '03-speak_now-deluxe_package.csv',
                '04-red_delux_edition.csv' , '05-1989_deluxe.csv', '06-reputation.csv' , '07-lover.csv' , 'folklore_delux_version.csv',
                '09-evermore_delux_version.csv']

    album = ['Taylor_Swift' , 'Fearless' , 'Speak_Now' , 'Red', '1989' , 'Reputation', 'Lover',
             'Folklore', 'Evermore']

    dict = {}
    for i in range(len(album)):
        dict[album[i]] = sample_lines(file_lst[i])

    drake = pd.read_csv('drake_data.csv')

    drake_sample = sample_lines('drake_data.csv')

    print(drake_sample)

    print('\n' , dict)
    return dict, drake_sample
        
        


        
        
        