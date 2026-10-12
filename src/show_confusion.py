"""Print the numbers behind results/<tag>_confusion.png, so they are not only in a picture.

Problem 3 asks which two categories the confusion matrix mixes up most, and
Problem 4 asks the same question again after cleaning. `run.py` draws that
matrix into `results/<tag>_confusion.png` with the counts written inside the
squares (`plot_confusion`), but it never prints them, so the numbers exist only
inside a picture. This prints the same matrix as numbers, from the model
`run.py` saved, so the report can quote numbers that came out of code.

    python src/show_confusion.py --tag run
    python src/show_confusion.py --tag clean | tee results/clean_confusion.txt

It reloads `results/<tag>_model.pt` and repeats the split `run.py` used
(`--test-ratio 0.2 --seed 0`, both of run.py's defaults), so the numbers printed
are the ones in the picture for that tag and come out the same every time. If a
run was made with other settings, pass the same `--test-ratio` and `--seed`.

It takes no arguments of its own beyond these, and nothing else in the
repository works this way: on your own computer run it through uv like every
other command. On an Intel Mac uv cannot install PyTorch at all ("The current
Python platform is not compatible with the lockfile's supported environments"),
so there, and in Colab, run the same command with `!python` after the cell in
section 3:

    !python src/show_confusion.py --tag run
"""

import argparse
from pathlib import Path

import numpy as np

from data import load_folder, split_train_test
from evaluate import accuracy, confusion_matrix
from train import load

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--tag", default="run",
                        help="which saved model, results/<tag>_model.pt")
    parser.add_argument("--data", default=str(ROOT / "data" / "clean"),
                        help="the folder the model was trained on")
    parser.add_argument("--test-ratio", type=float, default=0.2,
                        help="must match the run.py call that made this model")
    parser.add_argument("--seed", type=int, default=0,
                        help="must match the run.py call that made this model")
    args = parser.parse_args()

    model_path = ROOT / "results" / f"{args.tag}_model.pt"
    if not model_path.is_file():
        raise SystemExit(f"no saved model at {model_path.relative_to(ROOT)}: run "
                         f"`python src/run.py --tag {args.tag}` (and export it "
                         f"for the page) first")

    X, y, class_names, paths = load_folder(args.data)
    _, _, _, X_test, y_test, _ = split_train_test(
        X, y, paths, test_ratio=args.test_ratio, seed=args.seed
    )
    model = load(model_path)
    matrix = confusion_matrix(model, X_test, y_test, len(class_names))

    right = int(np.trace(matrix))
    print(f"{model_path.relative_to(ROOT)}, tested on {len(X_test)} pictures "
          f"({args.test_ratio:.0%} of the {len(X)} in {Path(args.data).name}):")
    print(f"test accuracy {accuracy(model, X_test, y_test):.1%} is "
          f"{right} of {len(X_test)} right, {len(X_test) - right} wrong\n")

    width = max(len(name) for name in class_names) + 2
    column = max(len(name) for name in class_names) + 2
    print(" " * width + "".join(f"{name:>{column}}" for name in class_names)
          + f"{'total':>11}")
    for i, name in enumerate(class_names):
        counts = "".join(f"{int(matrix[i][j]):>{column}}" for j in range(len(class_names)))
        print(f"{name:<{width}}{counts}{int(matrix[i].sum()):>11}")
    print(" " * width + "".join(f"{int(matrix[:, j].sum()):>{column}}"
                                for j in range(len(class_names)))
          + f"{len(X_test):>11}")
    print("row is the true class, column is what the model said, so the diagonal "
          "is the ones it got right")

    outside = matrix.copy()
    np.fill_diagonal(outside, 0)
    if outside.max() == 0:
        print("\nnothing is mixed up: every picture is on the diagonal")
        return
    true_class, said = np.unravel_index(int(np.argmax(outside)), outside.shape)
    share = outside[true_class, said] / max(1, int(matrix[true_class].sum()))
    print(f"\nmost mixed up: {class_names[true_class]} called "
          f"{class_names[said]} {int(outside[true_class, said])} "
          f"time{'s' if outside[true_class, said] != 1 else ''}, which is "
          f"{share:.0%} of the {class_names[true_class]} in the test set")
    print("per class: " + ", ".join(
        f"{name} {matrix[i, i]}/{int(matrix[i].sum())} "
        f"({matrix[i, i] / max(1, int(matrix[i].sum())):.0%})"
        for i, name in enumerate(class_names)))


if __name__ == "__main__":
    main()