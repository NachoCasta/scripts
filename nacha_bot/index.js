"use strict";
const path = require("path");

const ROOT = path.dirname(require.main.filename);

require("dotenv").config({ path: path.join(ROOT, ".env") });

const puppeteer = require("puppeteer"); // eslint-disable-line import/no-extraneous-dependencies

const Instauto = require("instauto"); // eslint-disable-line import/no-unresolved

const LOGS = path.join(ROOT, "logs");

const RASPBERRY_PI = process.env.RASPBERRY_PI === "true";

const DAYS_UNTIL_UNFOLLOW = 2;
const FOLLOWS_PER_HOUR = 20;
const RANDOM_FOLLOWS_PER_HOUR = Math.floor(
    Math.random() * 2 + FOLLOWS_PER_HOUR
);
const FOLLOWS_PER_DAY = 100;
const RANDOM_FOLLOWS_PER_DAY = Math.floor(Math.random() * 10 + FOLLOWS_PER_DAY);

console.log("Follows per day:", RANDOM_FOLLOWS_PER_DAY);
console.log("Follows per hour:", RANDOM_FOLLOWS_PER_HOUR);

const options = {
    cookiesPath: path.join(LOGS, "./cookies.json"),
    username: process.env.USERNAME,
    password: process.env.PASSWORD,
    maxFollowsPerHour: RANDOM_FOLLOWS_PER_HOUR,
    maxFollowsPerDay: RANDOM_FOLLOWS_PER_DAY,
    followUserRatioMin: null,
    followUserRatioMax: null,
    dontUnfollowUntilTimeElapsed: DAYS_UNTIL_UNFOLLOW * 24 * 60 * 60 * 1000,
    // If true, will not do any actions (defaults to true)
    dryRun: !RASPBERRY_PI,
};

(async () => {
    let browser;

    try {
        const puppeteerOptions = RASPBERRY_PI
            ? {
                  executablePath: "/usr/bin/chromium-browser",
                  headless: true,
                  args: ["--disable-features=VizDisplayCompositor"],
              }
            : { headless: false };
        browser = await puppeteer.launch(puppeteerOptions);

        const instautoDb = await Instauto.JSONDB({
            followedDbPath: path.join(LOGS, "followed.json"),
            unfollowedDbPath: path.join(LOGS, "unfollowed.json"),
            likedPhotosDbPath: path.join(LOGS, "liked-photos.json"),
        });

        const instauto = await Instauto(instautoDb, browser, options);

        const usersToFollowFollowersOf = [
            "chelcy.cl",
            "cmoran_shoes",
            "luau_shoes",
            "chinitascl",
            "zapatosmandalas",
            "estelazapatos",
            "fessiazapatos",
            "grossa.cl",
            "becca.shoesok",
            "rameshoes.cl",
            "shoes_divino",
        ];

        await instauto.followUsersFollowers({
            usersToFollowFollowersOf,
            skipPrivate: false,
            maxFollowsTotal: RANDOM_FOLLOWS_PER_DAY,
        });

        await instauto.sleep(10 * 60 * 1000);

        await instauto.unfollowOldFollowed({
            ageInDays: DAYS_UNTIL_UNFOLLOW,
            limit: FOLLOWS_PER_DAY + 50,
        });

        console.log("Done running");
    } catch (err) {
        console.error(err);
    } finally {
        console.log("Closing browser");
        if (browser) await browser.close();
    }
})();
