# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class DemolitionItem(scrapy.Item):
    # we can have duplicates for given address, lat, lon
    address = scrapy.Field()
    lat = scrapy.Field()
    lon = scrapy.Field()
    text = scrapy.Field()
    image_url = scrapy.Field()

