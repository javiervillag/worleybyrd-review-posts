# Finding the newest WorleyByrd reviews in a browser

This works with any browser tool: Claude in Chrome, Cowork's browser, or ChatGPT's agent browser.

General rules:
- Work in a new tab and close it when done.
- Read only. Never click Reply, Like, Share, Report, or "Write a review".
- Prefer `get_page_text`, `find` and `read_page` over screenshots. Use `javascript_tool` only to read the page, never to change it.
- Collect about the newest 10 reviews, then stop.

## WorleyByrd website testimonials

1. Open the website testimonials link.
2. The reviews sit in a review widget. Read each card's name, date and text with `javascript_tool` on `.ti-review-item` elements (`.ti-name`, `.ti-date`, `.ti-review-content`), or with `get_page_text`.
3. **Stars are images.** Count the `img` elements whose `src` ends in `/star/f.svg` (filled). Keep only cards with 5 filled stars.
4. These are Google reviews, so use `"source": "Google"`. Most are older than the newest Google reviews, so check for duplicates.

## Google Maps

1. Open the Google review link. If a consent banner shows, choose **Reject all**.
2. Click the **Reviews** tab. `find` "Reviews for <business>" returns the tab.
3. Sort by newest: click the **Sort reviews** button, then pick the **Newest** menu item.
4. **Scroll the left panel**, not the map, about 5 ticks at a point inside it. The review cards only load after you scroll. You'll see a spinner first.
5. Expand long reviews: click every **More** button in the list. There are usually around 10.
6. Read the reviews with `javascript_tool` on `document.querySelector('[role="main"]').innerText`, or with `get_page_text`. Each card reads in this order: name, "N reviews" (the reviewer's own count, so ignore it), the relative date ("3 weeks ago"), sometimes "NEW", then the text.
7. **Star rating per card:** the card text doesn't include it. Zoom a screenshot on the star row under the name, or `read_page` that card. Only keep cards with all stars filled.
8. Repeat steps 4 to 7 until you have about 10 reviews.

Notes:
- Google's page changes often. Use `find` with the visible words rather than class names.
- "Translated by Google": use the original text, or skip the review.
- "Response from the owner" is not part of the review. Leave it out.

## BBB

1. Open the BBB link. A "Just a moment…" check shows first. Wait about 5 to 10 seconds and it passes on its own. If it asks you to tick a box or solve a puzzle, stop and ask the user to open the page.
2. Pick **Most recent** in the sort control if it isn't already selected.
3. Read the page with `get_page_text` or `javascript_tool` (`document.body.innerText`). Each review reads in this order: "Review from", the name (first name plus initial, such as "Sam P"), "Date: MM/DD/YYYY", "5 stars", then the text. The rating is in the text, so filter on "5 stars".
4. Some reviews start with emoji stars, which show up as "?????" in the text. Drop that leading run; it isn't part of the words.
5. Expand any "Read more" link before reading.
6. **Redactions:** BBB blurs staff names. In the text they read "REMOVED", inside a blurred `<span>`. Keep "REMOVED" exactly as it appears in `quote`. Step 3 of SKILL.md explains how to swap it for a bracketed neutral word with `edits`.
7. Complaints live on a separate tab. Ignore them.

## Other sources (Facebook, Yelp, Nextdoor, Houzz)

Same pattern: find the reviews list, sort by newest if possible, expand "More", and read name, date, rating and full text. Facebook "recommendations" have no stars. Only use them if the user says to, and set `"source": "Facebook"`.
