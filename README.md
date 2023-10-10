# xbars-py
Currently scrapes Wiktionary to return dictionary entries, and stores data regarding parts of speech and verb inflections. The goal is to ultimately use this data to produce an automatic syntax tree generator.

Currently, there is one main module:
* dictsearch.py

## Requirements
This project was tested and developed on Python 3.10.2. The following libraries must be installed:
* [Beautiful Soup 4](https://beautiful-soup-4.readthedocs.io/en/latest/) - used by the scraper in `dictsearch.py`
* *(tentative)* [Natural Language Toolkit (NTLK)](https://www.nltk.org/install.html) - used by `psr.py` and `parser.py`.

Unfortunately, I can't make any promises regarding which versions of Python 3.x this project targets.
*(tentative):* I haven't tested thoroughly on Python 3.7, but it is the minimum Python version supported by NTLK.

## Modules
### `dictsearch.py` - a basic Wiktionary scraper
Aims to provide an extremely basic interface to scrape English language dictionary entries from Wiktionary.

The class constructor automatically does the scraping in the background, so the interface consists solely of the constructor and a few instance variables. As such, you'll want to make a new instance of the class when you want to search a new word, instead of modifying the instance variables.

#### Interface
##### `DictSearch(word)`
Searches for `word` on Wiktionary, scrapes the data if an English entry exists, and stores a dictionary entry and part of speech and verb inflection data.
* If a page for `word` does not exist on Wiktionary, a `PageNotFound` exception is raised.
* If a page for `word` exists, but an English entry for it does not exist, a `NoEnglishEntry` exception is raised.
##### `DictSearch.POSList`
* `set` class attribute that holds the parts of speech relevant for forming syntax trees. If a word has a part of speech that does not belong to `DictSearch.POSList` but is included in `DictSearch._POSList`, `.entry` will include the definition, but this library does not intend to automatically generate phrase structure rules for `DictSearch` instances with an empty `.POS`.
##### `.word`
* `str` instance variable that holds the word used to initialize this instance.
##### `.entry`
* `str` instance variable that holds the dictionary entry on Wiktionary for the word.
##### `.POS`
* `set` instance variable that holds the parts of speech associated with `.word` in English.
##### `.isAux` *=False*
* `bool` instance variable that is `True` if `.word` is an auxiliary/modal verb and is `False` otherwise.
##### `.isPlural` *=False*
* `bool` instance variable that is `True` if `.word` is a plural noun and is `False` otherwise.
##### `.verbRoot` *=""*
* `str` instance variable that holds the root form of `.word` if it is a verb inflected for tense/aspect and is `False` otherwise.
##### `.nounRoot` *=""*
* `str` instance variable that holds the root form of `.word` if it is a noun inflected for plurality and is `False` otherwise.
##### `.verbInflections` *=set()*
* `set` instance variable that holds any verb inflections associated with `.word` in English and is an empty `set` if `.word` is not an inflected verb.
  
---

### `psr.py` - [WORK IN PROGRESS]
*(tentative):* Holds the phrase structure rules later imported by `parser.py`. This module expands the functionality offered by NTLK's implementation of context-free grammars in `nltk.grammar.CFG` to demonstrate phrasal and head movement.

My implementation may be hacky, and from a (computational) linguistics perspective, there's a number of potential complaints about my implementation. For one, I violate the recursive spirit of Chomsky's generative syntax approach by defining multiple specialized phrase structure rules for, say, subject DPs/TPs/CP. Second of all, to the best of my knowledge, CFGs are unable to account for phrasal/head movement and subject/object control structures, so there may be fundamental concerns with using CFGs in the first place here. Unfortunately, due to the limits of my theoretical knowledge, this is a case of the ends taking precedence over the means.

---

### `parser.py` - [WORK IN PROGRESS]
Given a target configuration, aims to output potential parse trees for an input phrase/sentence.

#### Restrictions - [WORK IN PROGRESS]
I'm wondering if it'll be possible to show raising/control structures if I have a list of words that trigger this behavior; until I manage to actually get the basic functionality working, I simply can't really say if this'll end up being the case or not.
