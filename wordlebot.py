#!/usr/bin/python3
import sys
import re
import random
from termcolor import colored
import copy
import math
import time
import pickle
import argparse


letters = [chr(x) for x in range(ord('a'), ord('z')+1)]
possible_in_solution = [set(letters[:]) for x in range(0,5)]

with open('wordle-allowed-guesses.txt') as f: dictionary = f.read().splitlines()
with open('wordle-answers-alphabetical.txt') as f: wordle_words = f.read().splitlines()
for word in wordle_words:
    dictionary.append(word)
dictionary.sort()

dict_index = {}
ind = 0
for word in dictionary:
    dict_index[word] = ind
    ind = ind + 1

def get_match_pattern(word1, word2):
    ans = 0
    green = set()
    green_word2 = set()
    yellow_word2 = set()
    for i in range(len(word1)):
        #Get greens
        if word1[i] == word2[i]:
            green.add(i)
            green_word2.add(i)
            ans = ans | (2 << (2*(4-i)))
    for i in range (len (word1)):
        if i not in green:
            yellow = False
            for j in range(len(word2)):
                if j not in green_word2 and j not in yellow_word2:
                    if word1[i] == word2[j]:
                        yellow_word2.add(j)
                        yellow = True
                        break
            if yellow:
                ans = ans | 1 << (2*(4-i))
    return ans
def translate_pattern(pattern): #'gwywg' etc
    ans = 0
    for i in range(len(pattern)):
        if pattern[i] == 'g':
            ans = ans | (2 << (2*(4-i)))
        elif pattern[i] == 'y':
            ans = ans | (1 << (2*(4-i)))
    return ans

def get_color_pattern(pattern):
    result = ""
    for i in [4,3,2,1,0]:
        let_patt = pattern >> (2*i) & 3
        if let_patt == 0:
            result = result + "w"
        elif let_patt == 1:
            result = result + "y"
        elif let_patt == 2:
            result = result + "g"
    return result

def  print_pattern(pattern):
    for i in [4,3,2,1,0]:
        let_patt = pattern >> (2*i) & 3
        if let_patt == 0:
            print ('W', end='')
        elif let_patt == 1:
            print ('Y', end='')
        elif let_patt == 2:
            print ('G', end='')
        else:
            print ('Error!@!!!')
    print ('')

def generate_database():
    dbase = {}
    count = 0
    for word1 in dictionary:
        dbase[word1] = []
        for word2 in dictionary:
            pattern = get_match_pattern(word1, word2)
            dbase[word1].append(pattern)
        count = count + 1
        print (str(count) + ' / ' + str(len(dictionary)))
    with open('wordle_dbase.pickle', 'wb') as handle:
        pickle.dump(dbase, handle, protocol=pickle.HIGHEST_PROTOCOL)

def read_database():
    with open ('wordle_dbase.pickle', 'rb') as handle:
        return pickle.load(handle)

def get_pattern_from_known_solution(guess, solution):
    pattern = get_match_pattern(guess, solution)
    return get_color_pattern(pattern)

def GetRemainingWords(wordle_dbase, guess, pattern, possible_words):
    transpat = translate_pattern(pattern)
    rec = wordle_dbase[guess]
    possible_words_out = []
    for word in possible_words:
        ind = dict_index[word]
        if rec[ind] == transpat:
            possible_words_out.append(word)
    return possible_words_out

def get_entropy(wordle_dbase, word, possible_words):
    rec = wordle_dbase[word]
    hist = {}
    for w in possible_words:
        ind = dict_index[w]
        patt = rec[ind]
        if patt in hist.keys():
            hist[patt] = hist[patt] + 1
        else:
            hist[patt] = 1
    entropy = 0
    for key in hist:
        count = hist[key]
        p = count / len(possible_words)
        entropy = entropy - (p * math.log2(p))
    return entropy

def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage="%(prog)s (--generate_database) (--hardmode[not implemented]) (--use_full_wordlist[dordle mode]) (--starting_word_entropies)",
        description="Run the dordle bot!"
    )
    parser.add_argument("-g","--generate_database", action="store_true", help="Generate the match database. Takes about 20 mins. Only needs to be done once")
    parser.add_argument("--hardmode", action="store_true", help="Not implemented yet")
    parser.add_argument("-f","--use_full_wordlist", action="store_true", help="Use the full wordlist rather than the wordle list (dordle appears to use this)")
    parser.add_argument("-s","--starting_word_entropies", action="store_true", help="Show first word entropies (takes a few seconds)")
    parser.add_argument("-t","--target_mode", type=str, help="Show patterns based on target solution (use if you know the correct word)")
    return parser

if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()
    if args.generate_database:
        generate_database()
        exit()
    print ('Loading database...')
    wordle_dbase = read_database()
    print ('Database loaded')
    if args.use_full_wordlist:
        possible_words = dictionary
    else:
        possible_words = wordle_words
    if args.starting_word_entropies:
        entropies = list(map(lambda word : get_entropy(wordle_dbase, word, possible_words), wordle_dbase))
        word_entropies = list(zip(entropies, wordle_dbase))
        word_entropies.sort(reverse=True)
        print ('Best starting words')
        print (word_entropies[0:30])
 
    while(True):
        guess = str(input('What word did you guess:>'))
        print('The entropy of this guess is ' + str(get_entropy(wordle_dbase, guess, possible_words))+ ' bits')
        if (args.target_mode):
            color_string = get_pattern_from_known_solution(guess, args.target_mode)
            print ("Auto color pattern for known solution: " + color_string)
        else:
            color_string = str(input('What color pattern do you get? i.e. yyggw? :>'))

        possible_words = GetRemainingWords(wordle_dbase, guess, color_string, possible_words)
        entropies = list(map(lambda word : get_entropy(wordle_dbase, word, possible_words), wordle_dbase))
        word_entropies = list(zip(entropies, wordle_dbase))
        word_entropies.sort(reverse=True)
        
        print ('Top 30 guess words to use with associated entropy (higher is better)' + str(word_entropies[0:30]))
        if (len(possible_words) < 100):
            print ('Possible words remaining: ' + str(possible_words))
        else:
            print ('Have ' + str(len(possible_words)) + ' words remaining')
