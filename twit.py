#!/usr/bin/env python

# todo:
# handle plurals with cannonical
# handle http url errors

import urllib2
import json
import re
import math
import tweepy
from tweepy import auth
import random
from credentials import credentials
pws = credentials()

#pws object from credentials.py that holds all the credentials
# pws = {
# "WORDNIK_API_KEY" : "xyz",
# "CONSUMER_KEY" : "xyz",
# "CONSUMER_SECRET" :  "xyz",
# "ACCESS_TOKEN" : "xyz",
# "ACCESS_TOKEN_SECRET" : "xyz"
# }

auth = auth.OAuthHandler(pws["CONSUMER_KEY"], pws["CONSUMER_SECRET"])
auth.set_access_token(pws["ACCESS_TOKEN"], pws["ACCESS_TOKEN_SECRET"])
API = tweepy.API(auth)

# to debug http requests
# h=urllib2.HTTPHandler(debuglevel=1)
# opener = urllib2.build_opener(h)
# urllib2.install_opener(opener)


def getPartOfSpeech(word):
  endpoint = "http://api.wordnik.com:80/v4/word.json/" + word + "/definitions?limit=1&includeRelated=true&useCanonical=false&includeTags=false&api_key=" + pws["WORDNIK_API_KEY"];
  response = urllib2.urlopen(endpoint)
  data = json.loads(response.read())

  if data != [] and "partOfSpeech" in data[0]:
    part_of_speech = data[0]["partOfSpeech"]
    # print "part of speech: " + part_of_speech
    if part_of_speech == 'conjunction' or part_of_speech == 'proper-noun' or part_of_speech == 'pronoun' or part_of_speech == 'abbreviation' or part_of_speech == 'preposition':
      part_of_speech = False
  else:
    part_of_speech = False

  return part_of_speech


def replace(word):

  # print "replace: " + word

  capitalized = True if re.match("[A-Z]", word[0]) else False
  part_of_speech = getPartOfSpeech(word.lower())
  new_word = None

  if part_of_speech:
    random = "http://api.wordnik.com:80/v4/words.json/randomWords?hasDictionaryDef=true&includePartOfSpeech="
    details = "&minCorpusCount=1000&maxCorpusCount=-1&minDictionaryCount=2&maxDictionaryCount=-1&minLength=" + str(len(word) - 2) + "&maxLength=" + str(len(word) + 2) + "&limit=1&api_key="
    endpoint = random + part_of_speech + details + pws["WORDNIK_API_KEY"]
    response = urllib2.urlopen(endpoint).read()
    data = json.loads(response)

    if data != [] and "word" in data[0]:
      new_word = data[0]["word"]
      new_word = new_word.title() if capitalized else new_word
      # print "replace with: " + new_word
    else:
      # print "!! no replacement, no new word"
      new_word = False

  else:
    #print "!! no replacement, no part of speech"
    new_word = False

  return new_word


def writeNewTweet(status):

  print status.text
  phrase = status.text.split()

  non_words = [ word for word in phrase if re.match('.*[\d\W_-]+', word) ]

  # add all possible variants of URL to exempt list
  urls = []
  for url in status.entities["urls"]:
    urls.append(url["url"])
    urls.append(url["expanded_url"])
    urls.append(re.sub('[\W_]+$', '', url["display_url"]))

  exempt = non_words + urls

  # populate lists of phrase indeces of legit/exempt words
  exempt_indeces = []
  legit_indeces = []
  for i in range(len(phrase)):
    if phrase[i] in exempt:
      exempt_indeces.append(i)
    else:
      legit_indeces.append(i)

  #calculate the number of words to replace 0, 1 or 1/4 of phrase length
  replace_freq = 0 if len(legit_indeces) == 0 else int((math.floor(len(phrase))) / 4) or 1

  new_phrase = replaceWords(phrase, replace_freq, exempt_indeces, legit_indeces)

  tweet = None
  if len(new_phrase) + 6 + len(status.author.screen_name) < 140:
    tweet = new_phrase + " via @" + status.author.screen_name
  else:
    tweet = new_phrase

  return tweet


def replaceWords(phrase, replace_freq, exempt_indeces, legit_indeces):

  if replace_freq == 0 or len(legit_indeces) == 0:
    new_phrase = " ".join(phrase)
    return new_phrase

  else:
    # choose random index from legit_indeces
    to_replace = int(math.floor(len(legit_indeces) * random.random()))

    # get the value of the list element with that random index
    replace_index = legit_indeces[ to_replace ]

    # move this number from legit to exempt
    del legit_indeces[ to_replace ]
    exempt_indeces.append(to_replace)

    #replace word in phrase
    word_to_replace = phrase[ int(replace_index) ]
    new_word = replace(word_to_replace)

    if new_word:
      #replace word at given index
      phrase[ int(replace_index) ] = new_word
      replace_freq -= 1

    #recurse!
    return replaceWords(phrase, replace_freq, exempt_indeces, legit_indeces)


def postTweet(tweet):
  API.update_status(tweet)

#for i in range(5):
#status = API.home_timeline()[0]
#latest =  writeNewTweet(status)
#postTweet(latest)
