# RAG bench: the interactive figure

An isometric, interactive drawing of this project's pipeline, built with the [Anatomy](https://github.com/wheresryan22/anatomy) Agent Skill by Ryan (MIT). It explains the pipeline as a working bench instead of boxes and arrows.

| File | What it is |
|---|---|
| `rag-bench-light.html` | The figure, light theme. Standalone: open it in a browser. |
| `rag-bench.html` | The same figure, dark theme. |
| `rag-bench.gif` | A recording of one full cycle, used in the main README. |
| `rag-bench.png` | A still of the finished state. |
| `rig.mjs` | The model: the project's real settings (500-character chunks, 50 overlap, 1536 dimensions, `top_k = 5`), sample chunk names and scores, hybrid-rank merging, and the timeline. |
| `parts.mjs` | The geometry of every part, shared by the build and the live page. |
| `build.mjs` | Writes the HTML pages. |
| `kit/`, `scripts/` | The Anatomy drawing kit and its capture and line-check scripts, copied unchanged. `LICENSE-anatomy` is its licence. |

## Use it

* **Hover** to scrub through ingest and a question. **Click**, **Space** or **Enter** asks the next question; **1**, **2**, **3** pick one. **Arrow keys** step, **Home** and **End** jump. The figure tours by itself when left alone, and shows one still frame under reduced motion.
* **Rebuild** (Node 20.10 or later, no packages to install):

```bash
node build.mjs --light   # writes rag-bench-light.html
node build.mjs           # writes rag-bench.html
```

* **Check** (needs Chrome or Chromium; set `CHROME_PATH` if it is not found):

```bash
node scripts/lines.mjs rag-bench-light.html --reduced      # every drawn line must end on something
node scripts/capture.mjs rag-bench-light.html --out still.png --reduced
```

## What is real and what is sample data

Real, taken from `src/`: chunk size 500 characters, overlap 50, 1536-number vectors, hybrid keyword + vector search, `top_k = 5`, the answer-from-context rule.

Made up for the drawing: the eight chunk names, the three questions, and every keyword and vector score. The two rankings are merged with reciprocal-rank fusion (k = 60) to pick the top five; that is how the figure chooses, not a copy of Azure's internal scoring.
