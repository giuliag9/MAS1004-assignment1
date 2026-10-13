# Report notes, gathered as the runs happen

Evidence only. Every number here was printed by code that was actually run;
the source line is named next to each block. This file feeds
`long_report/long_report.tex` at Step 19.

## Problem 1. The categories, and how many images came back

Source: `src/collect.py` writes into `data/raw/<class name>/0001.jpg`, and its
own docstring (lines 8-10) says an image that fails to download, fails to open,
or is too small is skipped and counted, so the number you get back is usually
smaller than the number you asked for. `data/clean` is a copy of `data/raw` made
before any cleaning. Counts printed in Colab:

| class | data/raw | data/clean | data/new_images |
|---|---|---|---|
| amethyst | 134 | 134 | 5 |
| aventurine | 138 | 138 | 5 |
| citrine | 150 | 150 | 5 |
| rose_quartz | 150 | 150 | 6 |
| total | 572 | 572 | 21 |

Four categories, all varieties of quartz: amethyst, citrine, rose_quartz and
aventurine. A quartz variety is mostly the same crystal with a different colour
and a different kind of inclusion inside it, so the model has to work from
colour and from what shows through the stone, which is what makes the pairs
worth telling apart rather than being obviously different shapes. 150 each was
asked for; amethyst (134) and aventurine (138) came back short because the
collector keeps only the links that still open and are big enough. `data/clean`
matched `data/raw` exactly, so nothing had been cleaned yet at that point. The
new images are 21, five in each class and six rose quartz, which is the five per
class Problem 5 asks for.

## Problem 2. What prepare_image made of the images

Source: `src/data.py` lines 23-26 hold the recipe and lines 41-71 are
`prepare_image`. `pytest tests/test_data.py` is 16 passed, and
`python -m pytest -q tests/test_data.py -k prepare` is 7 passed, 9 deselected.
`src/show_prepare.py` draws the crop for one file and prints what it keeps and
throws away; `--scan <folder>` lists the pictures the crop throws most of away,
and `--scan <folder> --sheet` draws those as one picture of tiles, each tile
named and measured with what the crop keeps and what it drops from each side.

Measured on `data/new_images/aventurine/IMG_3068.JPG`, one of the photos taken
for this assignment, 4032 x 3024:

| step | result |
|---|---|
| on disk | 4032 x 3024 |
| after Resize(256) | 341 x 256 (shorter side 3024 -> 256) |
| square kept | x 58..282, y 16..240 |
| cut off, in the 341 x 256 picture | 58 left, 59 right, 16 top, 16 bottom |
| cut off, back in the original photo | 686 left, 698 right, 189 top, 189 bottom |
| kept | 57.5% of the area; 34.3% of the width and 12.5% of the height thrown away |

That the rectangle drawn is the rectangle the model gets is measured, not
assumed: the same box run through ToTensor and Normalize differs from
`prepare_image` by 0.0e+00, and `prepare_image` differs from torchvision's own
ImageNet recipe for ResNet18 by 0.0e+00.

### An image where the crop cut off part of the thing I care about

`data/new_images/rose_quartz/9dacd40a-f98e-4312-a62d-78c4fd3a0a4b.JPG`,
900 x 1600. Resize gives 256 x 455, the square keeps y 116..340, so 116 rows are
dropped above and 115 below: 50.8% of the height, 408 and 404 pixels of the
original, and only 43.1% of the area survives. The stone reaches the top of the
square, so its edge is thrown away. Wide photos lose the same way on the left
and right: the 4032 x 3024 photo above loses 34.3% of its width, 686 pixels each
side, even though the stone is nowhere near those edges.

A second case, found with `--scan data/new_images --sheet`: the contact sheet
draws the 15 worst of the 21 photos as `prepare_sheet.png`, and
`data/new_images/rose_quartz/ea7f4b76-efcc-4973-814e-a7afe9273198.JPG`,
1500 x 2000, keeps 57.5% of the area while the point of the heart is below the
bottom edge of the square: the tip of the stone is thrown away and the model
never sees it. The sheet turned up four pieces the crop cuts through, all in
these 21 photos, and each one is drawn at full size with `--image`:
the tall rose quartz above (top and both sides), the heart (its point),
`amethyst/44db3aaf-5cdf-4004-9255-868fefec64c3.JPG` (the top of the crystal) and
`aventurine/aba4d635-c6c9-4d89-af6f-9f279d0e5178.JPG` (the point of a pendant and
its loop). The heart and the tall quartz are the clearest of the four.

Finding a case needed the drawings, not a number. Three cheap ways of guessing
"did the crop cut the stone" were tried on these 21 photos, and all three put a
photo whose stone is safely inside the square above the one that is really cut:

| way of guessing | the picture that is really cut | a picture whose stone is safe | verdict |
|---|---|---|---|
| how unlike the plain background the band outside the square is | 9dacd40a, 24.8%, 8th of 21 | `aventurine/IMG_3197.JPG`, a stone lying in a palm, 84.3%, 1st | wrong way round |
| the same, as the longest unbroken run along the edge of the square | 9dacd40a, 5.6%, 10th of 21 | `amethyst/IMG_3200.JPG`, stone inside on cardboard, 33.9%, 1st | wrong way round |
| how busy the crop line is against how busy the inside is | 9dacd40a, 5.83 | `aventurine/IMG_3197.JPG`, 6.73 | the safe one scores higher |

The palm and the cardboard photo both beat the real case because what is on
their crop line is a brightness gradient or skin, not the stone. So `--scan`
reports the crop's own geometry only, says that the drawing decides, and
`src/show_prepare.py` keeps that reasoning in its docstring instead of shipping a
number that would have put the wrong photo in the report.

### The four pictures that go in the report

`long_report/figures/prepare_original.jpg`, `prepare_result.png`,
`prepare_cropbox.png` and `prepare_side_by_side.png` are `show_prepare.py` run in
Colab on an image from `data/clean/rose_quartz/`, so the left-hand picture is
what the template's caption at `long_report.tex:42` asks for, an image as
downloaded: a rose quartz heart on a stand, with a sphere and two towers behind
it. The red square in `prepare_cropbox.png` is the 224 x 224 crop and
`prepare_result.png` is the heart filling it. `prepare_sheet.png` is the drawing
of the 15 crops that throw most of the area away, described above; it is not in
the template and is kept as the evidence behind that paragraph.

The same four files made from `data/new_images/aventurine/IMG_3068.JPG` (the
4032 x 3024 photo measured above, a stone on a plain surface) are not lost: they
are kept as `own_photo_original.jpg` and `own_photo_result.png`, so a picture
taken by hand for this assignment can still be shown as a second Problem 2
picture if the report wants one. Nothing in `check.py` reads any of these files;
they are there for `long_report.tex` only.

### Four of the photos are stored sideways (EXIF orientation 6)

`show_prepare.py --scan data/new_images` over 21 images reports an orientation
other than 1 for `amethyst/IMG_3200.JPG`, `aventurine/IMG_3196.JPG`,
`rose_quartz/IMG_3069.JPG` and `rose_quartz/IMG_3194.JPG`. The camera stored
those landscape, with a note in the file saying "turn 90 degrees before
showing". `Image.open(...).convert("RGB")` does not apply the note, so
`prepare_image` cuts the middle out of a turned picture. The six steps do not
include a turning step and the tests never use a picture with EXIF data, so the
tests pass while those four reach the model sideways. The page will not even
agree with itself here: `docs/app.js` line 166 loads an upload into an `<img>`,
and browsers apply the note themselves, so the browser turns the photo and
Python does not. The self test badge cannot catch it, because `selftest.json`
holds three already resized square pictures with no EXIF in them.

## Problem 3 experiment table (before any cleaning)

Source: the four "One line for your experiment table" blocks, saved in
`results/<tag>_output.txt`.

| tag | start | trained | epochs | lr | trainable parameters | train accuracy | test accuracy |
|---|---|---|---|---|---|---|---|
| run | ImageNet | all layers | 10 | 0.0001 | 11,178,564 | 100.0% | 92.2% |
| scratch | random | all layers | 10 | 0.0001 | 11,178,564 | 99.6% | 82.6% |
| frozen | ImageNet | last layer | 10 | 0.001 | 2,052 | 97.2% | 88.7% |
| lr1e-3 | ImageNet | all layers | 10 | 0.001 | 11,178,564 | 96.7% | 84.3% |

Data: 572 images, 4 classes, amethyst 134 / aventurine 138 / citrine 150 /
rose_quartz 150. Split 457 train / 115 test.

## The split, and why the four rows are comparable

`split_train_test` uses `np.random.default_rng(seed)`, a local generator, so it
does not depend on global random state. Called twice locally with the same
class counts it returned identical test rows. Per class the test set is
amethyst 27, aventurine 28, citrine 30, rose_quartz 30; no image is on both
sides. `data/clean` did not change between the four runs, so all four test
accuracies are measured on the same 115 images.

## Tests as fractions of images

115 test images means one image is 0.87%.

| tag | test | as images |
|---|---|---|
| run | 92.2% | 106/115 |
| frozen | 88.7% | 102/115 |
| lr1e-3 | 84.3% | 97/115 |
| scratch | 82.6% | 95/115 |

Train accuracy is 457/457, 455/457, 444/457, 442/457 in the same order.

## How much noise the setup has

`run.py` seeds only the split. The per-epoch shuffling and the new last layer's
initial weights use torch's unseeded global generator, so the same command does
not print the same accuracy twice. Running the first three commands a second
time moved test accuracy by +2.6 (+3 images), +1.7 (+2) and +3.5 (+4) points.

Consequence for the write-up: differences of less than about four test images
are not evidence of anything. `run` (106/115) against `frozen` (102/115) is
therefore a tie. Pretraining against no pretraining (106 against 95, and the
scratch loss curve rising) is not.

## Parameter counts

`11,178,564 - 2,052 = 11,176,512`, which is ResNet18 without its `fc` layer.
The new head is `512*4 + 4 = 2,052` parameters, 0.018% of the model.

## Draft answers to the four "Write this down" boxes in Problem 3

1. The loss curve. In the `run` curve train loss falls every epoch: 0.8494,
   0.1486, 0.0485, ... 0.0054 at epoch 10. It does not flatten, it keeps going
   down, but test loss stops falling at epoch 4 (0.2505) and drifts up to 0.2822
   by epoch 10, while test accuracy stops improving at epoch 4 as well (92.2%)
   and stays there for epochs 5 to 10. Epochs 5 to 10 bought nothing. In the
   `scratch` curve test loss never settles below about 0.52 and jumps to 1.2557
   at epoch 7 while train accuracy reaches 98.9%: fitting the training set.
2. The gap. 100.0% train against 92.2% test is 7.8 points, that is, all 457
   training images right against 9 of 115 test images wrong. Meaning: the model
   can memorise 457 pictures of four visually distinct stones, and test accuracy
   measures what it can do on pictures it has not seen.
3. The confusion matrix. `results/run_confusion.png` draws the counts inside the
   squares, and `src/show_confusion.py --tag run` printed these same numbers
   from `results/run_model.pt` in Colab (same split, `seed 0`, 115 test
   pictures, so picture and numbers agree):

   ```
                     amethyst   aventurine      citrine  rose_quartz      total
   amethyst                23            2            0            2         27
   aventurine               0           25            1            2         28
   citrine                  0            0           30            0         30
   rose_quartz              2            0            0           28         30
                           25           27           31           32        115
   ```

   The 9 wrong ones, all of them once or twice: amethyst -> aventurine 2,
   amethyst -> rose_quartz 2, aventurine -> citrine 1, aventurine ->
   rose_quartz 2, rose_quartz -> amethyst 2. Per class recall: amethyst 23/27
   (85%), aventurine 25/28 (89%), citrine 30/30 (100%), rose_quartz 28/30
   (93%). No single direction is ahead: 2 is the largest count and four
   directions reach it, so which pair looks "most" mixed up depends on whether
   the two directions of a pair are added (amethyst/rose_quartz 4 and
   aventurine/rose_quartz 4 against amethyst/aventurine 2 and
   aventurine/citrine 1). Citrine is never the true class of a mistake, and it
   ends with one more prediction than it has pictures (31 against 30).

   Which two categories that is, and whether it surprises me. My final answer,
   with spellings fixed (`thoguht` to `thought`, `comapred` to `compared`,
   `turining` to `turning`) and the aventurine clause reworded as I asked:

   > The categories that got mixed up and surprised me was amethyst turning out
   > as aventurine twice. That is because purple is very different from green, so
   > I thought they wouldn't get mixed. Aventurine was mixed up for rose quartz
   > also twice but that surprised me less compared to the amethyst turning out
   > as aventurine, because rose quartz can be lighter in color, which makes it
   > more similar to the light green of aventurine. I wasn't surprised about
   > amethyst and rose quartz to get mixed up due to their similar colors.

   Agent's check, not my words: this agrees with the matrix in point 3. Amethyst
   to aventurine 2 and aventurine to rose quartz 2 both appear there, and it is
   amethyst with rose quartz that is the pair it mixes up most, 4 of the 9
   mistakes, through both directions. The sentence does not say the last part
   out loud, that the pair I was not surprised about is also the biggest, 4
   against 2. If wanted, it can open with one extra clause: "Amethyst and rose
   quartz is the pair it mixes up most, 4 of the 9 mistakes, and I was not
   surprised, their colors are close."
4. ImageNet against random, same code, data, epochs, lr: 92.2% against 82.6%,
   11 test images apart, and the scratch test loss rises as its train accuracy
   approaches 100%. The pretrained features already carry most of what
   separates coloured quartz; the random network has to learn everything from
   457 photographs.
5. Only the last layer trained: `2,052 / 11,178,564 = 0.018%` of the
   parameters, 5,445 times fewer, trained in 0.1 minutes instead of 0.3, and it
   reaches 88.7% against 92.2% for training everything. Within noise of the best
   run, with a smaller train/test gap (97.2 against 100.0) and a curve that
   falls smoothly with no jump.
6. The fourth setting is `lr1e-3`: the default run with the learning rate ten
   times larger. Test accuracy 84.3% against 92.2%, and its test loss is
   erratic, 16.8645 at epoch 1, 1.8993 at epoch 4 and 1.4221 at epoch 9, while
   the run at 0.0001 keeps test loss under 0.33 the whole way. A learning rate
   large enough for a frozen backbone pulling one fresh layer into place is too
large when all 11 million parameters can move.

## Problem 4. Cleaning

### The rule, as I wrote it before I ran anything

Given to the agent on 13 October 2026, while `data/removed/` was still empty: no
`clean.py remove` command had been run when this was written down. The wording
below is mine and is not tidied.

> My rules:
> I remove images that don't show a crystal at all
> I remove images that show drawings
> I remove images that show jewellery where the crystal is not predominant
> I remove images that has text and that take much space in the photo.
> I remove images that don't show clearly the crystal or not in the right direction.
> I remove images that has more than one type of crystal
> I remove images that show the wrong crystal.

Seven clauses. The command that applies them takes one `--reason` string per
clause, shorter than the sentence above, and `clean.py count` groups by that
exact string, so the string used in the log is written here too.

| clause (as written above) | `--reason` string put in the log | files | classes |
|---|---|---|---|
| doesn't show a crystal at all | `The image doesn't show a crystal at all` | 86 | amethyst 12, aventurine 45, rose_quartz 29 |
| show drawings | `The image is a drawing` | 2 | amethyst 2 |
| jewellery, crystal not predominant | `The image shows jewelry where the crystal is not predominant` | 22 | amethyst 9, aventurine 3, rose_quartz 10 |
| text taking much space | `The image has text and that take much space of the photo` | 25 | aventurine 16, citrine 7, rose_quartz 2 |
| not shown clearly / wrong direction | `The image doesn't show clearly the crystal, or not in the right direction` | 10 | amethyst 6, aventurine 2, rose_quartz 2 |
| more than one type of crystal | `The image has more than one type of crystal` | 18 | amethyst 1, aventurine 8, citrine 4, rose_quartz 5 |
| the wrong crystal | `The image shows the wrong crystal` | 25 | amethyst 8, aventurine 7, citrine 1, rose_quartz 9 |
| | **total** | **188** | amethyst 38, aventurine 81, citrine 12, rose_quartz 57 |

### The kinds of junk I found

Mine, as I wrote it down: mostly unrelated objects such as clothes, car
accessories, logos, drawings. I also found characters and wrong crystals.

Four kinds were named and the report asks for three, each with one picture.
These are the three, settled on 13 October 2026. Each file was already removed
by one of the clauses above, so it is waiting in `data/removed/<class>/` to be
copied into the report's figures:

| kind in the report | picture | the clause that removed it |
|---|---|---|
| not a crystal at all (clothes, car accessories, logos, characters) | `aventurine/0102.jpg` | doesn't show a crystal at all |
| a drawing rather than a photo | `amethyst/0118.jpg` | show drawings |
| the wrong crystal | `aventurine/0110.jpg` | the wrong crystal |

The three further pictures I first put forward are not used:
`amethyst/0123.jpg`, `amethyst/0131.jpg`, `rose_quartz/0109.jpg`.

### What was removed, by class

`clean.py count` on 14 October 2026, in `results/clean_count.txt`:

| class | downloaded | removed | kept | other |
|---|---|---|---|---|
| amethyst | 134 | 40 | 94 | 0 |
| aventurine | 138 | 83 | 55 | 0 |
| citrine | 150 | 17 | 133 | 0 |
| rose_quartz | 150 | 58 | 92 | 0 |

and the same removals by reason, seven rows from my rule and one from the
suspect pass:

| images | reason |
|---|---|
| 86 | The image doesn't show a crystal at all |
| 25 | The image shows the wrong crystal |
| 25 | The image has text and that take much space of the photo |
| 22 | The image shows jewelry where the crystal is not predominant |
| 18 | The image has more than one type of crystal |
| 10 | The image doesn't show clearly the crystal, or not in the right direction |
| 10 | The image is a near copy of another picture |
| 2 | The image is a drawing |

198 images removed and 374 kept of 572. The seven rule reasons add to 188, the
figure the seven commands moved, and the reason strings are spelled the same
every time, so this line groups the removals the tool would otherwise only know
by file name. Every class's `other` column is 0: no image left `data/raw` except
through `clean.py remove`, and every removal has a reason written down.

Aventurine is the class the cleaning changes most, 83 of its 138 images gone,
60%, and citrine the least, 17 of 150. That is what the class pages showed: the
aventurine search returned far more beads, bracelets and jewellery than the
other three.

### The suspect sheets against my rule, per class

The suspect pass ran on all 572 images before any removal, so these numbers are
about the data as downloaded. Each sheet draws the 32 images of a class that
look least like the rest of their class, and
`results/cleaning/suspects/suspects.csv` carries a row for every image with its
rank, rank 1 being the least typical.

| class | removed by my rule | of those, rank 1-20 | rank 21-32 | rank 33 and later |
|---|---|---|---|---|
| amethyst | 38 | 11 | 6 | 21 |
| aventurine | 81 | 15 | 9 | 57 |
| citrine | 12 | 4 | 0 | 8 |
| rose_quartz | 57 | 15 | 6 | 36 |

What the first 20 of each class went by:

- amethyst: no crystal 5, jewellery 3, drawing 1, unclear 1, wrong crystal 1
- aventurine: no crystal 9, wrong crystal 2, jewellery 1, more than one 1,
  unclear 1, text 1
- citrine: text 2, more than one 2
- rose_quartz: no crystal 5, jewellery 4, more than one 4, wrong crystal 1, text 1

Reading: the images that look least like the rest of their class are mostly junk
by my rule too, most strongly in aventurine and rose quartz, which are also the
two classes my rule removed the most from. Citrine is where the two views
disagree most, 4 of 20, and aventurine is where I went furthest on my own: 57 of
its 81 removals sit at rank 33 or later, in pictures the sheet never showed me.

"Removed but not on the suspect list at all" is always 0 and says nothing, since
`suspects.csv` has a rank for all 572 images. The number that answers "did you
find junk it did not list" is the rank 33 and later column, 21 / 57 / 8 / 36.

### Near copies

The suspect pass found **27 pairs** above 0.95 similarity.

16 of them were settled by rule, because both halves were junk under one of my
seven clauses and had already gone. That covers the amethyst tail: `0123`,
`0124`, `0126`, `0127` and `0128` are near copies of each other, so the run I
removed under "doesn't show a crystal at all" was a burst of near-identical
photos and removing it as junk took the duplicates with it.

The other 9 groups, 19 pictures, were still in `data/clean` and I decided them
one by one on the `copies.png` sheet, keeping the better picture of each group
and removing the rest under one new reason, "The image is a near copy of another
picture".

| kept | the near copies removed |
|---|---|
| `citrine/0100.jpg` | `citrine/0018.jpg` |
| `citrine/0149.jpg` | `citrine/0032.jpg` |
| `citrine/0006.jpg` | `citrine/0069.jpg` |
| `citrine/0050.jpg` | `citrine/0099.jpg` |
| `citrine/0083.jpg` | `citrine/0041.jpg` |
| `rose_quartz/0144.jpg` | `rose_quartz/0150.jpg` |
| `amethyst/0033.jpg` | `amethyst/0055.jpg` |
| `amethyst/0022.jpg` | `amethyst/0031.jpg` |
| `aventurine/0134.jpg` | `aventurine/0123.jpg`, `aventurine/0132.jpg` |

Ten images removed, one kept of each group, decided on 13 October 2026.

For the report, in one sentence: the suspect pass found 27 pairs of images above
0.95 similarity, 16 of them already removed as junk by my own rule, and of the
remaining nine groups I kept a single picture each and removed the other ten.

### Still to fill in for Problem 4

- The class and reason tables are in the section above, from
  `results/clean_count.txt`, and every class's `other` column is 0.
- The first 20 suspects per class, and the junk the suspect sheets never showed
  me, are in the section above, from the Colab run of 13 October 2026.
- The near copies are decided and written above.

## Problem 5. Images from a new source

Source: `src/clean.py` lines 364-415, run after all 198 removals, with `data/raw`,
`data/clean` and `data/removed` all still on disk. Output, in
`results/overlap.txt`:

    none of your 21 new images is a near copy of any of the 570 images you
    downloaded

    the closest any new image comes to a downloaded one: 0.85 (near copies are
    above 0.95)

Where the new images came from: photographs I took myself for this assignment,
with my own phone, saved as JPEG because the phone's HEIC files cannot be read
by the code (one of them, `data/new_images/aventurine/IMG_3068.JPG`, is the
photo measured in Problem 2). They are 21, five per class and six rose quartz,
in `data/new_images/<class>/`.

Why none of them can be among the downloads: they are photographs of objects in
front of me, taken by me, while the four classes were downloaded from a search
engine; a search could not return a photograph that never existed on the web.
The overlap check tests that rather than assuming it: every new image is
described and compared with all 572 downloaded files, including the 198 moved to
`data/removed/`, and the closest any of the 21 comes to any of them is 0.85,
under the 0.95 the tool calls a near copy. So the new images are a source that
cannot overlap with the downloads, which is what Problem 5 needs.

The tool prints 570 rather than 572 because it hashes every file and counts each
picture once; two of the 572 downloaded files are byte-for-byte copies of
another file in the set.

- TO FILL IN: accuracy on the downloaded test set and on the new images, side by
  side, from `check.py --compare run clean`.
- TO FILL IN: the five mistakes it was most sure about on the new images, with
  the pictures, and what in each image pushed it the wrong way.
- TO FILL IN: what is different about the new images: background, lighting,
  angle, distance, what else is in the frame.
- TO FILL IN: test accuracy (and accuracy on the new images) before cleaning
  92.2% and after, from `check.py --compare run clean`.