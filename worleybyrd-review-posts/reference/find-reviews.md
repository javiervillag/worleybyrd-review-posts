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
9. **Photos and profile pictures:** see "Customer photos and profile pictures" at the end of this file.

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

## Customer photos and profile pictures

Reviews with photos make the best posts, so look for them on purpose.

**While reading each review, also record:**
- **Photos the reviewer attached.** On Google they're thumbnails under the text (`button` elements whose label reads "Photo 1 on <name>'s review"); the image URL is in the button's `background-image`. Swap the size suffix for `=w2400` to get the largest version. On Yelp, open the photo and take the biggest size offered.
- **The reviewer's profile picture.** On Google it's the small round image next to the name; take its URL and swap the size suffix for `=s256-c`. On Yelp it's the user photo next to the name.

**Look further back for photo reviews.** After the newest reviews, keep scrolling (about 6 to 12 months back) and pick up any 5-star review with photos that isn't in `seen.json` yet. These are worth a post even if they're older.

**Which photos to use.** A customer's photo is used only as the background of that customer's own post, and only when it makes sense. Otherwise the post uses the normal photo rotation.
- **Use it** if it shows the finished roof, the house, or the crew at work, is sharp (at least about 1000px on the short side), and is not mostly sky, ground or a close-up of a person.
- **Skip it** if it has text, labels, arrows, a watermark, an app badge or a date stamp across the picture, or shows a readable house number or license plate up close.
- **Before/after collages:** crop out just the "after" panel, leaving the labels and watermark out. If that panel is too small or still has text in it, skip it.
- **Several good photos:** put the best one first. On a 2-slide carousel, slide 1 uses the first photo and slide 2 the second (`"photo": ["a.jpg", "b.jpg"]`).
- Save them in `photos/from-reviews/` as `<first>-<initial>-1.jpg`, and so on.

**Profile pictures.** Save real photos (a face, a pet, a house, a logo) to `photos/avatars/<first>-<initial>.jpg` and set `"avatar"` on the review. They show in the circle on the review card. Google's default icon (one colored letter on a flat background) doesn't count: leave `avatar` out and the card shows the brand-colored initial instead.

**Double-check names.** If a reviewer shares a last name with a staff member mentioned in reviews (for example, a "Clausen" reviewing a company whose office contact is "Casey Clausen"), they may be family. Leave the review out and mention it in the hand-over.
