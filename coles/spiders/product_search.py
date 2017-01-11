# -*- coding: utf-8 -*-
import scrapy
from selenium import webdriver
# from selenium.webdriver.support.wait import WebDriverWait
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support import expected_conditions as EC
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import TextResponse, Response
from scrapy.linkextractors import LinkExtractor
# from scrapy.contrib.linkextractors import LxmlLinkExtractor
from lxml import html


class Category(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()


class Item(scrapy.Item):
    name = scrapy.Field()
    url = scrapy.Field()
    category = scrapy.Field()
    sub_category = scrapy.Field()
    sub_sub_category = scrapy.Field()


class ProductSearchSpider(scrapy.Spider):
    name = "product-search"
    allowed_domains = ["shop.coles.com.au"]
    start_urls = ['https://shop.coles.com.au/a/a-national/everything/browse', ]

    def __init__(self, *args, **kwargs):
        self.driver = webdriver.Chrome()
        self.domain = "https://shop.coles.com.au"
        self.count = 0
        self.link_structure = {}
        # super(ProductSearchSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        self.driver.get(response.url)
        # 'https://shop.coles.com.au/a/a-national/everything/browse'
        # 'https://shop.coles.com.au/a/a-national/everything/browse/bread-bakery?pageNumber=1'
        # )
        # continue_btn = WebDriverWait(self.driver, 5).until(
        #     EC.visibility_of_element_located((By.CLASS_NAME, "popup-close")))
        # continue_btn.click()
        #
        # response.xpath('.//a[@class="clear"]/@href').extract()
        # response = Response(
        #     url=response.url,
        #     body=self.driver.page_source, )
        response = TextResponse(
            url=response.url, body=self.driver.page_source, encoding='utf-8')

        for category in response.xpath('.//a[@class="clear"]'):
            category_item = Category()
            category_item['title'] = category.xpath(
                './*/span[@class="item-title"]/text()').extract()[0]
            category_item['url'] = "{}{}".format(
                self.domain, category.xpath('./@href').extract()[0])
            print category_item['title']
            print " " + category_item['url']
            self.link_structure[category_item['title']] = {}

            if category_item.get('url'):
                if self.count > 1:
                    break
                self.count += 1
                yield scrapy.Request(
                    category_item['url'],
                    meta={
                        'category': category_item
                    },
                    callback=self.parse_category)
    # from scrapy.shell import inspect_response
    # inspect_response(response, self)
    # self.driver.close()
    def parse_category(self, response):
        '''
        parent category
        Will present a list of sub categories to select from
        '''
        self.driver.get(response.url)
        category = response.meta['category']
        response = TextResponse(
            url=response.url, body=self.driver.page_source, encoding='utf-8')
        for sub_cat in response.xpath('.//a[@class="clear"]'):
            sub_category = Category()
            sub_category['title'] = sub_cat.xpath(
                './*/span[@class="item-title"]/text()').extract()[0]
            sub_category['url'] = "{}{}".format(
                self.domain, sub_cat.xpath('./@href').extract()[0])
            self.link_structure[category['title']][sub_category['title']] = {}
            if sub_category.get('url'):
                yield scrapy.Request(
                    sub_category['url'],
                    meta={
                        'category': category,
                        'sub_category': sub_category
                    },
                    callback=self.parse_sub_category)

    def parse_sub_category(self, response):
        '''
        child of parent category
        Will present a list of child categories
        '''
        self.driver.get(response.url)
        category = response.meta['category']
        sub_category = response.meta['sub_category']
        response = TextResponse(
            url=response.url, body=self.driver.page_source, encoding='utf-8')

        for sub_sub_cat in response.xpath('.//a[@class="clear"]'):
            sub_sub_category = Category()
            sub_sub_category['title'] = sub_sub_cat.xpath(
                './*/span[@class="item-title"]/text()').extract()[0]
            sub_sub_category['url'] = "{}{}".format(
                self.domain, sub_sub_cat.xpath('./@href').extract()[0])
            self.link_structure[category['title']][sub_category['title']][
                sub_sub_category['title']] = sub_sub_category['url']
            if sub_sub_category.get('url'):
                yield scrapy.Request(
                    sub_sub_category['url'],
                    meta={
                        'category': category,
                        'sub_category': sub_category,
                        'sub_sub_category': sub_sub_category
                    },
                    callback=self.parse_sub_sub_category_items)

    def parse_sub_sub_category_pages(self, response):
        '''
        Should be the final (bottom child of the nested category strucutre)
        Will have multiple pages of items, need to iterate through these
        '''
        self.driver.get(response.url)
        category = response.meta['category']
        sub_category = response.meta['sub_category']
        response = TextResponse(
            url=response.url, body=self.driver.page_source, encoding='utf-8')

        for page in response.xpath(
                './/ul[@class="pagination"]//li[@class="page-number"]'):
            page_active = page.xpath('/a/@href').extract() ? True : False
            if page_active:
                page_url = response.url
                page_number = page.xpath('.//span[@class="number"]/text()')[
                    0].extract()

                yield scrapy.Request(
                page_url,
                meta = {
                'first_page': response,
                'page': page_number,
                'category': category,
                'sub_category': sub_category,
                'sub_sub_category': sub_sub_category,
                },
                callback=self.parse_item_page
                )
            else:
                page_url = response.url
                page_number = page.xpath('.//span[@class="number"]/text()')[
                    0].extract()

                yield scrapy.Request(
                page_url,
                meta = {
                'page': page_number,
                'category': category,
                'sub_category': sub_category,
                'sub_sub_category': sub_sub_category,
                },
                callback=self.parse_item_page
                )

    def parse_item_page(self, response):
        if response.meta.get('first_page'):
            response = reponse.meta['first_page']
        else:
            self.driver.get(response.url)
            response = TextResponse(
                url=response.url, body=self.driver.page_source, encoding='utf-8')

    # def parse(self, response):
    #     '''
    #     tester parse
    #     '''
    #     self.driver.get('')

    # class ProductSearchSpider(CrawlSpider):
    #     name = "product-search"
    #     allowed_domains = ["shop.coles.com.au"]
    #
    #     def __init__(self, *args, **kwargs):
    #         self.driver = webdriver.Firefox()
    #         super(ProductSearchSpider, self).__init__(*args, **kwargs)
    #
    #         self.start_urls = [
    #             'https://shop.coles.com.au/a/a-national/everything/search/milk',
    #         ]
    #
    #         # rules = (Rule(
    #         #     LinkExtractor(, )),
    #         #     callback="parse_page",
    #         #     follow=True), )
    #
    #     rules = (Rule(
    #         LinkExtractor(allow=()), callback='parse_page', follow=True), )
    #
    #     # def parse(self, response):
    #     #     print "response: %s" % (response)
    #     def parse_page(self, response):
    #         print "response: %s" % (response)
    #         from scrapy.shell import inspect_response
    #         inspect_response(response, self)


class Scrapy1Spider(CrawlSpider):
    name = "craiglist"
    allowed_domains = ["sfbay.craigslist.org"]
    start_urls = ('http://sfbay.craigslist.org/search/npo', )

    rules = (Rule(
        LinkExtractor(
            allow=(), restrict_xpaths=('//a[@class="button next"]', )),
        callback="parse_page",
        follow=True), )

    def parse_page(self, response):
        site = html.fromstring(response.body_as_unicode())
        titles = site.xpath('//div[@class="content"]/p[@class="row"]')
        print len(titles), 'AAAA'
