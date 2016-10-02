# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy import signals
from scrapy.exporters import JsonItemExporter

from .exporters import SeaTimesSnippetsExporter, SeaTimesTextToImageExporter


# can I just do DemolitionItem.fields?
EXPORT_FIELDS_COMMON = [
   	'permit_id', 'address', 'lat', 'lon', 'text', 'image_url', 'news_date',
]


class ImageGeneratorPipeline(object):
	"""
	Item created by scraping Seattle Times
	Items that have 'text' should be saved to one JSON file
	.... generate an Image file of the X characters surrounding the address in the text
	Items that have 'image_url' file should have their image URLs OCRed...
	...save out the good images to a folder
	...Items without any good images are destroyed
	...Items with good images are saved to a different JSON file
	"""

	# TODO: Implement this to pull from Redis and process

     @classmethod
     def from_crawler(cls, crawler):
         pipeline = cls()
         crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
         crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
         return pipeline

    def spider_opened(self, spider):
        self.snip_exporter = SeaTimesSnippetsExporter(
        	fields_to_export=EXPORT_FIELDS_COMMON,
        	export_empty_fields=True
        )
        self.text_img_exporter = SeaTimesTextToImageExporter(
        	fields_to_export=EXPORT_FIELDS_COMMON,
        	export_empty_fields=True
        )
        self.snip_exporter.start_exporting()
        self.text_img_exporter.start_exporting()

    def spider_closed(self, spider):
        self.snip_exporter.finish_exporting()
        self.text_img_exporter.finish_exporting()

    def process_item(self, item, spider):
        exporter = self.snip_exporter if item.get('image_url', None) else self.text_img_exporter
        exporter.export_item(item)
        return item


class JSONExportPipeline(object):
	"""
	This will be the final processor to a format that will be read
	in D3.js
	"""

    def __init__(self):
        self.files = {}

     @classmethod
     def from_crawler(cls, crawler):
         pipeline = cls()
         crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
         crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
         return pipeline

    def spider_opened(self, spider):
        file = open('seattimetimes.json', 'w+')
        self.files[spider] = file
        self.exporter = JsonItemExporter(file)
        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        file = self.files.pop(spider)
        file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item
