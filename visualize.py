import matplotlib.pyplot as plt
import pandas as pd
import datetime as dt
import os
import matplotlib.transforms as mtransforms
from matplotlib.axes import Axes

plt.ion()

# PREPROCESS SCORES DF
EXCLUDED_USERS = ["ESPNFAN8452492966"]

NAME_MAPPER = {
    "ESPNFAN4288357771's Picks 1": "John's Picks",
    "ESPNFAN8630827724's Picks 1": "Jarron's Picks",
    "ESPNFAN7873704290's Picks 1": "Ritu's Picks",
}

# Get Scores Data
scores_dir = os.listdir("outputs/")
scores = []
for score in scores_dir:
    df = pd.read_csv(
        "outputs/" + score,
        index_col=["entry_user", "time"],
        parse_dates=["time"],
    )

    df = df.loc[~df.index.get_level_values("entry_user").isin(EXCLUDED_USERS)]

    scores.append(df)
scores = pd.concat(scores).sort_index()
scores.loc[:, "entry_name"] = scores.entry_name.map(NAME_MAPPER).where(
    scores.entry_name.isin(NAME_MAPPER), scores.entry_name
)

desired_time_range = pd.date_range(
    scores.index.get_level_values("time").min(),
    scores.index.get_level_values("time").max(),
    freq="H",
)

desired_index = pd.MultiIndex.from_product(
    [scores.index.get_level_values("entry_user").unique(), desired_time_range],
    names=["entry_user", "time"],
)

scores = (
    scores.align(pd.DataFrame([], index=desired_index))[0]
    .groupby(level=["entry_user"])
    .ffill()
)

# TODO: Customize this
no_games_mask = scores.index.get_level_values("time").to_series().ge(
    dt.datetime(2024, 3, 25, 12)
) & scores.index.get_level_values("time").to_series().le(dt.datetime(2024, 3, 28, 20))

scores = scores.loc[~no_games_mask.values]
# END PREPROCESS SCORES DF

# Create the Plot
ax: Axes
fig, ax = plt.subplots(1, 1, figsize=(12, 8))

# Create Labels
current_scores = scores.groupby(
    scores.index.get_level_values("entry_user")
).current_points.max()
users_by_score = (
    current_scores.reset_index().groupby("current_points").agg(list).entry_user
)

# Sort by Score
scores = scores.loc[users_by_score.apply(lambda lst: lst[::-1]).explode()[::-1]]


def get_label(users):
    if len(users) == 1:
        return scores.loc[users[0], "entry_name"].iloc[
            0
        ], mtransforms.ScaledTranslation(1 / 12, -1 / 24, fig.dpi_scale_trans)
    elif len(users) > 1:
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

# Plot each line separately
for i, entry_user in enumerate(scores.index.get_level_values("entry_user").unique()):
    ax.plot(
        range(scores.loc[entry_user].index.size),
        scores.current_points.loc[entry_user],
        label=scores.entry_name.loc[entry_user].iloc[-1],
    )

# Add the labels
for value, (label, transform) in labels.items():
    ax.text(
        scores.index.get_level_values("time").nunique(),
        value,
        label,
        color="black",
        transform=ax.transData + transform,
        fontsize=8,
        clip_box=ax.clipbox,
        clip_on=True,
    )

# Add Text
ax.set_title("March Madness Bracket Scores", ha="center")
ax.set_xlabel("Time", fontweight="bold")
ax.set_ylabel("Score", fontweight="bold")

# Change Ticks
all_times = scores.index.get_level_values("time").unique()

jump_date = dt.datetime(2024, 3, 28, 20)
vline_loc = (all_times >= jump_date).argmax()
max_points = scores.current_points.max(0)
ax.vlines(vline_loc, 0, max_points, colors="k", linestyles="--", lw=2)
ax.text(
    vline_loc - 8,
    560,
    "Fast forward to\nSweet 16",
    color="black",
    fontweight="bold",
    fontsize=10,
    ha="center",
    clip_box=ax.clipbox,
    clip_on=True,
)

# TODO: Customize this
rng = range(0, len(all_times), 12)
xtick_times = all_times[rng]
xticklabels = xtick_times.map(lambda date: date.strftime("%H:00\n%m-%d"))

ax.set_xticks(rng)
ax.set_xticklabels(xticklabels)
ax.set_yticks(range(0, int(scores.current_points.max()) + 1, 40))

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

# ax.legend(bbox_to_anchor=(1.15, 1.05))
plt.show()

# Interactive
ax.set_autoscale_on(True)

for i, t in enumerate(all_times):
    ax.set_xlim(0, i)
    ax.set_ylim(0, scores.loc[(slice(None), t), "current_points"].max() + 10)

    # Need both of these in order to rescale
    ax.relim()
    ax.autoscale_view()
    # We need to draw *and* flush
    fig.canvas.draw()
    fig.canvas.flush_events()

    fig.savefig(f"gif-frames/{i:03}.png", bbox_inches="tight")
