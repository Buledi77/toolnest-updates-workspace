# How to add a review

1. Copy `data/reviews/_example.json` to `data/reviews/<slug>.json`.
2. Use the same slug as the page in `tools/<slug>.html`.
3. Use `testStatus: "tested"` only after using a real account. Record the date,
   plan, at least three real tasks, results and time taken. Use
   `testStatus: "researched"` when you only checked documentation and pricing.
4. Write honest pros, cons, best-fit and skip guidance. Keep the verdict to two
   or three sentences. Scores must be numbers from 1 to 10.
5. Put screenshots in `assets/reviews/<slug>/` and give each image a
   descriptive `alt` and caption. The build converts PNG/JPEG sources to WebP
   with `ffmpeg`; WebP files can be added directly. The first screenshot is
   eager-loaded; later screenshots are lazy-loaded.
6. Add current pricing notes and the date checked. Add FAQs only when you have
   a useful, supportable answer.
7. Run:

   ```sh
   python3 scripts/build_site.py
   scripts/qa-check
   ```

The build adds only the sections supported by the JSON. It also adds Review and
Product structured data with a rating only for `tested` reviews. Researched
reviews use Article structured data instead.
