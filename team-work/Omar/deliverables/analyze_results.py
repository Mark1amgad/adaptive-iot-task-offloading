"""
Beginner-friendly analyzer for IoT Local/Edge/Cloud task-offloading results.

Run:
    python analyze_results.py --input example_results.csv --output-dir analysis_output

Required CSV columns:
    task_id, policy, scenario, run_id, completed, latency_ms, deadline_ms

Optional columns:
    energy_j, resource_utilization_pct, selected_location, seed

This script analyzes the data you provide. It does not create real experiment results.
"""
import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


REQUIRED_COLUMNS = [
    "task_id", "policy", "scenario", "run_id",
    "completed", "latency_ms", "deadline_ms"
]

# Standardize common policy names so "local" and "Local Only" mean the same thing.
POLICY_NAMES = {
    "local": "Local Only",
    "local only": "Local Only",
    "edge": "Edge Only",
    "edge only": "Edge Only",
    "cloud": "Cloud Only",
    "cloud only": "Cloud Only",
    "ai": "AI Model",
    "ai model": "AI Model",
    "model": "AI Model",
}


def convert_completed(value):
    """Convert common CSV values to True/False. Unknown values become missing."""
    if pd.isna(value):
        return pd.NA

    value = str(value).strip().lower()

    if value in {"true", "1", "yes", "y", "completed", "success"}:
        return True
    if value in {"false", "0", "no", "n", "failed", "unfinished", "incomplete"}:
        return False

    return pd.NA


def load_csv(input_path):
    """Read CSV and check the columns and values we rely on."""
    df = pd.read_csv(input_path)

    # 1. Check that every required column exists.
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing_columns)
            + ". Compare your CSV header with the required schema in experiment_plan.md."
        )

    # 2. Remove accidental spaces around text.
    for column in ["task_id", "policy", "scenario", "run_id"]:
        df[column] = df[column].astype("string").str.strip()

    # 3. Standardize policy names.
    df["policy"] = (
        df["policy"].str.lower().map(POLICY_NAMES).fillna(df["policy"])
    )

    # 4. Convert completion values and numbers.
    df["completed"] = df["completed"].map(convert_completed).astype("boolean")
    numeric_columns = ["latency_ms", "deadline_ms"]
    for optional_column in ["energy_j", "resource_utilization_pct"]:
        if optional_column in df.columns:
            numeric_columns.append(optional_column)

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # 5. Reject unclear completion values instead of guessing.
    if df["completed"].isna().any():
        raise ValueError(
            "Some 'completed' values are unclear. Use true/false, 1/0, yes/no, "
            "completed/failed, or update convert_completed() to match your CSV."
        )

    if df[["task_id", "policy", "scenario", "run_id"]].isna().any().any():
        raise ValueError("task_id, policy, scenario, and run_id cannot be blank.")

    if df["deadline_ms"].isna().any():
        raise ValueError("deadline_ms is missing or not numeric in at least one row.")
    if (df["deadline_ms"] < 0).any():
        raise ValueError("deadline_ms cannot be negative.")
    if (df["latency_ms"].dropna() < 0).any():
        raise ValueError("latency_ms cannot be negative.")

    # A completed task must have a latency measurement.
    bad_latency = df["completed"] & df["latency_ms"].isna()
    if bad_latency.any():
        raise ValueError("At least one completed task has no valid latency_ms.")

    if "energy_j" in df.columns and (df["energy_j"].dropna() < 0).any():
        raise ValueError("energy_j cannot be negative.")

    if "resource_utilization_pct" in df.columns:
        util = df["resource_utilization_pct"].dropna()
        if ((util < 0) | (util > 100)).any():
            raise ValueError("resource_utilization_pct must be between 0 and 100.")

    # One row per task-policy-scenario-run is expected.
    key = ["task_id", "policy", "scenario", "run_id"]
    if df.duplicated(key).any():
        raise ValueError(
            "Duplicate task_id + policy + scenario + run_id rows found. "
            "Check whether the CSV contains events rather than one row per task."
        )

    return df


def add_task_metrics(df):
    """Add True/False columns that make the later calculations easier."""
    df = df.copy()

    # A task succeeds only if it completed and met its deadline.
    df["deadline_met"] = (
        df["completed"].astype(bool)
        & df["latency_ms"].notna()
        & (df["latency_ms"] <= df["deadline_ms"])
    )

    # Any task that did not meet its deadline is counted as a miss.
    # That includes failed or unfinished tasks.
    df["deadline_missed"] = ~df["deadline_met"]

    # Failure rate only counts tasks marked as not completed.
    df["task_failed"] = ~df["completed"].astype(bool)

    # Do not use a latency number for a task that never completed.
    df.loc[~df["completed"].astype(bool), "latency_ms"] = float("nan")

    return df


def calculate_run_metrics(task_df):
    """Calculate one row of metrics for each scenario + run + policy."""
    grouping = ["scenario", "run_id", "policy"]

    def deadline_success(series):
        # The mean of True/False values is the fraction that are True.
        return 100 * series.mean()

    metrics = {
        "tasks_submitted": ("task_id", "count"),
        "tasks_completed": ("completed", "sum"),
        "average_latency_ms": ("latency_ms", "mean"),
        "deadline_success_pct": ("deadline_met", deadline_success),
        "deadline_miss_pct": ("deadline_missed", deadline_success),
        "failure_rate_pct": ("task_failed", deadline_success),
    }

    if "energy_j" in task_df.columns:
        metrics["average_energy_j"] = ("energy_j", "mean")

    if "resource_utilization_pct" in task_df.columns:
        metrics["average_resource_utilization_pct"] = (
            "resource_utilization_pct", "mean"
        )

    result = task_df.groupby(grouping, dropna=False).agg(**metrics).reset_index()
    result["completion_rate_pct"] = (
        100 * result["tasks_completed"] / result["tasks_submitted"]
    )

    return result


def summarize_policies(run_df):
    """Summarize results across runs, separately for each scenario and policy."""
    metrics = [
        column for column in run_df.columns
        if column not in ["scenario", "run_id", "policy"]
        and pd.api.types.is_numeric_dtype(run_df[column])
    ]

    # Mean = average between runs; SD = standard deviation between runs;
    # count = number of run-level values contributing to the summary.
    summary = run_df.groupby(["scenario", "policy"])[metrics].agg(
        ["mean", "std", "count"]
    )

    # Flatten the multi-row column labels to simple names for CSV.
    summary.columns = [
        f"{metric}_{statistic}"
        for metric, statistic in summary.columns.to_flat_index()
    ]

    return summary.reset_index()


def draw_metric_plot(summary, metric, y_label, title, output_dir):
    """Create a bar chart of the mean metric for each policy and scenario."""
    mean_column = metric + "_mean"

    # Some metrics are optional, so skip a chart if the data does not exist.
    if mean_column not in summary.columns:
        return

    chart_data = summary[["scenario", "policy", mean_column]].dropna()
    if chart_data.empty:
        return

    scenarios = list(chart_data["scenario"].drop_duplicates())
    fig, axes = plt.subplots(
        len(scenarios), 1,
        figsize=(9, max(4, 3.5 * len(scenarios))),
        squeeze=False
    )

    for axis, scenario in zip(axes[:, 0], scenarios):
        data = chart_data[chart_data["scenario"] == scenario]
        axis.bar(data["policy"], data[mean_column])
        axis.set_title(str(scenario))
        axis.set_ylabel(y_label)
        axis.tick_params(axis="x", labelrotation=15)
        axis.grid(axis="y", alpha=0.25)

    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(output_dir / f"{metric}.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Analyze task-offloading CSV results.")
    parser.add_argument("--input", required=True, help="Path to the simulator CSV file.")
    parser.add_argument(
        "--output-dir", default="analysis_output",
        help="Folder where analysis CSVs and charts will be saved."
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Cannot find input file: {input_path}")

    # Run the analysis in clear stages.
    raw_data = load_csv(input_path)
    task_data = add_task_metrics(raw_data)
    run_metrics = calculate_run_metrics(task_data)
    policy_summary = summarize_policies(run_metrics)

    # Export tables so the team can inspect or reuse them.
    task_data.to_csv(output_dir / "task_metrics.csv", index=False)
    run_metrics.to_csv(output_dir / "run_metrics.csv", index=False)
    policy_summary.to_csv(output_dir / "policy_summary.csv", index=False)

    # Make charts for the main metrics.
    chart_list = [
        ("average_latency_ms", "Latency (ms)", "Average completed-task latency"),
        ("deadline_success_pct", "Success (%)", "Deadline success rate"),
        ("deadline_miss_pct", "Misses (%)", "Deadline miss rate"),
        ("failure_rate_pct", "Failures (%)", "Task failure rate"),
        ("average_energy_j", "Energy (J)", "Average energy"),
        ("average_resource_utilization_pct", "Utilization (%)",
         "Average resource utilization"),
    ]

    for metric, y_label, title in chart_list:
        draw_metric_plot(policy_summary, metric, y_label, title, output_dir)

    print(f"Input rows analyzed: {len(raw_data)}")
    print(f"Scenarios: {raw_data['scenario'].nunique()}")
    print(f"Policies: {raw_data['policy'].nunique()}")
    print(f"Output folder: {output_dir.resolve()}")
    print("Reminder: these results are only as valid as the CSV definitions and experiment fairness.")


if __name__ == "__main__":
    main()
