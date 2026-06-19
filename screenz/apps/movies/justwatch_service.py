"""
Gets streaming platform availability for movies in India
Uses JustWatch website scraping - free, no API key needed
"""
import requests
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
}

def get_platforms_for_movie(title, year=None):
    """
    Returns list of platforms where movie is available in India
    Example: [{'name': 'Netflix', 'slug': 'netflix', 'url': '...'}]
    """
    try:
        # Search JustWatch for movie
        search_url = 'https://apis.justwatch.com/contentpartner/v2/content/offers/locale/en_IN'

        # Try GraphQL API
        graphql_url = 'https://apis.justwatch.com/graphql'

        query = '''
        query GetSearchTitles($searchQuery: String!) {
          popularTitles(
            country: IN
            filter: { searchQuery: $searchQuery }
            first: 3
          ) {
            edges {
              node {
                id
                content(country: IN, language: "en") {
                  title
                  originalReleaseYear
                }
                offers(country: IN, platform: WEB) {
                  monetizationType
                  standardWebURL
                  package {
                    id
                    packageId
                    clearName
                    technicalName
                  }
                }
              }
            }
          }
        }
        '''

        response = requests.post(
            graphql_url,
            json={
                'query': query,
                'variables': {'searchQuery': title}
            },
            headers={
                'User-Agent': HEADERS['User-Agent'],
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            timeout=10
        )

        if response.status_code != 200:
            return []

        data = response.json()
        edges = data.get('data', {}).get('popularTitles', {}).get('edges', [])

        if not edges:
            return []

        # Find best matching movie
        target = edges[0]['node']

        # If year provided find better match
        if year:
            for edge in edges:
                node = edge['node']
                node_year = node.get('content', {}).get('originalReleaseYear')
                if node_year and abs(int(node_year) - int(year)) <= 1:
                    target = node
                    break

        # Get platforms from offers
        offers = target.get('offers', [])
        platforms = []
        seen_slugs = []

        # Platform name to slug mapping
        slug_map = {
            'netflix':          'netflix',
            'amazon prime':     'prime',
            'prime video':      'prime',
            'amazon':           'prime',
            'jiocinema':        'jio',
            'jio cinema':       'jio',
            'hotstar':          'hotstar',
            'disney':           'hotstar',
            'disney+ hotstar':  'hotstar',
            'apple tv':         'apple',
            'apple tv+':        'apple',
            'zee5':             'zee5',
            'sonyliv':          'sonyliv',
            'sony liv':         'sonyliv',
            'mubi':             'other',
            'curiosity stream': 'other',
        }

        for offer in offers:
            package   = offer.get('package', {})
            name      = package.get('clearName', '')
            tech_name = package.get('technicalName', '').lower()
            url       = offer.get('standardWebURL', '')

            if not name:
                continue

            # Find slug
            slug = 'other'
            name_lower = name.lower()
            for key, val in slug_map.items():
                if key in name_lower or key in tech_name:
                    slug = val
                    break

            # Skip duplicates and 'other'
            if slug in seen_slugs:
                continue
            if slug == 'other':
                continue

            seen_slugs.append(slug)
            platforms.append({
                'name': name,
                'slug': slug,
                'url':  url or get_platform_url(slug, title),
            })

        return platforms

    except Exception as e:
        print('JustWatch error for {}: {}'.format(title, e))
        return []


def get_platform_url(slug, title):
    """Fallback search URLs for each platform"""
    from urllib.parse import quote
    t = quote(title)
    urls = {
        'netflix':  'https://www.netflix.com/search?q=' + t,
        'prime':    'https://www.primevideo.com/search/ref=atv_nb_sr?phrase=' + t,
        'jio':      'https://www.jiocinema.com/search/' + t,
        'hotstar':  'https://www.hotstar.com/in/search?q=' + t,
        'apple':    'https://tv.apple.com/search?term=' + t,
        'zee5':     'https://www.zee5.com/search?q=' + t,
        'sonyliv':  'https://www.sonyliv.com/search?keyword=' + t,
    }
    return urls.get(slug, '#')


    