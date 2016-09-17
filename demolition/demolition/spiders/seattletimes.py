import copy
import json
import logging
import re
import urllib

import scrapy
from scrapy import loader

from demolition import settings
from demolition import items


NEWSBANKHEADERS = {
    "Host": "infoweb.newsbank.com.ezproxy.spl.org:2048"
}

JSON_REQ_HEADERS = {
    "Accept": "text/javascript, application/javascript, */*"
}

NEWSBANKCOOKIES = {
    "bc_session": "f12eedff-7690-48d1-8d6a-9c3f82f7ba66",
    "bc_username": "bryancwilson",
    "bc_language": "en-US",
    "bc_barcode": "1000010466257",
    "ezproxy": "fCmTiRcjErjLRxU",
    "has_js": "1",
}

log = logging.getLogger(__name__)


class SeattleTimesSpider(scrapy.Spider):
    """
    scrape Seattle Times, Seattle Daily Times online
    at NewsBank.com
    needs credentials from Seattle Public Library
    """
    name = "demolition_seattletimes"
    base_url = "http://infoweb.newsbank.com.ezproxy.spl.org:2048/resources/search/nb?p=AMNEWS&b=results&action=search&t=state%3AWA%21USA%2B-%2BWashington%2Fpubname%3A127D718D1E33F961%7CSTIW%21Multiple%2BPublications&fld0=alltext&bln1=AND&fld1=YMD_date&val1=&sort=_rank_%3AD"
    # query = "&val0=%227500+35TH+AV%22"

    with open('/opt/arthackerasure/data/seattlegov/demolitions.json', 'r') as demos:
        sites = json.load(demos)

    with open('/opt/arthackerasure/subs.json', 'r') as subs:
        address_subs = json.load(subs)


    def _make_address_variants(self, address):
        """ 
        Generate variants of address for permutations of address cardinal 
        directions, street type abbreviations # e.g., SW or S.W., av. or ave.
        or Ave. (is NewsBank search case sensitive?)
        """
        # try each member of the substitution set for a match
        # if a match then make a variant address for all members of the set
        # separate substitution sets for street types and cardinal directions

        # variants = [address,]  # always try to match on the origin adress
        variants = []
        # var_types = ['street_types', 'directions']

        subsST = self.address_subs['street_types']         
        matchesST = [key for key in subsST if key in address]
        for matchST in matchesST:
            for altST in self.address_subs['street_types'][matchST]:
                varST = address.replace(matchST, altST)
                variants.append(varST)

        # now for each variant do the directions var_type
        variants_final = copy.deepcopy(variants)
        for variant in variants:
            subsDI = self.address_subs['directions']  
            matchesDI = [key for key in subsDI if key in variant]
            for matchDI in matchesDI:
                for altDI in self.address_subs['directions'][matchDI]:
                    varDI = variant.replace(matchDI, altDI)
                    variants_final.append(varDI)

        return variants_final

    def start_requests(self):
        requests = []
        for site in self.sites:
            addresses = self._make_address_variants(site['address'])
            for address_variant in addresses:
                try:
                    log.info('\n\n\nqueuing request for {}\n\n\n'.format(address_variant))
                    qry = "&val0=%22{0}%22".format(address_variant)                    
                    req = scrapy.Request(url=self.base_url+qry,
                                        headers=NEWSBANKHEADERS,
                                        cookies=NEWSBANKCOOKIES,
                                        meta={"address": site['address'],
                                              "lat": site['location']['latitude'],
                                              "lon": site['location']['longitude'],
                                              "address_variant": address_variant 
                                        })
                    requests.append(req)

                except KeyError:
                    log.info('no lat/lon for site:{}'.format(site['address']))
                    continue

        return requests

    def parse(self, response):
        """
        do something with the response
        """

        i = loader.ItemLoader(item=items.DemolitionItem(), response=response)
        i.replace_xpath('text', '//div[@class="preview"]//text()')
        i.replace_value('address', response.meta["address"])
        # i.add_value('address_variant', response.meta["address_variant"])
        i.replace_value('lat', response.meta["lat"])
        i.replace_value('lon', response.meta["lon"])
        # if '701 N' in response.meta["address"]:
        #     import pdb; pdb.set_trace()
        item = i.load_item()
        item['image_url'] = []

        snippets = i.get_xpath("//div[@class='snippet']/text()") 
        if len(snippets):
            # import pdb; pdb.set_trace()
            snip_meta = {
                'item': item,
                'snippets': snippets,
                'search_response': response
            }
            snip_req = self.get_snippet_req(response, snippets[0], snip_meta)  # call the first of chained snippet requests
            
            return snip_req
        else:
            self.write_item_to_json(item)
                
    def get_snippet_req(self, response, snip_id, meta):
        """
        snippet images (small preview images of print newspaper scans)
        are loaded via XHR and not available in the response but can be gotten 
        with subrequests
        """
        base_url = "http://infoweb.newsbank.com.ezproxy.spl.org:2048/resources/SiteLinks/xmlquery/snippets/getsnippets.jsonp?rem=platform_v1_drupal&dbmode=imggroupid&jsonp=jsonp1474097742990&"
        # beyond base_url, need userid (ip address), snippet
        # snippet is from text() content of the div.snippet
        try:
            # import pdb; pdb.set_trace()
            userid = re.search(r"var snippet_userid='(.*)'", response.body).group(1)
            qry = "userid={}&{}&searchterms={}".format(userid, snip_id, urllib.quote_plus(response.meta["address_variant"]))
            HEADERS = copy.deepcopy(NEWSBANKHEADERS)
            HEADERS.update(JSON_REQ_HEADERS)
            snip_req = scrapy.Request(url=base_url+qry,
                                       headers=HEADERS,
                                       cookies=NEWSBANKCOOKIES,
                                       callback=self.parse_snippet_xhr,
                                       meta=meta
                                       )
            return snip_req
        except AttributeError:
            # import pdb; pdb.set_trace()
            return 
        
    def parse_snippet_xhr(self, response):
        """ update the item and chain the next snippet request if
            necessary
        """
        # import pdb; pdb.set_trace()
        item = response.meta['item']
        snippets = response.meta['snippets']
        gif_url = "http"+re.search(r'http(.*)\.gif"', response.body).group(1)+".gif"
        item['image_url'].append(gif_url)
        snippets.pop(0)
        if len(response.meta['snippets']):
            resp = response.meta['search_response']
            snip_req = self.get_snippet_req(resp, snippets[0], response.meta)  # call the first of chained snippet requests
            if snip_req:
                snip_req.meta['item'] = item
                snip_req.meta['snippets'] = snippets
                return snip_req
            else:
                self.write_item_to_json()
        else:
            # we're done!
            self.write_item_to_json(item)

    def write_item_to_json(self, item):
        if item.get('text', None) or item.get('image_url', None):
            # import pdb; pdb.set_trace()
            fn = '/opt/arthackerasure/data/out/{}'.format(settings.SPIDERS_OUTPUT_FILES[self.name])
            save_item = {item["address"][0]:dict(item)}
            with open(fn, 'w') as f:
                f.write(json.dumps(save_item))
        else:
            log.info('nothing found in Seattle Times for {}'.format(item['address']))
