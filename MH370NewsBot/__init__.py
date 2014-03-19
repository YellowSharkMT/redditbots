import praw, time, sys, urllib2, logging, os
from collections import deque
# Create config file from config-example.py
from config import USER, PASS

DELAY = 90
FETCH_LIMIT = 250
SEARCH_TERMS = ['mh370', 'flight 370', 'malaysia jet', 'malaysia plane']
LOG_FILE = os.path.dirname(__file__) + '/bot-output.log'


class RedditBot:
    subs_to_poll = ['news', 'worldnews']
    r = None
    post_cache = deque()
    already_posted_urls = deque()
    logger = None

    def __init__(self, autostart=True):
        self.r = praw.Reddit(user_agent='MH370News-Bot')
        self.r.config.decode_html_entities = True

        if autostart:
            self.init_logger()
            self.do_bot()


    def do_bot(self):
        self.log_in()
        self.poll()

    def log_in(self):
        logged_in = False
        while not logged_in:
            try:
                self.output('Attempting to log in...')
                self.r.login(USER, PASS)
                self.output('Logged in.')
                logged_in = True
            except urllib2.HTTPError, err:
                self.output('Log in failed. (%s)' % err.message)

    def poll(self):
        while True:
            self.update_already_posted_urls()

            for sub in self.subs_to_poll:
                self.output('Fetching posts from /r/%s...' % sub)
                posts = self.r.get_subreddit(sub).get_top_from_day(limit=FETCH_LIMIT)
                for post in posts:
                    isMatch = any(string in post.title.lower() for string in SEARCH_TERMS)
                    isFresh = post.id not in self.post_cache
                    isAlreadyPosted = post.url in self.already_posted_urls
                    if isFresh and isMatch and not isAlreadyPosted:
                        self.make_post(post, sub)
                    elif isAlreadyPosted:
                        self.post_cache.append(post.id)

            time.sleep(DELAY)

    def update_already_posted_urls(self):
        already_posted_posts = self.r.get_subreddit('MH370News').get_new(limit=FETCH_LIMIT)
        self.already_posted_urls.extend([p.url for p in already_posted_posts])

    def make_post(self, post, sub=''):
        submission_title = post.title
        try:
            submitted_post = self.r.submit('MH370News', submission_title, url=post.url)
            flair_result = self.r.get_subreddit('MH370News').set_flair(submitted_post, ('/r/%s' % sub), sub)
            self.output('Submitted post to %s: %s' + (sub, post.title))
            self.post_cache.append(post.id)
        except praw.errors.AlreadySubmitted:
            self.log_error('This post has already been submitted to MH370News. Adding it to the post_cache. (%s)'
                           % post.title)
            self.post_cache.append(post.id)
        except praw.errors.ExceptionList, err:
            # Usually this is caused by rate-limiting
            self.log_error('Could not submit post (rate-limited maybe?). Pausing for 60 seconds...')
            time.sleep(60)

    def output(self, msg):
        self.logger.info(msg)
        #print(msg)

    def log_error(self, msg):
        self.logger.error(msg)
        #print(msg)

    def test(self):
        self.log_in()
        self.output('Logged in successfully.')

    def init_logger(self):
        self.logger = logging.getLogger('BotLogger')
        hdlr = logging.FileHandler(LOG_FILE)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(msg)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel('DEBUG')


# -----------------------------------------------
if __name__ == '__main__':
    r = RedditBot()