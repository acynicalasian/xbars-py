import urllib.request
import urllib.parse
import json
import re
from bs4 import BeautifulSoup

class PageNotFound(Exception):
    pass
class NoEnglishEntry(Exception):
    pass

class DictSearch:
    """
    Given a search term, fetch JSON output from the MediaWiki API to determine whether a page exists
    for the search term. If so, copy the HTML data of the page for that term, and parse it to
    extract parts of speech, definitions, etc.
    """
    POSList = [ "Adjective", "Adverb", "Article", "Conjunction", "Determiner", "Pronoun",
                 "Proper noun", "Noun", "Preposition", "Verb" ]
    _POSList = POSList + [ "Letter", "Number", "Symbol", "Interjection" ]
    _aux_regex = re.compile(
        r"(?P<pp>\bauxiliary\b)?(?(pp)|\bmodal\b)" )
    _past_regex = re.compile(
        r"(([Ss]imple )?[Pp]ast (?P<pp>tense )?(?(pp)|(indicative )?))of (?P<root>\w+)" )
    _perf_regex = re.compile(
        r"[Pp]ast participle of (?P<root>\w+)" )
    _pres_regex = re.compile(
        r"[Ss]imple present (indicative )?of (?P<root>\w+)" )
    _con_regex = re.compile(
        r"(?P<pp>[Pp]resent participle )?(and )?(?(pp).*|[Gg]erund )of (?P<root>\w+)" )
    _plur_regex = re.compile(
        r"[Pp]lural of (?P<root>\w+)" )
    
    def __init__(self, word):
        # "Public" data members
        self.word = word
        self.entry = "" # hold dictionary entry
        self.POS = set() # hold parts of speech of word relevant for syntax trees
        self.isAux = False
        self.isPlural = False
        self.verbRoot = ""
        self.nounRoot = ""
        self.verbInflections = set() # should be empty if not a verb

        # "Private" data members
        self._soup = None
        self._html = None # hold HTML data of body of page

        if not isinstance(word, str):
            raise TypeError("Search term must be of type str")
        self._copypage(word) # instantiate self._html

        # Only runs if page exists
        self._soup = BeautifulSoup(self._html, "html.parser")
        self._parsepage()
        
    def _copypage(self, word):
        URL = "https://en.wiktionary.org/w/api.php?"
        param = {
            "action" : "parse",
            "page" : word,
            "prop" : "text",
            "format" : "json"
            }
        URL += urllib.parse.urlencode(param)
        raw = json.load(urllib.request.urlopen(URL))
        # If page does not exist
        if "error" in raw:
            raise PageNotFound("The page you specified ('" + word + "') doesn't exist")
        self._html = raw["parse"]["text"]["*"]

    def _parsepage(self):
        soup = self._soup
        treeptr = soup.find(id="English")
        if not treeptr:
            raise NoEnglishEntry("English entry does not exist for '" + self.word + "'")
        
        # Strip the HTML of the [quotations] and [synonyms] toggle boxes, [edit] buttons, reference
        # links, NavFrames (tables or something), empty <li> tags (for later in extracting
        # definitions), and maintenance notes
        for classid in [ "nyms-toggle", "HQToggle", "mw-editsection", "reference", "NavFrame",
                         "mw-empty-elt", "maintenance-line" ]: 
            for tag in soup.find_all(class_=classid):
                tag.decompose()

        # Remove <dl> tags (example usages) and <ul> tags (show up when clicking the [quotations]
        # button)
        for tagid in ["dl", "ul"]:
            for tag in soup.find_all(tagid):
                tag.decompose()

        # Section headers for etymology and part of speech all occur in tags with class
        # "mw-headline"
        treeptr = treeptr.find_next(class_="mw-headline")
        etym_regex = re.compile("Etymology")
        entry = ""
        # First condition exits if treeptr is None, second exits if we enter a section for a
        # different language, which always occurs in "h2" tags
        while treeptr and treeptr.parent.name != "h2":
            if etym_regex.match(treeptr.string):
                if (entry != "" and len(entry) >= 2 and entry[len(entry)-2:] != "\n\n"):
                    if entry[len(entry)-1] == '\n':
                        entry += '\n'
                    else:
                        entry += "\n\n"
                entry += treeptr.string + "\n"
                # <p> tags contain the etymology deets, but a gloss isn't guaranteed to occur; check
                # if the next <p> occurs before or after the next tag with class "mw-headline"
                nexthead = treeptr.find_next(class_="mw-headline")
                if (treeptr.find_next("p") not in nexthead.next_elements):
                    treeptr = treeptr.find_next("p")
                    entry += treeptr.get_text()
            elif treeptr.string in DictSearch._POSList:
                if (entry != "" and len(entry) >= 2 and entry[len(entry)-2:] != "\n\n"):
                    if entry[len(entry)-1] == '\n':
                        entry += '\n'
                    else:
                        entry += "\n\n"
                if treeptr.string in DictSearch.POSList:
                    self.POS.add(treeptr.string)
                entry += treeptr.string + '\n'
                # Handle verbs seperately, comb definitions for mentions of being auxiliaries
                verbFlag = True if treeptr.string == "Verb" else False
                nounFlag = True if treeptr.string == "Noun" else False
                # Extract the gloss
                treeptr = treeptr.find_next("p")
                entry += treeptr.get_text() + '\n'
                # Extract the section containing definitions
                olptr = treeptr.find_next("ol").extract()
                olptr = olptr.li
                liCount = 1
                nestedCount = 1
                innerptr = None
                while olptr:
                    if olptr.ol: # if there's a nested definition
                        innerptr = olptr.ol.extract()
                    # Wiktionary's formatting is inconsistent enough where I need to make sure <li>
                    # tags get a newspace in between them if one wasn't already written
                    if entry != "" and entry[len(entry)-1] != '\n':
                        entry += '\n'
                    text = str(liCount) + '. ' + olptr.get_text()
                    if text[len(text)-2:] == "\n\n":
                        text = text[:len(text)-1]
                    entry += text
                    if verbFlag:
                        m_aux_regex = DictSearch._aux_regex.search(text)
                        m_past_regex = DictSearch._past_regex.search(text)
                        m_perf_regex = DictSearch._perf_regex.search(text)
                        m_pres_regex = DictSearch._pres_regex.search(text)
                        m_con_regex = DictSearch._con_regex.search(text)
                        if m_aux_regex and self.word not in [ "modalize", "modalise" ]: # edge case
                            self.isAux = True
                        if m_past_regex:
                            self.verbInflections.add("past")
                            self.verbRoot = m_past_regex.group("root")
                        if m_perf_regex:
                            self.verbInflections.add("perfect")
                            self.verbRoot = m_perf_regex.group("root")
                        if m_pres_regex:
                            self.verbInflections.add("present")
                            self.verbRoot = m_pres_regex.group("root")
                        if m_con_regex:
                            self.verbInflections.add("continuous")
                            self.verbRoot = m_con_regex.group("root")
                    if nounFlag:
                        m_plur_regex = DictSearch._plur_regex.search(text)
                        if m_plur_regex:
                            self.isPlural = True
                            self.nounRoot = m_plur_regex.group("root")
                    if innerptr:
                        innerptr = innerptr.li
                        while innerptr:
                            if (entry != "" and entry[len(entry)-1] != '\n'):
                                entry += '\n'
                            text = ('\t' + str(nestedCount) + '. ' + innerptr.get_text())
                            if text[len(text)-2:] == "\n\n":
                                text = text[:len(text)-1]
                            entry += text
                            if verbFlag:
                                m_aux_regex = DictSearch._aux_regex.search(text)
                                m_past_regex = DictSearch._past_regex.search(text)
                                m_perf_regex = DictSearch._perf_regex.search(text)
                                m_pres_regex = DictSearch._pres_regex.search(text)
                                m_con_regex = DictSearch._con_regex.search(text)
                                if m_aux_regex and self.word not in [ "modalize", "modalise" ]:
                                    self.isAux = True
                                if m_past_regex:
                                    self.verbInflections.add("past")
                                    self.verbRoot = m_past_regex.group("root")
                                if m_perf_regex:
                                    self.verbInflections.add("perfect")
                                    self.verbRoot = m_perf_regex.group("root")
                                if m_pres_regex:
                                    self.verbInflections.add("present")
                                    self.verbRoot = m_pres_regex.group("root")
                                if m_con_regex:
                                    self.verbInflections.add("continuous")
                                    self.verbRoot = m_con_regex.group("root")
                            if nounFlag:
                                m_plur_regex = DictSearch._plur_regex.search(text)
                                if m_plur_regex:
                                    self.isPlural = True
                                    self.nounRoot = m_plur_regex.group("root")
                            nestedCount += 1
                            innerptr = innerptr.find_next("li")
                        nestedCount = 1
                        innerptr= None
                    liCount += 1
                    olptr = olptr.find_next("li")
            # tag with class "mw-headline" that doesn't correspond with etymology or definitions
            else:
                pass
            treeptr = treeptr.find_next(class_="mw-headline")
        self.entry = entry
