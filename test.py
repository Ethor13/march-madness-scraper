import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime as dt

plt.ion()


def initialize_data():
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
    ) & scores.index.get_level_values("time").to_series().le(
        dt.datetime(2024, 3, 28, 20)
    )

    scores = scores.loc[~no_games_mask.values]

    return scores.reset_index().pivot(
        index=["entry_name"], columns=["time"], values="current_points"
    )


class DynamicUpdate:
    # Suppose we know the x range
    min_x = 0
    max_x = 10

    def on_launch(self):
        # Set up plot
        self.figure, self.ax = plt.subplots()
        (self.lines,) = self.ax.plot([], [])
        # Autoscale on unknown axis and known lims on the other
        self.ax.set_autoscaley_on(True)
        self.ax.set_xlim(self.min_x, self.max_x)
        # Other stuff
        self.ax.grid()
        ...

    def on_running(self, xdata, ydata):
        # Update data (with the new _and_ the old points)
        self.lines.set_xdata(xdata)
        self.lines.set_ydata(ydata)
        # Need both of these in order to rescale
        self.ax.relim()
        self.ax.autoscale_view()
        # We need to draw *and* flush
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

    # Example
    def __call__(self):
        import numpy as np
        import time

        self.on_launch()
        xdata = []
        ydata = []
        for x in np.arange(0, 10, 0.5):
            xdata.append(x)
            ydata.append(np.exp(-(x**2)) + 10 * np.exp(-((x - 7) ** 2)))
            self.on_running(xdata, ydata)
            time.sleep(0.1)
        return xdata, ydata


d = DynamicUpdate()
d()
