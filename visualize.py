import matplotlib.pyplot as plt
import pandas as pd
import os
import matplotlib.transforms as mtransforms


# Get Scores Data
scores_dir = os.listdir("outputs/")
scores = []
for score in scores_dir:
    df = pd.read_csv(
        "outputs/" + score,
        index_col=["entry_user", "time"],
        parse_dates=["time"],
    )
    scores.append(df)
scores = pd.concat(scores).sort_index()

# Create the Plot
fig, ax = plt.subplots(1, 1, figsize=(12, 8))

# Plot each line separately
for i, entry_user in enumerate(scores.index.get_level_values("entry_user")):
    ax.plot(scores.loc[entry_user].index, scores.current_points.loc[entry_user])

# Create Labels
current_scores = scores.groupby(
    scores.index.get_level_values("entry_user")
).current_points.max()
users_by_score = (
    current_scores.reset_index().groupby("current_points").agg(list).entry_user
)


def get_label(users):
    if len(users) == 1:
        return users[0], mtransforms.ScaledTranslation(
            1 / 12, -1 / 24, fig.dpi_scale_trans
        )
    elif len(users) > 3:
        return f"{len(users)}-way tie", mtransforms.ScaledTranslation(
            1 / 12, -1 / 24, fig.dpi_scale_trans
        )
    else:
        max_time = scores.index.get_level_values("time").max()
        entry_names = scores.loc[users].loc[(slice(None), max_time), "entry_name"]
        return "\n".join(entry_names), mtransforms.ScaledTranslation(
            1 / 12, -1 / 15 * len(users), fig.dpi_scale_trans
        )


labels = users_by_score.apply(get_label)

# Add the labels
for value, (label, transform) in labels.items():
    ax.text(
        scores.index.get_level_values("time").max(),
        value,
        label,
        color="black",
        transform=ax.transData + transform,
    )

# Add Text
ax.set_title("March Madness Bracket Scores", ha="center")
ax.set_xlabel("Time", fontweight="bold")
ax.set_ylabel("Score", fontweight="bold")

# Change Ticks
all_times = scores.index.get_level_values("time").unique()
xticklabels = all_times.map(lambda date: date.strftime("%H:00\n%m-%d"))

ax.set_xticks(all_times)
ax.set_xticklabels(xticklabels)
ax.set_yticks(range(0, scores.current_points.max() + 1, 10))

ax.xaxis.tick_bottom()
ax.yaxis.tick_left()
ax.grid(True, "major", "both")
ax.tick_params(
    axis="both",
    which="both",
    labelsize="large",
    bottom=False,
    top=False,
    labelbottom=True,
    left=False,
    right=False,
    labelleft=True,
)

# Show/Save the plot
fig.savefig("mm.png", bbox_inches='tight')
plt.show()
