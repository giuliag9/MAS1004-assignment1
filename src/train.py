"""Build a model and train it. YOU write the bodies of these functions.

The model is ResNet18, a convolutional network that was already trained on
ImageNet, 1.2 million photographs of 1,000 kinds of thing. You keep everything
it learned there and replace only its last layer, so that it answers with your
categories instead of those 1,000. Then you train it further on your images.

Run `pytest tests/test_train.py` after you fill them in. The first run
downloads the ImageNet weights, about 45 MB.
"""

import torch
import torch.nn as nn
from torchvision.models import ResNet18_Weights, resnet18


def build_model(num_classes, pretrained=True, freeze=False):
    """Return a ResNet18 whose last layer has `num_classes` outputs.

    Arguments
        num_classes  int, how many categories you have
        pretrained   True: start from the ImageNet weights,
                     torchvision.models.ResNet18_Weights.IMAGENET1K_V1.
                     False: start from random numbers, as if ImageNet had
                     never happened. You need this for the comparison in
                     Problem 3.
        freeze       True: only the new last layer is trained. Every other
                     parameter keeps the value it came with, which you do by
                     setting requires_grad to False on it.
                     False: every parameter is trained.

    Returns the model from torchvision.models.resnet18, with its `fc`
    attribute replaced by a new nn.Linear that has 512 inputs and num_classes
    outputs.

    Do not put a softmax at the end. The loss function adds it for you, and the
    web page adds it for you.
    """
    weights = ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
    model = resnet18(weights=weights)

    # Replace only the last layer, so the model answers with your categories
    # instead of the 1,000 ImageNet ones. No softmax: CrossEntropyLoss adds it
    # for training, and the web page adds it at prediction time.
    model.fc = nn.Linear(512, num_classes)

    if freeze:
        for parameter in model.parameters():
            parameter.requires_grad = False
        for parameter in model.fc.parameters():
            parameter.requires_grad = True

    return model


def train(model, X_train, y_train, X_test, y_test,
          epochs=10, lr=1e-4, batch_size=32):
    """Train the model and report what happened at every epoch.

    Arguments
        model        what build_model returned, or any other torch model
        X_train      np.float32 (N, ...)      y_train  np.int64 (N,)
        X_test       np.float32 (M, ...)      y_test   np.int64 (M,)
        epochs       int, how many times to go through the training set
        lr           float, the learning rate
        batch_size   int, how many rows per step

    Returns a dict named history with four keys. Each value is a list of
    `epochs` numbers, one per epoch:
        "train_loss"  the mean loss over the batches of that epoch
        "train_acc"   the share of training rows the model got right in those
                      batches, between 0.0 and 1.0
        "test_loss"   the mean loss over the test set, measured after the epoch
        "test_acc"    the share of the test set it gets right, measured after
                      the epoch, between 0.0 and 1.0

    What to do
        Use a GPU when there is one:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        Move the model there once, and each batch there as you use it. Keep
        X_train and X_test themselves in ordinary memory: they may not fit on
        the GPU.
        Shuffle the training rows again at the start of every epoch.
        Use nn.CrossEntropyLoss, which expects raw outputs, and torch.optim.Adam
        over the parameters that have requires_grad set.
        Call model.train() before the training batches and model.eval() before
        measuring the test set. ResNet contains BatchNorm layers, which behave
        differently in the two modes.
        Do not compute gradients while measuring the test set, and never let
        the test rows change the parameters.
        Print one line per epoch, so that you can watch it while it runs.

    The model is trained in place. When this function returns, `model` is the
    trained one, and it is left on the device it was trained on.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # Adam may only change the parameters that are allowed to change. With
    # freeze=True that is only the new last layer.
    trainable = [p for p in model.parameters() if p.requires_grad]
    optimiser = torch.optim.Adam(trainable, lr=lr)
    loss_function = nn.CrossEntropyLoss()

    # The rows stay in ordinary memory and go to the GPU one batch at a time,
    # so that a big training set does not run you out of room.
    train_X = torch.as_tensor(X_train, dtype=torch.float32)
    train_y = torch.as_tensor(y_train, dtype=torch.long)
    test_X = torch.as_tensor(X_test, dtype=torch.float32)
    test_y = torch.as_tensor(y_test, dtype=torch.long)

    history = {"train_loss": [], "train_acc": [], "test_loss": [], "test_acc": []}

    for epoch in range(1, epochs + 1):
        model.train()  # BatchNorm and Dropout behave differently in the two modes
        order = torch.randperm(len(train_X))
        losses, correct, seen = [], 0, 0

        for start in range(0, len(train_X), batch_size):
            rows = order[start:start + batch_size]
            inputs = train_X[rows].to(device)
            targets = train_y[rows].to(device)

            optimiser.zero_grad()
            outputs = model(inputs)
            loss = loss_function(outputs, targets)
            losses.append(float(loss.detach()))  # detach: loss still tracks grad
            correct += int((outputs.argmax(dim=1) == targets).sum())
            seen += len(targets)

            loss.backward()
            optimiser.step()

        test_loss, test_acc = _measure(model, test_X, test_y, loss_function,
                                       device, batch_size)
        history["train_loss"].append(sum(losses) / len(losses))
        history["train_acc"].append(correct / seen)
        history["test_loss"].append(test_loss)
        history["test_acc"].append(test_acc)

        print(f"epoch {epoch:3d}/{epochs}  "
              f"train loss {history['train_loss'][-1]:.4f}  "
              f"train acc {history['train_acc'][-1]:6.1%}  "
              f"test loss {test_loss:.4f}  "
              f"test acc {test_acc:6.1%}")

    return history


def _measure(model, X, y, loss_function, device, batch_size):
    """Mean loss and accuracy over X, without letting it change the model."""
    model.eval()
    losses, correct, seen = [], 0, 0

    with torch.no_grad():
        for start in range(0, len(X), batch_size):
            inputs = X[start:start + batch_size].to(device)
            targets = y[start:start + batch_size].to(device)
            outputs = model(inputs)
            losses.append(float(loss_function(outputs, targets)))
            correct += int((outputs.argmax(dim=1) == targets).sum())
            seen += len(targets)

    return sum(losses) / len(losses), correct / seen


def count_trainable(model):
    """How many parameters training is allowed to change. Written for you."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def save(model, path):
    """Save a trained model. Written for you."""
    torch.save(model, path)


def load(path):
    """Load a model saved by `save`, onto the CPU. Written for you."""
    model = torch.load(path, map_location="cpu", weights_only=False)
    model.eval()
    return model
