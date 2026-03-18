"""
ARCH-FL Enhanced Visualization Script
Focuses on accuracy relationships with privacy parameters and data distributions
"""

import os
import json
import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings("ignore")

# Set style for publication-quality figures
plt.style.use("seaborn-v0_8-paper")
sns.set_palette("husl")
sns.set_context("paper", font_scale=1.5)

# Configure plotting parameters
FIG_SIZE = (14, 8)
DPI = 300
COLORS = {
    "iid": "#2E86AB",
    "non_iid": "#A23B72",
    "dp_low": "#F18F01",
    "dp_high": "#C73E1D",
    "baseline": "#aaaaff",
    "chexpert": "#2874A6",
    "mimic": "#B03A2E",
    "delta_1e-5": "#1B98A0",
    "delta_1e-4": "#E8963E",
    "delta_1e-3": "#A7467A",
}


class AccuracyVisualizer:
    """Generate visualizations focusing on accuracy relationships"""

    def __init__(self, db_path: str, output_dir: str = "./visualizations"):
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._connect_db()

    def _connect_db(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def _execute_query(self, query: str, params: tuple = ()) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame"""
        return pd.read_sql_query(query, self.conn, params=params)

    def load_experiment_data(self) -> pd.DataFrame:
        """Load all experiment data with focus on accuracy metrics"""
        query = """
        SELECT
            e.id as experiment_id,
            e.name as experiment_name,
            e.num_clients,
            e.iid,
            e.status,
            e.created_at,
            e.parameters,
            er.rounds_completed,
            er.accuracy as final_accuracy,
            er.loss as final_loss,
            er.client_count,
            er.total_rounds,
            er.metrics as experiment_metrics,
            cr.client_id,
            cr.round,
            cr.accuracy as client_accuracy,
            cr.loss as client_loss,
            cr.timestamp
        FROM experiments e
        LEFT JOIN experiment_results er ON e.id = er.experiment_id
        LEFT JOIN client_results cr ON e.id = cr.experiment_id
        WHERE e.status = 'completed' AND er.accuracy IS NOT NULL
        ORDER BY e.id, cr.round, cr.client_id
        """
        return self._execute_query(query)

    def parse_parameters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract and parse privacy and distribution parameters"""
        df = df.copy()

        def extract_params(row):
            if pd.isna(row["parameters"]):
                return {}
            try:
                params = (
                    json.loads(row["parameters"])
                    if isinstance(row["parameters"], str)
                    else row["parameters"]
                )
                return {
                    "dp_enabled": params.get("dp_enabled", False),
                    "epsilon": params.get("epsilon", None),
                    "delta": params.get("delta", 1e-5),
                    "num_rounds": params.get("num_rounds", 0),
                    "local_epochs": params.get("local_epochs", 1),
                    "learning_rate": params.get("learning_rate", 0.01),
                    "batch_size": params.get("batch_size", 32),
                    "alpha": params.get("alpha", 0.5),  # Non-IID concentration
                    "aggregation_method": params.get("aggregation_method", "fed_avg"),
                    "noise_multiplier": params.get("noise_multiplier", None),
                    "max_grad_norm": params.get("max_grad_norm", 1.0),
                }
            except:
                return {}

        param_df = df.apply(extract_params, axis=1).apply(pd.Series)

        for col in param_df.columns:
            df[col] = param_df[col]

        # Add derived columns
        df["accuracy_percent"] = df["final_accuracy"]
        df["client_accuracy_percent"] = df["client_accuracy"]
        df["privacy_budget"] = df.apply(
            lambda row: (
                f"ε={row['epsilon']}, δ={row['delta']:.0e}"
                if row["dp_enabled"]
                else "No DP"
            ),
            axis=1,
        )
        df["distribution"] = df["iid"].apply(lambda x: "IID" if x == 1 else "Non-IID")
        df["log_epsilon"] = df["epsilon"].apply(
            lambda x: np.log10(x) if x and x > 0 else None
        )

        return df

    def figure_1_accuracy_vs_epsilon(self, df: pd.DataFrame):
        """
        Figure 1: Accuracy vs Epsilon for different delta values
        Shows how privacy budget affects model utility
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Filter DP experiments
        dp_df = df[df["dp_enabled"] == True].copy()

        if dp_df.empty:
            print("No DP experiments found")
            return

        # 1.1 Accuracy vs Epsilon (all data)
        ax1 = axes[0, 0]
        for delta in sorted(dp_df["delta"].unique()):
            delta_df = dp_df[dp_df["delta"] == delta]
            if not delta_df.empty:
                # Group by epsilon for this delta
                eps_data = (
                    delta_df.groupby("epsilon")["accuracy_percent"]
                    .agg(["mean", "std"])
                    .reset_index()
                )

                ax1.errorbar(
                    eps_data["epsilon"],
                    eps_data["mean"],
                    yerr=eps_data["std"],
                    marker="o",
                    capsize=5,
                    label=f"δ = {delta:.0e}",
                    linewidth=2,
                    markersize=8,
                )

        # Add baseline (no DP)
        baseline_df = df[df["dp_enabled"] == False]
        if not baseline_df.empty:
            baseline_acc = baseline_df["accuracy_percent"].mean()
            ax1.axhline(
                y=baseline_acc,
                color="gray",
                linestyle="--",
                alpha=0.7,
                label="No DP (Baseline)",
            )

            # Add shaded region for baseline std
            baseline_std = baseline_df["accuracy_percent"].std()
            ax1.axhspan(
                baseline_acc - baseline_std,
                baseline_acc + baseline_std,
                alpha=0.1,
                color="gray",
            )

        ax1.set_xlabel("Privacy Budget (ε)", fontsize=12, fontweight="bold")
        ax1.set_ylabel("Accuracy (%)", fontsize=12, fontweight="bold")
        ax1.set_title(
            "Accuracy vs Privacy Budget (ε) for Different δ",
            fontsize=14,
            fontweight="bold",
            pad=15,
        )
        ax1.set_xscale("log")
        ax1.grid(True, alpha=0.3, which="both")
        ax1.legend(loc="best", fontsize=10)

        # 1.2 Accuracy vs Epsilon (split by IID/Non-IID)
        ax2 = axes[0, 1]
        for dist_type in ["IID", "Non-IID"]:
            dist_df = dp_df[dp_df["distribution"] == dist_type]
            if not dist_df.empty:
                # Take median delta for clarity
                median_delta = dist_df["delta"].median()
                dist_df = dist_df[dist_df["delta"] == median_delta]

                eps_data = (
                    dist_df.groupby("epsilon")["accuracy_percent"]
                    .agg(["mean", "std"])
                    .reset_index()
                )

                color = COLORS["iid"] if dist_type == "IID" else COLORS["non_iid"]
                ax2.errorbar(
                    eps_data["epsilon"],
                    eps_data["mean"],
                    yerr=eps_data["std"],
                    marker="o",
                    capsize=5,
                    label=f"{dist_type} (δ={median_delta:.0e})",
                    color=color,
                    linewidth=2,
                    markersize=8,
                )

        ax2.set_xlabel("Privacy Budget (ε)", fontsize=12, fontweight="bold")
        ax2.set_ylabel("Accuracy (%)", fontsize=12, fontweight="bold")
        ax2.set_title(
            "Privacy Impact: IID vs Non-IID Distributions",
            fontsize=14,
            fontweight="bold",
            pad=15,
        )
        ax2.set_xscale("log")
        ax2.grid(True, alpha=0.3, which="both")
        ax2.legend(loc="best", fontsize=10)

        # 1.3 Accuracy heatmap: Epsilon vs Delta
        ax3 = axes[1, 0]

        # Create pivot table for heatmap
        pivot_data = (
            dp_df.groupby(["epsilon", "delta"])["accuracy_percent"].mean().reset_index()
        )
        heatmap_data = pivot_data.pivot(
            index="delta", columns="epsilon", values="accuracy_percent"
        )

        # Format delta for display
        heatmap_data.index = [f"{d:.0e}" for d in heatmap_data.index]
        heatmap_data.columns = [f"ε={c}" for c in heatmap_data.columns]

        sns.heatmap(
            heatmap_data,
            annot=True,
            fmt=".1f",
            cmap="YlOrRd",
            ax=ax3,
            cbar_kws={"label": "Accuracy (%)"},
            linewidths=1,
            linecolor="white",
        )
        ax3.set_title(
            "Accuracy Heatmap: ε vs δ Trade-off", fontsize=14, fontweight="bold", pad=15
        )
        ax3.set_xlabel("Privacy Budget (ε)")
        ax3.set_ylabel("Delta (δ)")

        # 1.4 Accuracy drop vs epsilon
        ax4 = axes[1, 1]

        baseline_acc = (
            baseline_df["accuracy_percent"].mean() if not baseline_df.empty else 100
        )

        for dist_type in ["IID", "Non-IID"]:
            dist_df = dp_df[dp_df["distribution"] == dist_type]
            if not dist_df.empty:
                # Calculate accuracy drop from baseline
                acc_drop = []
                for eps in sorted(dist_df["epsilon"].unique()):
                    eps_acc = dist_df[dist_df["epsilon"] == eps][
                        "accuracy_percent"
                    ].mean()
                    acc_drop.append(
                        {
                            "epsilon": eps,
                            "drop": baseline_acc - eps_acc,
                            "distribution": dist_type,
                        }
                    )

                drop_df = pd.DataFrame(acc_drop)
                if not drop_df.empty:
                    color = COLORS["iid"] if dist_type == "IID" else COLORS["non_iid"]
                    ax4.plot(
                        drop_df["epsilon"],
                        drop_df["drop"],
                        marker="o",
                        linewidth=2,
                        markersize=8,
                        color=color,
                        label=dist_type,
                    )

        ax4.set_xlabel("Privacy Budget (ε)", fontsize=12, fontweight="bold")
        ax4.set_ylabel("Accuracy Drop (% points)", fontsize=12, fontweight="bold")
        ax4.set_title(
            "Privacy-Induced Accuracy Degradation",
            fontsize=14,
            fontweight="bold",
            pad=15,
        )
        ax4.set_xscale("log")
        ax4.grid(True, alpha=0.3, which="both")
        ax4.legend(loc="best", fontsize=10)
        ax4.invert_xaxis()  # Higher epsilon = less privacy = smaller drop

        plt.suptitle(
            "Impact of Differential Privacy Parameters on Model Accuracy",
            fontsize=16,
            fontweight="bold",
            y=1.02,
        )
        plt.tight_layout()
        plt.savefig(
            self.output_dir / "figure_1_accuracy_vs_epsilon.png",
            dpi=DPI,
            bbox_inches="tight",
        )
        plt.close()
        print("✓ Generated Figure 1: Accuracy vs Epsilon")

    def figure_2_iid_vs_non_iid_accuracy(self, df: pd.DataFrame):
        """
        Figure 2: Accuracy comparison between IID and Non-IID across privacy levels
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # 2.1 Box plot: IID vs Non-IID accuracy
        ax1 = axes[0, 0]

        # Prepare data
        plot_data = []
        for _, row in df.iterrows():
            if not pd.isna(row["final_accuracy"]):
                plot_data.append(
                    {
                        "Distribution": "IID" if row["iid"] else "Non-IID",
                        "Privacy": "With DP" if row["dp_enabled"] else "No DP",
                        "Accuracy": row["accuracy_percent"],
                    }
                )

        plot_df = pd.DataFrame(plot_data)

        if not plot_df.empty:
            sns.boxplot(
                data=plot_df,
                x="Distribution",
                y="Accuracy",
                hue="Privacy",
                ax=ax1,
                palette=["#95A5A6", "#E67E22"],
            )
            ax1.set_title(
                "Accuracy Distribution: IID vs Non-IID", fontweight="bold", fontsize=14
            )
            ax1.set_ylabel("Accuracy (%)")
            ax1.grid(True, alpha=0.3, axis="y")

            # Add statistical annotation
            for i, dist in enumerate(["IID", "Non-IID"]):
                for j, priv in enumerate(["No DP", "With DP"]):
                    subset = plot_df[
                        (plot_df["Distribution"] == dist) & (plot_df["Privacy"] == priv)
                    ]
                    if not subset.empty:
                        mean_val = subset["Accuracy"].mean()
                        ax1.text(
                            i + j * 0.3 - 0.15,
                            mean_val + 1,
                            f"{mean_val:.1f}%",
                            ha="center",
                            fontsize=9,
                            fontweight="bold",
                        )

        # 2.2 Accuracy vs Alpha (Non-IID concentration)
        ax2 = axes[0, 1]

        non_iid_df = df[df["iid"] == 0].copy()
        if not non_iid_df.empty and "alpha" in non_iid_df.columns:
            for dp_status in [True, False]:
                subset = non_iid_df[non_iid_df["dp_enabled"] == dp_status]
                if not subset.empty:
                    # Group by alpha
                    alpha_data = (
                        subset.groupby("alpha")["accuracy_percent"]
                        .agg(["mean", "std"])
                        .reset_index()
                    )

                    label = "With DP" if dp_status else "No DP"
                    color = "#E67E22" if dp_status else "#95A5A6"

                    ax2.errorbar(
                        alpha_data["alpha"],
                        alpha_data["mean"],
                        yerr=alpha_data["std"],
                        marker="o",
                        capsize=5,
                        label=label,
                        color=color,
                        linewidth=2,
                    )

            ax2.set_xlabel(
                "Alpha (α) - Lower = More Non-IID", fontsize=12, fontweight="bold"
            )
            ax2.set_ylabel("Accuracy (%)", fontsize=12, fontweight="bold")
            ax2.set_title(
                "Impact of Non-IID Concentration (α) on Accuracy",
                fontsize=14,
                fontweight="bold",
                pad=15,
            )
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            ax2.invert_xaxis()  # Lower alpha = more non-IID

            # Add trend line
            z = np.polyfit(
                non_iid_df["alpha"].dropna(), non_iid_df["accuracy_percent"].dropna(), 1
            )
            p = np.poly1d(z)
            x_trend = np.linspace(
                non_iid_df["alpha"].min(), non_iid_df["alpha"].max(), 50
            )
            ax2.plot(x_trend, p(x_trend), "--", color="gray", alpha=0.5, label="Trend")

        # 2.3 Accuracy drop due to non-IID at different privacy levels
        ax3 = axes[1, 0]

        # Calculate accuracy drop
        iid_acc = df[df["iid"] == 1].groupby("dp_enabled")["accuracy_percent"].mean()

        drop_data = []
        for dp_status in [True, False]:
            non_iid_subset = non_iid_df[non_iid_df["dp_enabled"] == dp_status]
            if not non_iid_subset.empty:
                for eps in (
                    sorted(non_iid_subset["epsilon"].unique()) if dp_status else [None]
                ):
                    if dp_status:
                        subset = non_iid_subset[non_iid_subset["epsilon"] == eps]
                        label = f"ε={eps}"
                    else:
                        subset = non_iid_subset
                        label = "No DP"

                    if not subset.empty:
                        non_iid_mean = subset["accuracy_percent"].mean()
                        iid_mean = (
                            iid_acc[dp_status]
                            if dp_status in iid_acc.index
                            else iid_acc[False]
                        )

                        drop_data.append(
                            {
                                "Privacy": label,
                                "Drop": iid_mean - non_iid_mean,
                                "DP": dp_status,
                            }
                        )

        drop_df = pd.DataFrame(drop_data)
        if not drop_df.empty:
            bars = ax3.bar(
                range(len(drop_df)),
                drop_df["Drop"],
                color=[
                    COLORS["dp_low"] if d else COLORS["baseline"] for d in drop_df["DP"]
                ],
            )
            ax3.set_xticks(range(len(drop_df)))
            ax3.set_xticklabels(drop_df["Privacy"], rotation=45, ha="right")
            ax3.set_ylabel("Accuracy Drop (% points)", fontsize=12, fontweight="bold")
            ax3.set_title(
                "Accuracy Loss Due to Non-IID Distribution",
                fontsize=14,
                fontweight="bold",
                pad=15,
            )
            ax3.grid(True, alpha=0.3, axis="y")

            # Add value labels
            for bar, val in zip(bars, drop_df["Drop"]):
                height = bar.get_height()
                ax3.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.1,
                    f"{val:.2f}%",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                )

        # 2.4 Client accuracy variance (IID vs Non-IID)
        ax4 = axes[1, 1]

        variance_data = []
        for exp_id in df["experiment_id"].unique():
            exp_df = df[df["experiment_id"] == exp_id]
            client_accs = exp_df["client_accuracy_percent"].dropna()

            if len(client_accs) > 1:
                variance_data.append(
                    {
                        "Experiment": exp_id,
                        "Distribution": "IID" if exp_df["iid"].iloc[0] else "Non-IID",
                        "Privacy": "With DP"
                        if exp_df["dp_enabled"].iloc[0]
                        else "No DP",
                        "Variance": client_accs.var(),
                        "Std": client_accs.std(),
                    }
                )

        var_df = pd.DataFrame(variance_data)
        if not var_df.empty:
            # Grouped bar plot
            var_pivot = var_df.pivot_table(
                values="Std", index="Distribution", columns="Privacy", aggfunc="mean"
            )

            var_pivot.plot(kind="bar", ax=ax4, color=["#95A5A6", "#E67E22"])
            ax4.set_title(
                "Client Accuracy Variance (Fairness Metric)",
                fontweight="bold",
                fontsize=14,
            )
            ax4.set_ylabel("Standard Deviation of Client Accuracies")
            ax4.set_xlabel("Data Distribution")
            ax4.grid(True, alpha=0.3, axis="y")
            ax4.legend(title="Privacy")

            # Add value labels
            for container in ax4.containers:
                ax4.bar_label(container, fmt="%.2f", fontsize=9)

        plt.suptitle(
            "IID vs Non-IID: Impact on Model Accuracy and Fairness",
            fontsize=16,
            fontweight="bold",
            y=1.02,
        )
        plt.tight_layout()
        plt.savefig(
            self.output_dir / "figure_2_iid_vs_non_iid_accuracy.png",
            dpi=DPI,
            bbox_inches="tight",
        )
        plt.close()
        print("✓ Generated Figure 2: IID vs Non-IID Accuracy")

    def figure_3_accuracy_heatmap_matrix(self, df: pd.DataFrame):
        """
        Figure 3: Comprehensive heatmap matrix showing accuracy relationships
        """
        fig = plt.figure(figsize=(18, 12))

        # Create grid for subplots
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

        # 3.1 Epsilon vs Delta heatmap (IID)
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_epsilon_delta_heatmap(df[df["iid"] == 1], ax1, "IID Distribution")

        # 3.2 Epsilon vs Delta heatmap (Non-IID)
        ax2 = fig.add_subplot(gs[0, 1])
        self._plot_epsilon_delta_heatmap(
            df[df["iid"] == 0], ax2, "Non-IID Distribution"
        )

        # 3.3 Epsilon vs Alpha heatmap
        ax3 = fig.add_subplot(gs[0, 2])
        self._plot_epsilon_alpha_heatmap(df, ax3)

        # 3.4 Delta vs Alpha heatmap
        ax4 = fig.add_subplot(gs[1, 0])
        self._plot_delta_alpha_heatmap(df, ax4)

        # 3.5 Privacy Level vs Distribution heatmap
        ax5 = fig.add_subplot(gs[1, 1])
        self._plot_privacy_distribution_heatmap(df, ax5)

        # 3.6 Epsilon vs Rounds heatmap
        ax6 = fig.add_subplot(gs[1, 2])
        self._plot_epsilon_rounds_heatmap(df, ax6)

        # 3.7 Summary statistics table
        ax7 = fig.add_subplot(gs[2, :])
        self._plot_summary_table(df, ax7)

        plt.suptitle(
            "Accuracy Relationship Matrix: Privacy, Distribution, and Performance",
            fontsize=18,
            fontweight="bold",
            y=0.98,
        )
        plt.savefig(
            self.output_dir / "figure_3_accuracy_heatmap_matrix.png",
            dpi=DPI,
            bbox_inches="tight",
        )
        plt.close()
        print("✓ Generated Figure 3: Accuracy Heatmap Matrix")

    def _plot_epsilon_delta_heatmap(self, df: pd.DataFrame, ax, title: str):
        """Helper for epsilon-delta heatmap"""
        dp_df = df[df["dp_enabled"] == True]
        if dp_df.empty:
            ax.text(0.5, 0.5, "No data", ha="center", va="center")
            return

        pivot = dp_df.pivot_table(
            values="accuracy_percent", index="delta", columns="epsilon", aggfunc="mean"
        )

        # Format labels
        pivot.index = [f"{d:.0e}" for d in pivot.index]
        pivot.columns = [f"ε={c}" for c in pivot.columns]

        sns.heatmap(
            pivot,
            annot=True,
            fmt=".1f",
            cmap="viridis",
            ax=ax,
            cbar_kws={"label": "Accuracy (%)"},
            linewidths=1,
        )
        ax.set_title(title, fontweight="bold", fontsize=12)
        ax.set_xlabel("Privacy Budget (ε)")
        ax.set_ylabel("Delta (δ)")

    def _plot_epsilon_alpha_heatmap(self, df: pd.DataFrame, ax):
        """Heatmap: Epsilon vs Alpha"""
        non_iid_df = df[df["iid"] == 0].copy()
        # print(non_iid_df)
        if non_iid_df.empty or "alpha" not in non_iid_df.columns:
            ax.text(0.5, 0.5, "No non-IID data with alpha", ha="center", va="center")
            return

        # Bin alpha values for better visualization
        non_iid_df["alpha_bin"] = pd.cut(non_iid_df["alpha"], bins=5)
        print(non_iid_df["dp_enabled"])  # All shouldn't be same value eg True
        pivot = non_iid_df.pivot_table(
            values="accuracy_percent",
            index="alpha_bin",
            columns="epsilon" if "epsilon" in non_iid_df.columns else "dp_enabled",
            aggfunc="mean",
        )
        if not pivot.empty:
            sns.heatmap(
                pivot,
                annot=True,
                fmt=".1f",
                cmap="YlGnBu",
                ax=ax,
                cbar_kws={"label": "Accuracy (%)"},
            )
            ax.set_title(
                "Epsilon vs Alpha (Non-IID Concentration)",
                fontweight="bold",
                fontsize=12,
            )
            ax.set_xlabel("Privacy Configuration")
            ax.set_ylabel("Alpha (lower = more non-IID)")
        else:
            print("Pivot empty - no valid combinations")

    def _plot_delta_alpha_heatmap(self, df: pd.DataFrame, ax):
        """Heatmap: Delta vs Alpha"""
        non_iid_df = df[(df["iid"] == 0) & (df["dp_enabled"] == True)].copy()
        if non_iid_df.empty or "alpha" not in non_iid_df.columns:
            ax.text(0.5, 0.5, "No DP non-IID data", ha="center", va="center")
            return

        non_iid_df["alpha_bin"] = pd.cut(non_iid_df["alpha"], bins=4)

        pivot = non_iid_df.pivot_table(
            values="accuracy_percent",
            index="alpha_bin",
            columns="delta",
            aggfunc="mean",
        )
        if not pivot.empty:
            pivot.columns = [f"{c:.0e}" for c in pivot.columns]

            sns.heatmap(
                pivot,
                annot=True,
                fmt=".1f",
                cmap="RdYlBu_r",
                ax=ax,
                cbar_kws={"label": "Accuracy (%)"},
            )
            ax.set_title("Delta vs Alpha Interaction", fontweight="bold", fontsize=12)
            ax.set_xlabel("Delta (δ)")
            ax.set_ylabel("Alpha")
        else:
            print("Pivot empty - no valid combinations")

    def _plot_privacy_distribution_heatmap(self, df: pd.DataFrame, ax):
        """Heatmap: Privacy Level vs Distribution"""
        # Create privacy categories
        df["privacy_level"] = df.apply(
            lambda x: (
                "No DP"
                if not x["dp_enabled"]
                else f"ε={x['epsilon']}"
                if x["epsilon"] <= 1.0
                else f"ε={x['epsilon']}"
            ),
            axis=1,
        )

        pivot = df.pivot_table(
            values="accuracy_percent",
            index="distribution",
            columns="privacy_level",
            aggfunc="mean",
        )
        if not pivot.empty:
            sns.heatmap(
                pivot,
                annot=True,
                fmt=".1f",
                cmap="coolwarm",
                ax=ax,
                cbar_kws={"label": "Accuracy (%)"},
                center=75,
            )
            ax.set_title(
                "Privacy Level vs Distribution", fontweight="bold", fontsize=12
            )
            ax.set_xlabel("Privacy Configuration")
            ax.set_ylabel("Data Distribution")
        else:
            print("Pivot empty - no valid combinations")

    def _plot_epsilon_rounds_heatmap(self, df: pd.DataFrame, ax):
        """Heatmap: Epsilon vs Training Rounds"""
        df["rounds_bin"] = pd.cut(df["rounds_completed"], bins=5)

        pivot = df.pivot_table(
            values="accuracy_percent",
            index="rounds_bin",
            columns="epsilon" if "epsilon" in df.columns else "dp_enabled",
            aggfunc="mean",
        )
        if not pivot.empty:
            sns.heatmap(
                pivot,
                annot=True,
                fmt=".1f",
                cmap="magma",
                ax=ax,
                cbar_kws={"label": "Accuracy (%)"},
            )
            ax.set_title("Epsilon vs Training Rounds", fontweight="bold", fontsize=12)
            ax.set_xlabel("Privacy Budget (ε)")
            ax.set_ylabel("Rounds Completed")
        else:
            print("Pivot empty - no valid combinations")

    def _plot_summary_table(self, df: pd.DataFrame, ax):
        """Create summary statistics table"""
        ax.axis("tight")
        ax.axis("off")

        # Calculate summary statistics
        summary_data = []

        for dist in ["IID", "Non-IID"]:
            for dp in ["No DP", "With DP"]:
                subset = df[
                    (df["distribution"] == dist)
                    & (df["dp_enabled"] == (dp == "With DP"))
                ]

                if not subset.empty:
                    summary_data.append(
                        [
                            dist,
                            dp,
                            f"{subset['accuracy_percent'].mean():.2f}%",
                            f"{subset['accuracy_percent'].std():.2f}",
                            f"{subset['final_loss'].mean():.4f}",
                            f"{len(subset)}",
                        ]
                    )

        # Add epsilon-specific data
        for eps in sorted(df[df["dp_enabled"] == True]["epsilon"].unique()):
            subset = df[df["epsilon"] == eps]
            if not subset.empty:
                summary_data.append(
                    [
                        "All",
                        f"ε={eps}",
                        f"{subset['accuracy_percent'].mean():.2f}%",
                        f"{subset['accuracy_percent'].std():.2f}",
                        f"{subset['final_loss'].mean():.4f}",
                        f"{len(subset)}",
                    ]
                )

        # Create table
        columns = ["Distribution", "Privacy", "Avg Acc", "Std", "Avg Loss", "Count"]
        table = ax.table(
            cellText=summary_data,
            colLabels=columns,
            cellLoc="center",
            loc="center",
            colWidths=[0.15, 0.2, 0.15, 0.15, 0.15, 0.1],
        )

        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)

        # Style header
        for (i, j), cell in table.get_celld().items():
            if i == 0:
                cell.set_facecolor("#40466e")
                cell.set_text_props(weight="bold", color="white")

        ax.set_title("Summary Statistics Table", fontweight="bold", fontsize=14, pad=20)

    def figure_4_convergence_with_privacy(self, df: pd.DataFrame):
        """
        Figure 4: Convergence curves showing accuracy over rounds for different privacy levels
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # 4.1 IID convergence at different privacy levels
        ax1 = axes[0, 0]
        self._plot_convergence_curves(df[df["iid"] == 1], ax1, "IID Distribution")

        # 4.2 Non-IID convergence at different privacy levels
        ax2 = axes[0, 1]
        self._plot_convergence_curves(df[df["iid"] == 0], ax2, "Non-IID Distribution")

        # 4.3 Privacy impact on convergence speed
        ax3 = axes[1, 0]
        self._plot_convergence_speed(df, ax3)

        # 4.4 Final accuracy vs convergence time
        ax4 = axes[1, 1]
        self._plot_accuracy_vs_time(df, ax4)

        plt.suptitle(
            "Convergence Analysis: Impact of Privacy on Learning Dynamics",
            fontsize=16,
            fontweight="bold",
            y=1.02,
        )
        plt.tight_layout()
        plt.savefig(
            self.output_dir / "figure_4_convergence_with_privacy.png",
            dpi=DPI,
            bbox_inches="tight",
        )
        plt.close()
        print("✓ Generated Figure 4: Convergence with Privacy")

    def _plot_convergence_curves(self, df: pd.DataFrame, ax, title: str):
        """Plot convergence curves for different privacy levels"""
        # Get per-round data
        round_data = []
        for _, row in df.iterrows():
            if not pd.isna(row["round"]) and not pd.isna(row["client_accuracy"]):
                privacy_label = (
                    "No DP" if not row["dp_enabled"] else f"ε={row['epsilon']}"
                )
                round_data.append(
                    {
                        "Round": row["round"],
                        "Accuracy": row["client_accuracy_percent"],
                        "Privacy": privacy_label,
                        "Experiment": row["experiment_id"],
                    }
                )

        round_df = pd.DataFrame(round_data)

        if round_df.empty:
            ax.text(0.5, 0.5, "No round data", ha="center", va="center")
            return

        # Plot curves for each privacy level
        for privacy in sorted(round_df["Privacy"].unique()):
            subset = round_df[round_df["Privacy"] == privacy]

            # Calculate mean and std per round
            grouped = (
                subset.groupby("Round")["Accuracy"]
                .agg(["mean", "std", "count"])
                .reset_index()
            )

            # Only plot if enough data
            if len(grouped) > 1:
                color = (
                    COLORS["baseline"]
                    if privacy == "No DP"
                    else plt.cm.RdYlBu_r(
                        privacy.split("=")[-1] if "=" in privacy else 0.5
                    )
                )
                ax.plot(
                    grouped["Round"],
                    grouped["mean"],
                    label=privacy,
                    linewidth=2,
                    marker="o",
                    markersize=4,
                    markevery=5,
                )
                ax.fill_between(
                    grouped["Round"],
                    grouped["mean"] - grouped["std"],
                    grouped["mean"] + grouped["std"],
                    alpha=0.1,
                )

        ax.set_xlabel("Communication Round", fontsize=11)
        ax.set_ylabel("Accuracy (%)", fontsize=11)
        ax.set_title(title, fontweight="bold", fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize=9)
        ax.set_ylim([0, 100])

    def _plot_convergence_speed(self, df: pd.DataFrame, ax):
        """Plot rounds to reach target accuracy"""
        target_acc = 75  # Target accuracy percentage

        speed_data = []
        for exp_id in df["experiment_id"].unique():
            exp_df = df[df["experiment_id"] == exp_id]

            # Get per-round accuracy
            round_accs = exp_df.groupby("round")["client_accuracy_percent"].mean()

            # Find first round reaching target
            rounds_to_target = None
            for round_num, acc in round_accs.items():
                if acc >= target_acc:
                    rounds_to_target = round_num
                    break

            if rounds_to_target:
                speed_data.append(
                    {
                        "Experiment": exp_id,
                        "Distribution": "IID" if exp_df["iid"].iloc[0] else "Non-IID",
                        "Privacy": "No DP"
                        if not exp_df["dp_enabled"].iloc[0]
                        else f"ε={exp_df['epsilon'].iloc[0]}",
                        "Rounds": rounds_to_target,
                    }
                )

        speed_df = pd.DataFrame(speed_data)

        if not speed_df.empty:
            # Create grouped bar plot
            pivot = speed_df.pivot_table(
                values="Rounds", index="Distribution", columns="Privacy", aggfunc="mean"
            )
            if not pivot.empty:
                pivot.plot(
                    kind="bar",
                    ax=ax,
                    color=["#95A5A6", "#F39C12", "#E67E22", "#D35400"],
                )
                ax.set_title(
                    f"Rounds to Reach {target_acc}% Accuracy",
                    fontweight="bold",
                    fontsize=12,
                )
                ax.set_ylabel("Number of Rounds")
                ax.set_xlabel("Data Distribution")
                ax.grid(True, alpha=0.3, axis="y")
                ax.legend(title="Privacy", bbox_to_anchor=(1.05, 1))

                # Add value labels
                for container in ax.containers:
                    ax.bar_label(container, fmt="%.0f", fontsize=9)
            else:
                print("Pivot empty - no valid combinations")

    def _plot_accuracy_vs_time(self, df: pd.DataFrame, ax):
        """Scatter plot: Final accuracy vs training time"""
        time_data = []
        for exp_id in df["experiment_id"].unique():
            exp_df = df[df["experiment_id"] == exp_id]

            # Estimate training time from rounds
            total_rounds = (
                exp_df["total_rounds"].iloc[0]
                if "total_rounds" in exp_df.columns
                else 0
            )
            rounds_completed = (
                exp_df["rounds_completed"].iloc[0]
                if "rounds_completed" in exp_df.columns
                else 0
            )

            time_data.append(
                {
                    "Experiment": exp_id,
                    "Distribution": "IID" if exp_df["iid"].iloc[0] else "Non-IID",
                    "Privacy": "No DP"
                    if not exp_df["dp_enabled"].iloc[0]
                    else f"ε={exp_df['epsilon'].iloc[0]}",
                    "Accuracy": exp_df["accuracy_percent"].iloc[0],
                    "Rounds": rounds_completed,
                }
            )

        time_df = pd.DataFrame(time_data)

        if not time_df.empty:
            # Create scatter plot
            for dist in ["IID", "Non-IID"]:
                for priv in time_df["Privacy"].unique():
                    subset = time_df[
                        (time_df["Distribution"] == dist) & (time_df["Privacy"] == priv)
                    ]
                    if not subset.empty:
                        marker = "o" if dist == "IID" else "s"
                        color = (
                            COLORS["baseline"] if priv == "No DP" else COLORS["dp_low"]
                        )
                        ax.scatter(
                            subset["Rounds"],
                            subset["Accuracy"],
                            label=f"{dist}, {priv}",
                            marker=marker,
                            s=100,
                            alpha=0.7,
                        )

            ax.set_xlabel("Training Rounds Completed", fontsize=11)
            ax.set_ylabel("Final Accuracy (%)", fontsize=11)
            ax.set_title(
                "Accuracy vs Training Duration", fontweight="bold", fontsize=12
            )
            ax.grid(True, alpha=0.3)
            ax.legend(bbox_to_anchor=(1.05, 1), fontsize=8)

    def generate_all_charts(self):
        """Generate all visualization charts"""
        print("\n" + "=" * 70)
        print("ARCH-FL Accuracy Analysis Visualization Generator")
        print("=" * 70 + "\n")

        # Load and prepare data
        print("Loading experiment data...")
        df = self.load_experiment_data()
        df = self.parse_parameters(df)

        print(
            f"Loaded {len(df)} records from {df['experiment_id'].nunique()} experiments"
        )
        print(
            f"Experiments with DP: {df[df['dp_enabled'] == True]['experiment_id'].nunique()}"
        )
        print(
            f"Experiments without DP: {df[df['dp_enabled'] == False]['experiment_id'].nunique()}"
        )
        print(f"IID experiments: {df[df['iid'] == 1]['experiment_id'].nunique()}")
        print(f"Non-IID experiments: {df[df['iid'] == 0]['experiment_id'].nunique()}\n")

        # Generate figures
        self.figure_1_accuracy_vs_epsilon(df)
        self.figure_2_iid_vs_non_iid_accuracy(df)
        self.figure_3_accuracy_heatmap_matrix(df)
        self.figure_4_convergence_with_privacy(df)

        # Generate summary statistics CSV
        self.generate_summary_csv(df)

        print(f"\n✓ All charts generated successfully in: {self.output_dir}")
        print("\n" + "=" * 70)

    def generate_summary_csv(self, df: pd.DataFrame):
        """Generate CSV with summary statistics"""
        summary = []

        for (dist, dp_enabled, eps), group in df.groupby(
            ["distribution", "dp_enabled", "epsilon"]
        ):
            summary.append(
                {
                    "Distribution": dist,
                    "DP_Enabled": dp_enabled,
                    "Epsilon": eps if dp_enabled else "N/A",
                    "Delta": group["delta"].iloc[0] if dp_enabled else "N/A",
                    "Mean_Accuracy": group["accuracy_percent"].mean(),
                    "Std_Accuracy": group["accuracy_percent"].std(),
                    "Min_Accuracy": group["accuracy_percent"].min(),
                    "Max_Accuracy": group["accuracy_percent"].max(),
                    "Mean_Loss": group["final_loss"].mean(),
                    "Std_Loss": group["final_loss"].std(),
                    "Num_Experiments": group["experiment_id"].nunique(),
                    "Num_Records": len(group),
                }
            )

        summary_df = pd.DataFrame(summary)
        summary_df.to_csv(self.output_dir / "accuracy_summary.csv", index=False)
        print(
            f"✓ Summary statistics saved to: {self.output_dir / 'accuracy_summary.csv'}"
        )


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate ARCH-FL accuracy visualizations"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="../dashboard/data/dashboard.db",
        help="Path to SQLite database",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="../assets/findings",
        help="Directory to save visualizations",
    )
    parser.add_argument(
        "--charts",
        nargs="+",
        choices=["all", "epsilon", "iid", "heatmap", "convergence"],
        default=["all"],
        help="Charts to generate",
    )

    args = parser.parse_args()

    # Initialize visualizer
    visualizer = AccuracyVisualizer(args.db_path, args.output_dir)

    # Generate selected charts
    if "all" in args.charts:
        visualizer.generate_all_charts()
    else:
        df = visualizer.load_experiment_data()
        df = visualizer.parse_parameters(df)

        chart_map = {
            "epsilon": visualizer.figure_1_accuracy_vs_epsilon,
            "iid": visualizer.figure_2_iid_vs_non_iid_accuracy,
            "heatmap": visualizer.figure_3_accuracy_heatmap_matrix,
            "convergence": visualizer.figure_4_convergence_with_privacy,
        }

        for chart in args.charts:
            if chart in chart_map:
                print(f"\nGenerating {chart} chart...")
                chart_map[chart](df)

        visualizer.generate_summary_csv(df)


if __name__ == "__main__":
    main()
