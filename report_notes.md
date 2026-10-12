# Report notes, gathered as the runs happen

Evidence only. Every number here was printed by code that was actually run;
the source line is named next to each block. This file feeds
`long_report/long_report.tex` at Step 19.

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