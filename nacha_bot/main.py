# imports
import os
import random

from instapy import InstaPy
from instapy import smart_run

from dotenv import load_dotenv
load_dotenv()

# login credentials
insta_username = os.getenv("USERNAME")
insta_password = os.getenv("PASSWORD")

# get an InstaPy session!
# set headless_browser=True to run InstaPy in the background
session = InstaPy(username=insta_username,
                  password=insta_password,
                  headless_browser=True)

accounts = random.sample(["chelcy.cl", "cmoran_shoes", "luau_shoes", "chinitascl", "zapatosmandalas",
                          "estelazapatos", "fessiazapatos", "grossa.cl", "becca.shoesok", "rameshoes.cl", "shoes_divino"], 10)

with smart_run(session):
    """ Activity flow """
    # general settings
    session.set_quota_supervisor(enabled=True, peak_follows_daily=150, peak_follows_hourly=30, peak_unfollows_hourly=60,
                                 peak_unfollows_daily=300, sleep_after=["follows_h", "unfollows_h"], stochastic_flow=True, notify_me=True)
    session.set_skip_users(skip_private=False)
    # activity
    session.unfollow_users(amount=200, instapy_followed_enabled=True, instapy_followed_param="all",
                           style="RANDOM", unfollow_after=2*24*60*60, sleep_delay=5*60)
