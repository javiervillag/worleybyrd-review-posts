---
name: worleybyrd-review-posts
description: Turns WorleyByrd Roofing & Restoration's newest 5-star reviews (Google, the WorleyByrd website testimonials, and BBB) into ready-to-post Instagram images (1080x1350) in WorleyByrd's brand, using WorleyByrd's own drone photos, with captions and an approval sheet. Already set up with WorleyByrd's logo, colors, photos and review links, so there are no setup questions. Use when someone says "make review posts", "new review posts", "turn our reviews into Instagram posts", "post our 5-star reviews", "new reviews for WorleyByrd", or pastes a review and wants a post. It never posts anything itself.
---

# WorleyByrd review posts

You're helping someone on the WorleyByrd team, most likely marketing, who is probably **not technical**. Keep messages short and friendly. Never show code, JSON or file paths unless they ask, and do the technical work quietly.

This skill **never posts, publishes or replies** to anything online. The person approves the images and posts them themselves.

Everything is already set up for WorleyByrd: logo, brand colors (navy and gold), fonts, background photos (WorleyByrd's own drone shots) and review links. **Don't ask setup questions.**

## 0. Get the WorleyByrd folder ready (first time only)

- The tools sit next to this file: `scripts/make_posts.py` and `scripts/fonts/`.
- The ready-made business folder is `business/`. It holds `settings.json`, `logo.png`, `photos/`, and `seen.json` (the reviews already turned into posts, so they aren't repeated).
- If there's no `WorleyByrd Review Posts/` folder in the working folder yet, **copy `business/` there under that name** and use the copy from now on. In Cowork that's the folder the person picked; it's kept for next time.
- If the person attaches a `seen.json` or a `settings.json` from a previous run, put it in that folder first.

Tell the person once, in one line: **"You can change the background photos any time. Just send me new house or roof photos and I'll swap them in."**

## 1. Get the newest 5-star reviews

Use the three links in `settings.json` (`review_links`): Google, the WorleyByrd website testimonials, and BBB.

**If you have a browser** (Claude in Chrome, or Cowork's browser), open each one and follow `reference/find-reviews.md`. Read only: never click Reply, Like, Report or Write a review. On Google, take about the 20 newest reviews.

**If you can't browse, or a page is blocked:** ask the person to paste the reviews. Say: "Open WorleyByrd on Google Maps, click Reviews, sort by Newest, and paste the last few 5-star reviews here."

Rules:
- **5-star only.** Skip 4-star and lower. On the website, the review widget shows star images: filled stars are `/star/f.svg` and empty ones are `/star/e.svg`, so a 1-star review still shows five star shapes.
- **Website testimonials are Google reviews** copied onto the site. Use `"source": "Google"`.
- **Same review in two places:** the same customer often posts on Google and BBB. Make **one** post, and use the Google copy, because BBB hides staff names.
- **Customer photos and profile pictures:** reviews with photos make the best posts, so look for them on purpose, including older 5-star reviews with photos that aren't in `seen.json` yet. When a reviewer attached a photo that works as a background (the finished roof, the house, the crew; sharp; no text, labels or watermark), save it in `photos/from-reviews/` and set `"photo"` on that review: it becomes that post's background, and only that post's. Crop a before/after collage down to the "after" panel. If no photo works, leave `photo` out and the post uses the normal rotation. Save a real profile picture to `photos/avatars/` and set `"avatar"`; skip Google's default one-letter icons. The details are in `reference/find-reviews.md` ("Customer photos and profile pictures"). In the hand-over, say which posts use the customer's own photo.
- **Image testimonials** (a screenshot or card with text): read the text from the image, check it word for word, and treat it as a review.
- Reviews already in `seen.json` are skipped automatically. Say how many were new.

## 2. Write `reviews.json` (you do this; the person never sees it)

The format is at the top of `scripts/make_posts.py`.

- **`quote`** is the full review, word for word. Never fix spelling or grammar.
- **`name`** is first name plus last initial ("Sarah M.").
- **`date`** is "Mon YYYY". It goes in the approval sheet only, not on the image.
- **`excerpt`** (for long reviews) is the 1 to 3 strongest whole sentences, copied word for word.
- **`hl`** is one short phrase shown in gold, copied word for word.
- **Blurred names (BBB only):** BBB shows staff names as "REMOVED". Don't leave "REMOVED" in, and don't guess the name.
  - First try an `excerpt` that avoids it.
  - Otherwise swap in the plainest role word that reads naturally, with no brackets. For example, "REMOVED(owner) responds" becomes "The owner responds". Write it as `"edits": [{"from": "REMOVED(owner)", "to": "The owner"}]`. It's listed in the approval sheet.
- **`caption`**: under 80 words, warm and plain, family-owned Central Texas voice.
  - Thank the reviewer by first name.
  - Mention one specific thing from the review.
  - End with `Free roof inspection: (512) 216-8202` and 3 or 4 of the hashtags in `settings.json`.
  - Never invent details that aren't in the review.

## 3. Make the images

```bash
pip install pillow   # only if "Pillow is missing" appears
python3 scripts/make_posts.py --folder "WorleyByrd Review Posts" reviews.json
```

Layout is automatic:
- Short reviews get the big-quote look.
- Medium reviews get the review-card look.
- Reviews of 70+ words become a 2-slide carousel: best line first, full review second.

If they ask for a different look, add `--template hero|bubble|auto` or `--carousel off|long-only|always`.

**Look at every image before showing it.** Check for cut-off text, an awkward photo crop, or stray "REMOVED". To fix a crop, set `photo_focus` for that photo in `settings.json`, then run again.

## 4. Hand over

1. Show the images grouped per post, with each caption underneath.
2. Give them the `posts/<date>` folder to download, zipped if possible. It includes `approval.csv` (opens in Excel or Google Sheets) and `captions.md`.
3. Tell them in plain words:
   - How many posts you made, and how many are carousels
   - Anything that was skipped or edited
   - That nothing was posted, so they review and post themselves
   - The next step: "Next week just say 'make review posts' and I'll grab the new ones."
