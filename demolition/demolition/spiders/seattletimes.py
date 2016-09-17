import json

import scrapy

from . import settings


NEWSBANKHEADERS = {
    "Cookie": "bc_session=f12eedff-7690-48d1-8d6a-9c3f82f7ba66; bc_username=bryancwilson; bc_language=en-US; bc_barcode=1000010466257; _ga=GA1.2.1610034180.1473810739; ezproxy=aAhmedZjkctSiYm; has_js=1",
    "Host": "infoweb.newsbank.com.ezproxy.spl.org:2048"
}


class SeattleTimesSpider(scrapy.Spider):
    """
    scrape Seattle Times, Seattle Daily Times online
    at NewsBank.com
    needs credentials from Seattle Public Library
    """
    name = "demolition_seattletimes"
    base_url = "http://infoweb.newsbank.com.ezproxy.spl.org:2048/resources/search/nb?p=AMNEWS&b=results&action=search&t=state%3AWA%21USA%2B-%2BWashington%2Fpubname%3A127D718D1E33F961%7CSTIW%21Multiple%2BPublications&fld0=alltext&bln1=AND&fld1=YMD_date&val1=&sort=_rank_%3AD"
    query = "&val0=%227500+35TH+AV%22"
    with open('/opt/arthackerasure/data/seattlegov/demolitions.json', 'r') as demos:
        sites = json.load(demos)

    def _make_address_variants(self, address):
        """ 
        Generate variants of address for permutations of address cardinal 
        directions, street type abbreviations # e.g., SW or S.W., av. or ave.
        or Ave. (is NewsBank search case sensitive?)
        """
        return [address]

    def start_requests(self):
        requests = []
        for site in self.sites:
            # search 
            addresses = self._make_address_variants(site['address'])
            for address_variant in addresses:                
                qry = "&val0=%22{0}%22".format(address_variant)
                req = scrapy.Request(url=self.base_url+qry,
                                   headers=NEWSBANKHEADERS,)
                requests.append[req]
                return requests

    def parse(self, response):
        """
        do something with the response
        """
        fn = settings.SPIDERS_OUT_FILES[self.name]
        with open(fn, 'w') as f:
            pass
            f  # pylint