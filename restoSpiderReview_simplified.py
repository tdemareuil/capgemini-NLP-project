# Logging packages
import logging
import logzero
from logzero import logger

# Scrapy packages
import scrapy
from TA_scrapy.items import ReviewRestoItem     # you can use it if you want but it is not mandatory
from TA_scrapy.spiders import get_info          # package where you can write your own functions


class RestoReviewSpider(scrapy.Spider):
    name = "RestoReviewSpider"

    def __init__(self, *args, **kwargs): 
        super(RestoReviewSpider, self).__init__(*args, **kwargs)

        # Set logging level
        logzero.loglevel(logging.WARNING)

        # Parse max_page
        self.max_page = kwargs.get('max_page')
        if self.max_page:
            self.max_page = int(self.max_page)

        # To track the evolution of scrapping
        self.main_nb = 0
        self.resto_nb = 0
        self.review_nb = 0
        

    def start_requests(self):
        """ Give the urls to follow to scrapy
        - function automatically called when using "scrapy crawl my_spider"
        """

        # Basic restaurant page on TripAdvisor GreaterLondon
        url = 'https://www.tripadvisor.co.uk/Restaurants-g191259-Greater_London_England.html'
        yield scrapy.Request(url=url, callback=self.parse)

   
    def parse(self, response):
        """MAIN PARSING : Start from a classical reastaurant page
            - Usually there are 30 restaurants per page
            - 
        """

        # Display a message in the console
        logger.warn(' > PARSING NEW MAIN PAGE OF RESTO ({})'.format(self.main_nb))
        self.main_nb += 1

        # Get the list of the 30 restaurants of the page
        restaurant_urls = response.css('div.wQjYiB7z > span > a ::attr(href)').extract()
        # For each url : follow restaurant url to get the reviews
        for restaurant_url in restaurant_urls:
            restaurant_url = 'https://www.tripadvisor.co.uk/'+restaurant_url
            #logger.warn('> New restaurant detected : {}'.format(restaurant_url))
            yield response.follow(url=restaurant_url, callback=self.parse_resto)

        
        # Get next page information
        next_page, next_page_number = get_info.get_urls_next_list_of_restos(response)
        
        # Follow the page if we decide to
        if get_info.go_to_next_page(next_page, next_page_number, max_page=10):
            yield response.follow(next_page, callback=self.parse)


    def parse_resto(self, response):
        """SECOND PARSING : Given a restaurant, get each review url and get to parse it
            - Usually there are 10 comments per page
        """
        logger.warn(' > PARSING NEW RESTO PAGE ({})'.format(self.resto_nb))
        self.resto_nb += 1

        # Get the list of reviews on the restaurant page
        url_reviews = response.css('div.quote > a ::attr(href)').extract()

        # For each review open the link and parse it into the parse_review method
        for url_review in url_reviews:
            url_review = 'https://www.tripadvisor.co.uk'+url_review
            #logger.warn('> New review detected : {}'.format(url_review))
            yield response.follow(url=url_review, callback=self.parse_review)

        

        
      

    def parse_review(self, response):
        """FINAL PARSING : Open a specific page with review and client opinion
            - Read these data and store them
            - Get all the data you can find and that you believe interesting
        """

        # Count the number of review scrapped
        self.review_nb += 1

        # You can store the scrapped data into a dictionnary or create an Item in items.py (cf XActuItem and scrapy documentation)
        review_item = {}

        logger.warn('> Test : {}'.format(response))

        
        review_item['partial content'] = response.css('p.partial_entry ::text').extract_first()

        review_item['name'] = response.css('DIV.prw_rup.prw_reviews_member_info_hsx .username .scrname ::text').extract_first()

        review_item['title'] = response.css('div.quote > a > span::text').extract_first()

        review_item['Restaurant_name'] = response.css('a.HEADING ::text').extract()

        review_item['Rating'] = response.xpath('//*[@class="rating"]/span/span/@alt').extract()



        
        yield review_item 


