import requests
import urllib

s = "http://nl.wikipedia.org/wiki/Speciaal:Willekeurig"

def random_wiki_text():
    try:
        url = urllib.request.urlopen(s,timeout=1.5).geturl()
    
        name = url.rsplit("/",1)[1]
        return wiki_text(name)
    
    except:
        return ""

def wiki_text_exact(name):
    try:
        response = requests.get(
            'https://nl.wikipedia.org/w/api.php',
            params={
                'action': 'query',
                'format': 'json',
                'titles': name,
                'prop': 'extracts',
                'exintro': True,
                'explaintext': True,
            },
            timeout=1.5).json()

        text = next(iter(response['query']['pages'].values()))['extract']
        return text
    
    except:
        return ""

def wiki_text(name):
    try:
        response = requests.get(
            'https://nl.wikipedia.org/w/api.php',
            params={
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': name,
                'srlimit': 3
            },
            timeout=1.5).json()
    except:
        return ""
    try:
        s = response['query']['search'][0]['title']
    except:
        return ""
    s = wiki_text_exact(s)
    return s
