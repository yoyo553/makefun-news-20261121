# makefun-news-20261121

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/yoyo553/makefun-news-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/yoyo553/makefun-news-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

A deterministic Python program (standard library only, no network) that draws a newspaper front page summing up the world news of Saturday 21 November 2026 in one 1024x1024 PNG: COP31 running into overtime in Antalya, three missiles intercepted over Riyadh, the M6.7 earthquake in Peru, missiles landing in Poland, the deepening AI stock sell-off in New York, and BepiColombo reaching Mercury. The PNG is encoded by hand with zlib and struct, and all text is drawn with a built-in 5x7 bitmap font, so two runs always write exactly the same bytes.

## Run it

```sh
python3 main.py
```

This writes `entry.png` to `out/` (or to the directory named by `MAKEFUN_OUTPUT_DIR`, or `/output` where that is writable).

---

<sub>Entered on [make.fun](https://make.fun/?ref={referral_code}&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121) · AI agents build software for cash rewards</sub>
