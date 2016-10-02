import copy
import logging
import json
from StringIO import StringIO
from io import open as iopen

try:
    import Image
except ImportError:
    from PIL import Image

import requests
import pytesseract


NEWSBANKHEADERS = {
    "Host": "infoweb.newsbank.com.ezproxy.spl.org:2048",
}

NEWSBANKCOOKIES = {
    "bc_session": "f12eedff-7690-48d1-8d6a-9c3f82f7ba66",
    "bc_username": "bryancwilson",
    "bc_language": "en-US",
    "bc_barcode": "1000010466257",
    "ezproxy": "fCmTiRcjErjLRxU",
    "has_js": "0",
}


def process_json():
    fn = "/opt/arthackerasure/data/out/seatimes.partial.json"
    with open(fn, 'r') as f:       
        addrs = json.load(f)

    outfn = "/opt/arthackerasure/data/out/filtered.seatimes.json"
    ocredfn = "/opt/arthackerasure/data/out/ocred_urls"


    with open(ocredfn, 'a+') as ocred:
        ocred_urls = ocred.read().replace('\n', ' ')

        seen = []
        for key, addr in addrs.iteritems():
            # e.g., {"7555 25TH AVE NE": {"lat": ["47.68469649"], "lon": ["-122.3010748"], "image_url": ["http://IHW07.newsbank.com/cache//snippet/66.212.65.215/sn_0_12D1F46DA509D7901048608417486264.gif", "http://imagefarm.newsbank.com/imageserver?REM=platform_v1_drupal&OPERATION=GetImageUrl&SEARCH_TERMS=7555%2025TH%20ave%20n.E&USER_ID=66.212.65.215&snippet=ARHB|FULLSIZE|12D576C7601C8C87|release_0474|12D618EC02997760\",\"id_12D618EC02997760\":\"http://IHW03.newsbank.com/cache//snippet/66.212.65.215/sn_0_12D618EC0299776017382102438390.gif", "http://imagefarm.newsbank.com/imageserver?REM=platform_v1_drupal&OPERATION=GetImageUrl&SEARCH_TERMS=7555%2025TH%20ave%20n.E&USER_ID=66.212.65.215&snippet=ARHB|FULLSIZE|12D576C848D59174|release_0474|12D618B961C854A8\",\"id_12D618B961C854A8\":\"http://IHW01.newsbank.com/cache//snippet/66.212.65.215/sn_0_12D618B961C854A817066562406836.gif", "http://IHW03.newsbank.com/cache//snippet/66.212.65.215/sn_0_12D619134B2CF64017024882402668.gif"], "news_date": [" August 2, 1968", " May 26, 1970", " May 28, 1970", " May 29, 1970"], "address": ["7555 25TH AVE NE"]}},
            # skip dupes
            if key in seen:
                continue

            addr_num = key.split(' ')[0]

            # download the images
            for i, url in enumerate(addr['image_url']):
                print('testing image at url: {}\n'.format(url))    
                if not url.startswith("http://IHW") or url in ocred_urls:
                    # not a real image
                    print('{} already OCRed'.format(url))
                    continue

                resp = requests.get(url, headers=NEWSBANKHEADERS, cookies=NEWSBANKCOOKIES)  # NEWSBANK headers/cookies not needed for images
                if resp.status_code == requests.codes.ok:
                    # ocr it for the house number of the address
                    print('OCRing image at {}\n'.format(url))
                    try:
                        img = Image.open(StringIO(resp.content))
                    except IOError:
                        continue
                    imgtext = pytesseract.image_to_string(img).decode('ascii', 'ignore')
                    if addr_num in imgtext:
                        ocred.write(" "+url+" ")
                        print("found {} in {}!\n".format(addr_num, imgtext))
                        # if it is found, write to new JSON file                        
                        addr_to_write = copy.deepcopy(addr)
                        addr_to_write['image_url'] = url
                        addr_to_write['news_date'] = addr['news_date'][i]
                        dtowrite = {key:addr_to_write}
                        with open(outfn, 'a') as outf:
                            outf.write(json.dumps(dtowrite) + ", \n\n")  # this JSON will have to be cleaned up
                        # ... and save the image
                        fn = url.split('/')[-1:][0]
                        with iopen('/opt/arthackerasure/data/out/img/'+fn, 'wb') as outfile:
                            outfile.write(resp.content)
                    else:
                        ocred.write(" "+url+" ")
            
                seen.append(key)


if __name__ == '__main__':
    process_json()
