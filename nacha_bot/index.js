"use strict";
const path = require("path");

const ROOT = path.dirname(require.main.filename);

require("dotenv").config({ path: path.join(ROOT, ".env") });

const puppeteer = require("puppeteer"); // eslint-disable-line import/no-extraneous-dependencies

const Instauto = require("instauto"); // eslint-disable-line import/no-unresolved

const DAYS_UNTIL_UNFOLLOW = 2;

const LOGS = path.join(ROOT, "logs");

const options = {
    cookiesPath: path.join(LOGS, "./cookies.json"),
    username: process.env.USERNAME,
    password: process.env.PASSWORD,
    maxFollowsPerHour: 20,
    maxFollowsPerDay: 150,
    maxLikesPerDay: 50,
    dontUnfollowUntilTimeElapsed: DAYS_UNTIL_UNFOLLOW * 24 * 60 * 60 * 1000,
    // If true, will not do any actions (defaults to true)
    dryRun: false,
};

(async () => {
    let browser;

    try {
        browser = await puppeteer.launch({ headless: false });

        // Create a database where state will be loaded/saved to
        const instautoDb = await Instauto.JSONDB({
            // Will store a list of all users that have been followed before, to prevent future re-following.
            followedDbPath: path.join(LOGS, "followed.json"),
            // Will store all unfollowed users here
            unfollowedDbPath: path.join(LOGS, "unfollowed.json"),
            // Will store all likes here
            likedPhotosDbPath: path.join(LOGS, "liked-photos.json"),
        });

        const instauto = await Instauto(instautoDb, browser, options);

        // List of usernames that we should follow the followers of, can be celebrities etc.
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

        // Now go through each of these and follow a certain amount of their followers
        await instauto.followUsersFollowers({
            usersToFollowFollowersOf,
            skipPrivate: false,
        });

        await instauto.sleep(10 * 60 * 1000);

        // Unfollow auto-followed users (regardless of whether they are following us)
        // after a certain amount of days
        await instauto.unfollowOldFollowed({ ageInDays: DAYS_UNTIL_UNFOLLOW });

        console.log("Done running");
    } catch (err) {
        console.error(err);
    } finally {
        console.log("Closing browser");
        if (browser) await browser.close();
    }
})();
