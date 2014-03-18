import praw, time, sys, urllib2
from collections import deque
# Create config file from config-example.py
from config import USER, PASS

DELAY = 20
FETCH_LIMIT = 250
SEARCH_TERMS = ['mh370', 'flight 370', 'malaysia jet', 'malaysia plane']

class RedditBot:
  subs_to_poll = ['news', 'worldnews']
  r = None
  post_cache = deque()
  already_posted_urls = deque()


  def __init__(self):
    self.r = praw.Reddit(user_agent='MH370News-Bot')
    self.r.config.decode_html_entities = True

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
      self.output('------------------------')
      self.output('Beginning cycle...')
      self.output('')

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

      self.output('Cycle complete. Pausing for %ss...' % DELAY)
      self.output('')
      time.sleep(DELAY)


  def update_already_posted_urls(self):
    already_posted_posts = self.r.get_subreddit('MH370News').get_new(limit=FETCH_LIMIT)
    self.already_posted_urls.extend([p.url for p in already_posted_posts])


  def make_post(self, post, sub=''):
    submission_title = post.title + (' [/r/%s]' % sub)
    try:
      self.r.submit('MH370News', submission_title, url=post.url)
      self.output('Submitted post: ' + post.title)
      self.post_cache.append(post.id)
    except praw.errors.AlreadySubmitted:
      self.output('This post has already been submitted to MH370News. Adding it to the post_cache. (%s)'
            % post.title)
      self.post_cache.append(post.id)
    except praw.errors.ExceptionList, err:
      # Usually this is caused by rate-limiting
      self.output('Could not submit post (rate-limited maybe?). Pausing for 60 seconds...')
      time.sleep(60)


  def output(self, msg):
    print(msg)


# -----------------------------------------------
if __name__ == '__main__':
  r = RedditBot()