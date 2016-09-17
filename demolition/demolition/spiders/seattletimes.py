import copy
import json

import scrapy

from demolition import settings


NEWSBANKHEADERS = {
    "Host": "infoweb.newsbank.com.ezproxy.spl.org:2048"
}

NEWSBANKCOOKIES = {
    "bc_session": "f12eedff-7690-48d1-8d6a-9c3f82f7ba66",
    "bc_username": "bryancwilson",
    "bc_language": "en-US",
    "bc_barcode": "1000010466257",
    "ezproxy": "QPgiIBokzx5nNK7",
    "has_js": "1",
}


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
            # search 
            addresses = self._make_address_variants(site['address'])
            for address_variant in addresses:                
                qry = "&val0=%22{0}%22".format(address_variant)
                req = scrapy.Request(url=self.base_url+qry,
                                    headers=NEWSBANKHEADERS,
                                    cookies=NEWSBANKCOOKIES)
                requests.append(req)
        return [requests[0]]

    def parse(self, response):
        """
        do something with the response
        """
        import pdb; pdb.set_trace()
        fn = settings.SPIDERS_OUT_FILES[self.name]
        with open(fn, 'w') as f:
            pass
            f  # pylint
