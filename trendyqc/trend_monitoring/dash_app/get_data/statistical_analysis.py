import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

VALUE_COLUMN_CANDIDATES = [
    "qc_value",
    "fold80",
]


def get_metric_value_column(df):
    """
    Try to find the column containing the metric values.
    Adjust VALUE_COLUMN_CANDIDATES if your dataframe uses a different name.
    """
    for col in df.columns[5:]:
        if col in df.columns:
            return col

    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    # Avoid choosing obvious non-metric numeric columns
    excluded = {"run_order", "days_back"}
    numeric_cols = [c for c in numeric_cols if c not in excluded]

    if len(numeric_cols) == 1:
        return numeric_cols[0]

    raise ValueError(
        "Could not identify the metric value column. "
        "Please add the correct column name to VALUE_COLUMN_CANDIDATES."
    )


def compute_linear_trend_with_ci(
    df,
    value_col,
    project_col="project_name",
    date_col="date",
    group_col=None,
    min_points=3,
):
    """
    Computes run-level median trend and 95% confidence band.

    Returns a dataframe with:
    project_name, run_order, fit, ci_lower, ci_upper, group
    """

    if df.empty:
        return pd.DataFrame()

    d = df.copy()

    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.dropna(subset=[project_col, date_col, value_col])

    if d.empty:
        return pd.DataFrame()

    # If group_col exists, calculate separate trend lines per group.
    # Otherwise calculate one overall trend line.
    if group_col and group_col in d.columns:
        group_cols = [group_col, project_col, date_col]
    else:
        group_col = None
        group_cols = [project_col, date_col]

    # Use median per run. This matches the visual logic of boxplots.
    run_summary = d.groupby(group_cols, as_index=False).agg(
        median_value=(value_col, "median"),
        n_samples=(value_col, "size"),
    )

    trend_frames = []

    if group_col:
        grouped = run_summary.groupby(group_col)
    else:
        grouped = [(None, run_summary)]

    for group_name, g in grouped:
        g = g.sort_values(date_col).reset_index(drop=True)

        if g.shape[0] < min_points:
            continue

        g["run_order"] = np.arange(1, g.shape[0] + 1)

        x = g["run_order"].astype(float).to_numpy()
        y = g["median_value"].astype(float).to_numpy()

        n = len(x)

        if n < min_points:
            continue

        x_mean = x.mean()
        y_mean = y.mean()

        sxx = np.sum((x - x_mean) ** 2)

        if sxx == 0:
            continue

        # Ordinary least squares fit
        slope = np.sum((x - x_mean) * (y - y_mean)) / sxx
        intercept = y_mean - slope * x_mean

        fitted = intercept + slope * x

        residuals = y - fitted
        dof = n - 2

        if dof <= 0:
            continue

        residual_standard_error = np.sqrt(np.sum(residuals**2) / dof)
        t_value = stats.t.ppf(0.975, dof)

        # Confidence interval for the estimated mean trend
        standard_error_mean = residual_standard_error * np.sqrt(
            (1 / n) + ((x - x_mean) ** 2 / sxx)
        )

        ci_lower = fitted - t_value * standard_error_mean
        ci_upper = fitted + t_value * standard_error_mean

        out = g[[project_col, date_col, "run_order"]].copy()
        out["fit"] = fitted
        out["ci_lower"] = ci_lower
        out["ci_upper"] = ci_upper
        out["slope_per_run"] = slope
        out["p_value"] = stats.linregress(x, y).pvalue

        if group_col:
            out[group_col] = group_name
        else:
            out["trend_group"] = "Overall"

        trend_frames.append(out)

    if not trend_frames:
        return pd.DataFrame()

    return pd.concat(trend_frames, ignore_index=True)


def add_trend_line_and_ci(
    fig,
    df,
    value_col,
    project_col="project_name",
    date_col="date",
    group_col=None,
    show_confidence_band=True,
):
    """
    Adds a run-median trend line and optional 95% confidence band.

    This version draws the confidence band as one closed polygon,
    which behaves better with categorical x-axis labels.
    """

    trend_df = compute_linear_trend_with_ci(
        df=df,
        value_col=value_col,
        project_col=project_col,
        date_col=date_col,
        group_col=group_col,
    )

    if trend_df.empty:
        return fig

    # Keep x-axis order consistent with run date
    ordered_projects = (
        df[[project_col, date_col]]
        .drop_duplicates()
        .assign(
            **{
                date_col: lambda x: pd.to_datetime(
                    x[date_col], errors="coerce"
                )
            }
        )
        .sort_values(date_col)[project_col]
        .tolist()
    )

    fig.update_xaxes(
        categoryorder="array",
        categoryarray=ordered_projects,
    )

    if group_col and group_col in trend_df.columns:
        grouped = trend_df.groupby(group_col)
    else:
        grouped = [("Overall", trend_df)]

    for group_name, g in grouped:
        g = g.sort_values("run_order").copy()

        if g.empty:
            continue

        x_values = g[project_col].tolist()

        if show_confidence_band:
            # Draw confidence band as a single closed polygon
            band_x = x_values + x_values[::-1]
            band_y = g["ci_upper"].tolist() + g["ci_lower"].tolist()[::-1]

            fig.add_trace(
                go.Scatter(
                    x=band_x,
                    y=band_y,
                    fill="toself",
                    mode="lines",
                    line=dict(width=0),
                    fillcolor="rgba(0, 0, 0, 0.12)",
                    hoverinfo="skip",
                    name=f"95% confidence band - {group_name}",
                    showlegend=True,
                )
            )

        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=g["fit"],
                mode="lines+markers",
                name=f"Trend line - {group_name}",
                line=dict(color="black", width=2, dash="dash"),
                marker=dict(size=5, color="black"),
                customdata=np.stack(
                    [
                        g["slope_per_run"],
                        g["p_value"],
                    ],
                    axis=-1,
                ),
                hovertemplate=(
                    "Run: %{x}<br>"
                    "Estimated trend value: %{y:.3g}<br>"
                    "Slope per run: %{customdata[0]:.4f}<br>"
                    "p-value: %{customdata[1]:.4g}"
                    "<extra></extra>"
                ),
            )
        )

    return fig
