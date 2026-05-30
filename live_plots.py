import os
import pandas as pd
import matplotlib.pyplot as plt
import time
from dotenv import dotenv_values

env = dotenv_values(".env")
max_rounds = int(env.get("FED_CONFIG_R", 20))  # read number of rounds
print(f"Max rounds set to: {max_rounds}")

# Configuration
clients = {
    "flclient-1": {
        "path": "./Output/flclient-1/anomaly_detection.csv",
        "color": "blue",
        "anomaly_color": "red"
    },
    "flclient-2": {
        "path": "./Output/flclient-2/anomaly_detection.csv",
        "color": "orange",
        "anomaly_color": "green"
    },
    "flclient-3": {
        "path": "./Output/flclient-3/anomaly_detection.csv",
        "color": "purple",
        "anomaly_color": "brown"
    }
}

file_check_interval = 0.05  # seconds between checks

def read_csv_rows_incrementally(file_path, last_row_read):
    try:
        df = pd.read_csv(file_path)
        if last_row_read < len(df):
            return df.iloc[last_row_read:], len(df)
        return pd.DataFrame(), len(df)
    except Exception:
        return pd.DataFrame(), last_row_read

# Wait until all files exist
print("Waiting for all client CSV files to appear...")
while not all(os.path.exists(cfg["path"]) for cfg in clients.values()):
    time.sleep(1)
print("All files detected. Starting plot...")

# Initialize plot
plt.ion()
fig, ax = plt.subplots(figsize=(14, 6))
ax.set_title("Live Updating MSE vs Threshold")
ax.set_xlabel("Epochs")
ax.set_ylabel("MSE")
ax.grid(True)

# State per client
plot_data = {}
for name, cfg in clients.items():
    plot_data[name] = {
        "x": [],
        "mse": [],
        "thresh": [],
        "anomaly_x": [],
        "anomaly_y": [],
        "last_row_read": 0,
        "index": 0,
        "last_mtime": 0,
        "last_model": None,
        "line_mse": ax.plot([], [], label=f"{name} MSE", color=cfg["color"])[0],
        "line_thresh": ax.plot([], [], label=f"{name} Threshold", color=cfg["color"], linestyle="--")[0],
        "scatter": ax.scatter([], [], color=cfg["anomaly_color"], marker='o', label=f"{name} Anomaly")
    }

ax.legend()


training_finished_line_drawn = False

while True:
    y_max = 0
    for name, cfg in clients.items():
        data = plot_data[name]
        file_path = cfg["path"]

        if not os.path.exists(file_path):
            continue

        current_mtime = os.path.getmtime(file_path)

        # If the file was reset (mod time or shrinking row count)
        if current_mtime < data["last_mtime"]:
            print(f"File for {name} reset. Clearing previous data.")
            # Reset plot data
            data.update({
                "x": [],
                "mse": [],
                "thresh": [],
                "anomaly_x": [],
                "anomaly_y": [],
                "last_row_read": 0,
                "index": 0,
                "last_model": None
            })

            # Clear plot
            data["line_mse"].set_data([], [])
            data["line_thresh"].set_data([], [])
            data["scatter"].remove()
            data["scatter"] = ax.scatter(
                data["anomaly_x"], data["anomaly_y"],
                color=cfg["anomaly_color"], marker='o', label=f"{name} Anomaly"
            )
            ax.legend()

        new_data, new_last_row = read_csv_rows_incrementally(file_path, data["last_row_read"])

        if not new_data.empty:
            for _, row in new_data.iterrows():
                current_model = int(row["MODEL VERSION"])

                data["x"].append(data["index"])
                data["mse"].append(row["DETECTED MSE"])
                data["thresh"].append(row["MSE THRESHOLD"])

                if row["IS ANOMALY"]:
                    data["anomaly_x"].append(data["index"])
                    data["anomaly_y"].append(row["DETECTED MSE"])

                # Add vertical lines for rounds
                if data["last_model"] is not None and current_model != data["last_model"]:
                    if current_model < max_rounds:
                        ax.axvline(data["index"], color="yellow", linestyle=":", linewidth=0.8)
                        ax.text(data["index"], 0.95, f"Round {current_model}",
                                rotation=90, fontsize=8, color="gray", fontweight="bold", va='top', ha='left', transform=ax.get_xaxis_transform())
                    elif not training_finished_line_drawn and current_model == max_rounds:
                        # Draw "Training Finished" line only once
                        ax.axvline(data["index"], color="red", linestyle="--", linewidth=1.2)
                        ax.text(data["index"] + 1, 0.95, "Training Finished",
                                rotation=90, fontsize=9, color="red", fontweight="bold", va='top', ha='left', transform=ax.get_xaxis_transform())
                        training_finished_line_drawn = True

                data["last_model"] = current_model
                data["index"] += 1

            # Update line data
            data["line_mse"].set_data(data["x"], data["mse"])
            data["line_thresh"].set_data(data["x"], data["thresh"])
            data["scatter"].remove()
            data["scatter"] = ax.scatter(
                data["anomaly_x"], data["anomaly_y"],
                color=cfg["anomaly_color"], marker='o', label=f"{name} Anomaly"
            )

            data["last_row_read"] = new_last_row

        data["last_mtime"] = current_mtime

        # Update max Y for scaling
        if data["mse"] or data["thresh"] or data["anomaly_y"]:
            y_max = max(y_max, max(data["mse"] + data["thresh"] + data["anomaly_y"]))

    # Update plot limits
    max_index = max((d["index"] for d in plot_data.values()), default=10)
    ax.set_xlim(0, max(10, max_index))
    ax.set_ylim(0, y_max * 1.1 if y_max > 0 else 1)
    ax.legend()
    plt.pause(0.5)

    time.sleep(file_check_interval)
