#!/usr/bin/python -tt
# Copyright 2010 Google Inc.
# Licensed under the Apache License, Version 2.0
# http://www.apache.org/licenses/LICENSE-2.0

# Google's Python Class
# http://code.google.com/edu/languages/google-python-class/

"""Wordcount exercise
Google's Python class

The main() below is already defined and complete. It calls print_words()
and print_top() functions which you write.

1. For the --count flag, implement a print_words(filename) function that counts
how often each word appears in the text and prints:
word1 count1
word2 count2
...

Print the above list in order sorted by word (python will sort punctuation to
come before letters -- that's fine). Store all the words as lowercase,
so 'The' and 'the' count as the same word.

2. For the --topcount flag, implement a print_top(filename) which is similar
to print_words() but which prints just the top 20 most common words sorted
so the most common word is first, then the next most common, and so on.

Use str.split() (no arguments) to split on all whitespace.

Workflow: don't build the whole program at once. Get it to an intermediate
milestone and print your data structure and sys.exit(0).
When that's working, try for the next milestone.

Optional: define a helper function to avoid code duplication inside
print_words() and print_top().

"""

import sys

def print_words(filename):
    wordCount = read_file(filename)
    for key in sorted(wordCount.keys()):
        print "%s %s" % (key, wordCount[key])

def print_top(filename):
    wordCount = read_file(filename)

    # sorts wordCount dictionary into list of tuples based on the count value. 
    # Reverse the list so the max value is at the front of the array after sort.
    sortedWordCount = sorted(wordCount.items(), key=lambda hashTable:hashTable[1], reverse=True)

    for wordCountTuple in sortedWordCount[:20]:
        print "%s %s" % (wordCountTuple[0], wordCountTuple[1])

# +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
# Outputs all keys for the read_file function to test that the function 
# stores file data into a dictionary correctly.
# +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
def test_file_reader(filename):
    wordCount = read_file(filename)
    for key in sorted(wordCount.keys()):
        print key

# +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
# Reads a file and returns a dictionary containing {word : count}
# +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
def read_file(filename):
    wordCount = {}
    file = open(filename, 'r')
    
    # Read in each word of the file, separated by the <space> delimiter.
    # Increment the word counter every time the word appears.
    for line in file:
        words = line.split()
        
        for word in words:
            lower = word.lower() # ex. "Word" == "word"
            
            # initialize the counter if this is the first time the word is 
            # seen.
            if not lower in wordCount :
                wordCount[lower] = 1
            
            # if the word already appears in the dictionary, increment the 
            # word counter.
            else:
                wordCount[lower] += 1
    
    return wordCount


# Define print_words(filename) and print_top(filename) functions.
# You could write a helper utility function that reads a file
# and builds and returns a word/count dict for it.
# Then print_words() and print_top() can just call the utility function.

###

# This basic command line argument parsing code is provided and
# calls the print_words() and print_top() functions which you must define.
def main():
  if len(sys.argv) != 3:
    print 'usage: ./wordcount.py {--count | --topcount} file'
    sys.exit(1)

  option = sys.argv[1]
  filename = sys.argv[2]
  if option == '--count':
    print_words(filename)
  elif option == '--topcount':
    print_top(filename)
  else:
    print 'unknown option: ' + option
    sys.exit(1)

if __name__ == '__main__':
  main()
