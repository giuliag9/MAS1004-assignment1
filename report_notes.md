# Report notes, gathered as the runs happen

Evidence only. Every number here was printed by code that was actually run;
the source line is named next to each block. This file feeds
`long_report/long_report.tex` at Step 19.

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
3. The confusion matrix. `results/run_confusion.png`, and the numbers printed by
   the snippet in `results/` -> TO FILL IN.
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