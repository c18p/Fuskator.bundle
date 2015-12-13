NAME   = 'Fuskator'
PREFIX = '/photos/fuskator'

ICON = "icon-default.png"

URL_BASE = "http://fuskator.com"

DEFAULT_CACHE_TIME = CACHE_1MONTH

SORT = [None, 'quality', 'rating', 'tags']

POPULAR_TAGS = ['2 girls', 'anal', 'asian', 'babe', 'blonde', 'blowjob', 'brunette', 'bukkake',
        'busty', 'cum', 'ebony', 'facial', 'hardcore', 'interracial', 'japanese', 
        'lesbians, -solo', 'MILF', 'petite', 'redhead', 'schoolgirl', 'shaved', 'small_tits',
        'solo', 'stockings', 'teen']
####################################################################################################
def Start():

    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
    Plugin.AddViewGroup("Pictures", viewMode="Pictures", mediaType="photos")

    ObjectContainer.title1 = NAME
    ObjectContainer.view_group = "List"

    HTTP.CacheTime  = DEFAULT_CACHE_TIME
    HTTP.User_Agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36'

    if 'search_history' not in Dict:
        Dict['search_history'] = []
        Dict.Save()      
    if 'query_thumbs' not in Dict:
        Dict['query_thumbs'] = {}
        Dict.Save()

@handler(PREFIX, NAME, ICON)
def MainMenu():       

    oc = ObjectContainer(no_cache=True)

    oc.add(DirectoryObject(
        key   = Callback(ListGalleries, cache=CACHE_1HOUR),
        title = u'%s' % L('latest')
    ))
    oc.add(DirectoryObject(
        key   = Callback(Tags),
        title = u'%s' % L('popular_tags')
    ))
    oc.add(DirectoryObject(
        key   = Callback(ListImages, url=String.Quote("http://fuskator.com/thumbs/random/"), cache=0),
        title = u'%s' % L('random_gallery'),
    ))
    oc.add(InputDirectoryObject(
        key   = Callback(OrderBy),
        title = u'%s' % L('search'),
    ))
    if Dict['search_history']:
        oc.add(DirectoryObject(
            key   = Callback(SearchHistory),
            title = u'%s' % L('search_history'),
        ))
        oc.add(DirectoryObject(
            key   = Callback(SearchHistoryClear),
            title = u'%s' % L('clear_search_history'),
        ))

    oc.add(PrefsObject(
        title = L('preferences'),
    ))

    return oc

####################################################################################################
# Search History
####################################################################################################
@route(PREFIX + '/searchhistory')
def SearchHistory():

    oc = ObjectContainer()

    for item in Dict['search_history']:
        oc.add(DirectoryObject(
            key   = Callback(OrderBy, query=item),
            title = u'%s' % item,
            thumb = Resource.ContentsOfURLWithFallback(Dict['query_thumbs'][item], fallback=R(ICON)) if item in Dict['query_thumbs'] else R(ICON),
        ))

    return oc

@route(PREFIX + '/searchhistoryclear')
def SearchHistoryClear():

    Dict['search_history'] = []
    Dict.Save()
    return ObjectContainer()

####################################################################################################
# Listings
####################################################################################################
@route(PREFIX + '/tags')
def Tags():

    oc = ObjectContainer()

    for item in sorted(POPULAR_TAGS):
        oc.add(DirectoryObject(
            key   = Callback(OrderBy, query=item),
            title = item,
            thumb = Resource.ContentsOfURLWithFallback(Dict['query_thumbs'][item], fallback=R(ICON)) if item in Dict['query_thumbs'] else R(ICON),
        ))

    return oc

@route(PREFIX + '/orderby')
def OrderBy(query='-'):

    oc = ObjectContainer()

    for item in SORT:
        oc.add(DirectoryObject(
            key   = Callback(ListGalleries, query=query, order=item),
            title = u'%s' % L(item) if item else u'%s' % L('none'),
        ))

    return oc

@route(PREFIX + '/list', page=int, cache=int)
def ListGalleries(page=1, query="-", order=None, cache=DEFAULT_CACHE_TIME):

    oc = ObjectContainer()

    if query != '-' and query not in Dict['search_history']:
        Dict['search_history'].insert(0, query)
        Dict.Save()

    search_query = " ".join(["\"%s\"" % x.strip().replace(" ", "_") for x in query.split(',')]) if query != '-' else '-'

    url = "%s/page/%d/" % (URL_BASE, page)
    if query:
        url += "%s/" % String.Quote(search_query, usePlus=True)
    if order:
        url += "%s/" % order

    Log("FUSKATOR: " + url)

    data = HTML.ElementFromURL(url, cacheTime=cache)

    items = data.xpath("//div[@class='thumblinks']/div[@class='pic']")
    stats_pattern = Regex(r"([\d]+) pics \/ ([\d]+) hits")
    for item in items:
        try:
            item_url    = URL_BASE + item.xpath("div[@class='gallery_data'][2]/a/@href")[0]
            item_thumb  = URL_BASE + item.xpath("div[@class='pic_pad']/a/img/@src")[0]
            item_stats  = item.xpath("div[@class='gallery_data'][1]/text()")[0]
            item_pics   = stats_pattern.search(item_stats).group(1)
            item_hits   = stats_pattern.search(item_stats).group(2)
            item_name   = " ".join(item.xpath("div[@class='pic_pad']/a/img/@alt")[0].split(' ')[:2])
            item_rating = item.xpath("div[@class='pic_rating']/text()")[0][-9:].split('/')[0].strip()

            if query not in Dict['query_thumbs']:
                Dict['query_thumbs'][query] = item_thumb
                Dict.Save()

            oc.add(PhotoAlbumObject(
                rating_key = item_name,
                key   = Callback(ListImages, url=String.Quote(item_url)),
                title = u'%s - %s - %s' % (item_rating, item_name, item_stats),
                summary = u'%s' % (item_hits),
                thumb = Resource.ContentsOfURLWithFallback(item_thumb),
            ))
        except:
            continue
    #if order != 'rating':
    if Prefs['sort_pages'] == "rating":
        oc.objects.sort(key=lambda obj: obj.title, reverse=True)
    elif Prefs['sort_pages'] == "hits":
        oc.objects.sort(key=lambda obj: int(obj.summary), reverse=True)

    if len(oc) >= 52:
        oc.add(NextPageObject(
            key = Callback(ListGalleries, page=page+1, query=query, order=order, cache=cache),
            title = u'%s' % L('more'),
        )) 

    return oc

@route(PREFIX + '/list/images', cache=int)
def ListImages(url, cache=DEFAULT_CACHE_TIME):

    oc = ObjectContainer(view_group='Pictures')

    page = HTML.ElementFromURL(String.Unquote(url), cacheTime=cache)

    img_base_url = page.xpath("//div[@class='thumblinks']/script/text()")[0]
    pattern = Regex(r"unescape\(\'([^\']*)\'\)")
    img_base_url = "http:%s" % String.Unquote(pattern.search(img_base_url).group(1))

    file_pattern = Regex(r"[^\.]*-([\d]*\.[^\.]*)")

    images = page.xpath("//div[@class='thumblinks']/div[@class='wrapper']/div[@class='pic']/a/img")
    for img in images:
        img_thumb = URL_BASE + img.get("src")
        img_file  = file_pattern.search(img_thumb).group(1)
        img_path  = img_base_url + img_file

        oc.add(PhotoObject(
            title = u'%s' % img_file,
            url   = img_path,
            thumb = Resource.ContentsOfURLWithFallback(img_thumb),
        ))

    return oc