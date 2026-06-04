import csv
import os

import matplotlib.pyplot as plt


ALGORITHMS = ["fedavg", "fedprox", "scaffold"]
COLORS = {"fedavg": "#378ADD", "fedprox": "#1D9E75", "scaffold": "#D85A30"}


def load_loss_csv(algorithm):
    fname = f"training_loss_{algorithm}.csv"
    if not os.path.exists(fname):
        return [], []

    rounds = []
    losses = []
    with open(fname, newline="") as f:
        for row in csv.DictReader(f):
            rounds.append(int(row["round"]))
            losses.append(float(row["loss"]))
    return rounds, losses


def plot():
    fig, ax = plt.subplots(figsize=(9, 5))
    for algorithm in ALGORITHMS:
        rounds, losses = load_loss_csv(algorithm)
        if not rounds:
            continue
        ax.plot(
            rounds,
            losses,
            label=algorithm.upper(),
            color=COLORS[algorithm],
            linewidth=2,
            marker="o",
            markersize=3,
        )

    ax.set_xlabel("Communication round")
    ax.set_ylabel("Training loss (MSE)")
    ax.set_title("Training loss per algorithm")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("training_loss_comparison.png", dpi=150)
    plt.show()


if __name__ == "__main__":
    plot()
