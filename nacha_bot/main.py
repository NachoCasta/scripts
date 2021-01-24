# imports
from instapy import InstaPy
from instapy import smart_run

# login credentials
insta_username = ''
insta_password = ''

# get an InstaPy session!
# set headless_browser=True to run InstaPy in the background
session = InstaPy(username=insta_username,
                  password=insta_password,
                  headless_browser=False)

accounts = ["chelcy.cl", "cmoran_shoes", "luau_shoes", "chinitascl", "zapatosmandalas",
            "estelazapatos", "fessiazapatos", "grossa.cl", "becca.shoesok", "rameshoes.cl", "shoes_divino"]

with smart_run(session):
    """ Activity flow """
    # general settings
    session.set_quota_supervisor(enabled=True, peak_follows_daily=150, peak_follows_hourly=30, peak_unfollows_hourly=40,
                                 peak_unfollows_daily=200, sleep_after=["follows_h", "unfollows_d"], stochastic_flow=True, notify_me=True)
    session.set_skip_users(skip_private=False)
    # activity
    session.unfollow_users(amount=100, instapy_followed_enabled=True, instapy_followed_param="all",
                           style="RANDOM", unfollow_after=2*24*60*60, sleep_delay=5*60)
    session.follow_user_followers(accounts, amount=10, randomize=False)
    session.unfollow_users(amount=100, instapy_followed_enabled=True, instapy_followed_param="all",
                           style="RANDOM", unfollow_after=2*24*60*60, sleep_delay=5*60)
    session.follow_likers(accounts, photos_grab_amount=2, follow_likers_per_photo=10,
                          randomize=True, sleep_delay=600, interact=False)
    session.like_by_feed(amount=100, randomize=True,
                         unfollow=False, interact=False)
