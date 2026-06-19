"""
Gets director and cast from Wikipedia
Free - No API key - Works in India!
Auto saves to database after first fetch
"""
import re
import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

def clean_text(text):
    """Remove citations [1] and extra spaces"""
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = ' '.join(text.split())
    return text.strip()

def get_cast_and_director(movie_title, release_year=None):
    """
    Fetches director and cast from Wikipedia
    Returns (director_string, cast_string)
    Example: ('Christopher Nolan', 'Leonardo DiCaprio, Joseph Gordon-Levitt')
    """
    try:
        # Step 1 - Search Wikipedia
        if release_year:
            query = '{} {} film'.format(movie_title, release_year)
        else:
            query = '{} film'.format(movie_title)

        search_resp = requests.get(
            'https://en.wikipedia.org/w/api.php',
            params={
                'action':   'query',
                'list':     'search',
                'srsearch': query,
                'format':   'json',
                'srlimit':  '5',
            },
            headers=HEADERS,
            timeout=8
        )

        results = search_resp.json().get('query', {}).get('search', [])
        if not results:
            return '', ''

        # Step 2 - Try each result until we find film infobox
        for result in results[:3]:
            page_title = result['title']

            # Skip non-film pages
            skip_words = ['soundtrack', 'album', 'song', 'novel', 'book', 'series']
            if any(w in page_title.lower() for w in skip_words):
                continue

            # Get page HTML
            page_resp = requests.get(
                'https://en.wikipedia.org/wiki/{}'.format(
                    page_title.replace(' ', '_')
                ),
                headers=HEADERS,
                timeout=8
            )

            director, cast = parse_infobox(page_resp.text)

            if director or cast:
                return director, cast

        return '', ''

    except Exception as e:
        print('Wikipedia error for "{}": {}'.format(movie_title, e))
        return '', ''


def parse_infobox(html):
    """Parse director and cast from Wikipedia infobox"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Find infobox table
        infobox = (
            soup.find('table', class_='infobox vevent') or
            soup.find('table', class_='infobox')
        )

        if not infobox:
            return '', ''

        director  = ''
        cast_list = []

        for row in infobox.find_all('tr'):
            header = row.find('th')
            data   = row.find('td')

            if not header or not data:
                continue

            header_text = header.get_text().strip().lower()

            # Get Director
            if 'directed' in header_text or header_text == 'director':
                names = []
                # Try list items first
                items = data.find_all('li')
                if items:
                    for item in items[:3]:
                        n = clean_text(item.get_text())
                        if n:
                            names.append(n)
                else:
                    # Get links (director names are usually linked)
                    links = data.find_all('a')
                    if links:
                        for link in links[:3]:
                            n = clean_text(link.get_text())
                            if n and len(n) > 2:
                                names.append(n)
                    else:
                        n = clean_text(data.get_text())
                        if n:
                            names.append(n)
                director = ', '.join(names)

            # Get Cast/Starring
            if 'starring' in header_text or 'cast' in header_text:
                items = data.find_all('li')
                if items:
                    for item in items[:8]:
                        n = clean_text(item.get_text())
                        if n and len(n) > 1:
                            cast_list.append(n)
                else:
                    links = data.find_all('a')
                    if links:
                        for link in links[:8]:
                            n = clean_text(link.get_text())
                            if n and len(n) > 2:
                                cast_list.append(n)
                    else:
                        raw = clean_text(data.get_text())
                        if raw:
                            for name in raw.split('\n'):
                                name = name.strip()
                                if name and len(name) > 1:
                                    cast_list.append(name)
                            cast_list = cast_list[:8]

        cast = ', '.join(cast_list)
        return director, cast

    except Exception as e:
        print('Parse error:', e)
        return '', ''