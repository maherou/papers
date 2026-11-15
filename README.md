# Papers

My papers with their companions: a short pitch video and a "Take the Challenge" quiz for each one. The site is live at **https://maherou.github.io/papers/**.

The papers themselves are archived on Zenodo with permanent DOIs, and the videos are on YouTube. This repo holds the page that brings them together, the quizzes, the quiz player, and the two Claude skills that make the quizzes and videos.

Want a site like this for your own papers? Start from [Collegeville/papers](https://github.com/Collegeville/papers), which is set up for copying.

## What's here

```
index.html                  the papers page
_data/papers.yml            one entry per paper
assets/papers/              cover and video thumbnails
quizzes/<slug>/quiz.json    one quiz per paper
player/                     the quiz player (plain HTML and JavaScript)
skills/article-quiz/        Claude skill: paper PDF -> quiz.json
skills/article-video/       Claude skill: paper -> narrated pitch video
_config.yml                 site title, intro text, and address
```

## Adding a paper

1. Add an entry to `_data/papers.yml`. The page lists papers newest month first, and alphabetically by title within a month. The comments at the top of that file explain each field.
2. Save the paper's first page as its cover image, `assets/papers/<slug>.jpg`:

   ```bash
   pdftoppm -f 1 -l 1 -r 80 -jpeg -jpegopt quality=82 -singlefile paper.pdf assets/papers/<slug>
   ```

3. Optional: if YouTube's thumbnail is not the frame you want, save one from the video and set `thumbnail` on the entry. Choose a time when the title slide has finished appearing:

   ```bash
   ffmpeg -ss 4 -i video.mp4 -frames:v 1 -vf scale=540:-2 -q:v 3 assets/papers/<slug>-video.jpg
   ```

4. For a paper already published elsewhere, set `url` (where "Read paper" goes) in place of `doi`, `venue` for the journal citation, and `related` for other versions (each with `label`, `url` and an optional `note`). Set `video.doi` if the video has its own Zenodo record. If the cover image is the publisher's page, set `cover_note` to say so and add it to the "Not covered" list in `LICENSE-CONTENT`.
5. Optional: add a quiz (below) and set `quiz: true` to show the "Take the Challenge" link.

## Making a quiz

1. In the Claude app, with the `article-quiz` skill installed (see below), attach the paper PDF and ask for a quiz. Give the PDF URL and pitch-video URL if you have them.
2. Review the questions in the conversation, or in `quiz-summary.md`.
3. Save the files to `quizzes/<slug>/`, using the paper's slug from `_data/papers.yml`.
4. Check the quiz against the PDF. It must print `OK`:

   ```bash
   python3 skills/article-quiz/scripts/validate_quiz.py quizzes/<slug>/quiz.json --pdf path/to/paper.pdf
   ```

   Quote checking needs `pdftotext` (poppler), `pypdf`, or `pymupdf`, or pass `--text paper.txt` with text you extracted yourself.
5. Set `quiz: true` on the paper's entry, then commit and push.

## Making a pitch video

With the `article-video` skill installed, attach the paper and ask Claude for a short video. Claude drafts a storyboard and script for your approval, renders a silent draft, and asks you to record the narration on your phone. It then cleans the recording and syncs the animation to your voice. Upload the result to YouTube and add its ID under `video` in the paper's entry. See [skills/article-video/SKILL.md](skills/article-video/SKILL.md).

## Installing the skills in the Claude app

For each skill: in Finder, right-click the skill's folder in `skills/` (for example `article-quiz`) and choose **Compress**. Then in the Claude app, go to **Settings > Capabilities > Skills** and upload the zip file.

## Previewing the site on your computer

```bash
bundle install
bundle exec jekyll serve   # http://localhost:4000/papers/
```

To test the quiz checker: `python3 -m unittest discover skills/article-quiz/tests`.

## License

Code is under the [MIT License](LICENSE). Documents, written content, images, audio, and video are under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); see [LICENSE-CONTENT](LICENSE-CONTENT). © 2026 Michael A. Heroux. Not covered: the first-page image of the published Research Software Science article (`assets/papers/research-software-science.jpg`), whose copyright stays with the publisher.

## Image policy

No photos or likenesses of any real person, living or dead, appear in this repo or on anything built from it. All images are created together with Claude, so Michael A. Heroux owns them and they are licensed CC BY 4.0. The only exception is Michael himself: his standard professional portrait and an occasional informal photo. Any other exception needs Michael's explicit approval for that specific case. Future contributors, including AI coding sessions, must follow this policy.
