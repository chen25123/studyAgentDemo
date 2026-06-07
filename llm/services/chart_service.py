"""Chart 生成服务 —— matplotlib 渲染 → base64 PNG。

支持柱状图（group_by 场景）和单一指标卡（无 group_by 场景）。
"""

import base64
import io

import matplotlib

matplotlib.use("Agg")  # 非交互式后端，适合服务端
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

# 中文字体配置
_CN_FONT = None
for name in ["Microsoft YaHei", "SimHei", "PingFang SC", "Noto Sans CJK SC"]:
    for f in fm.fontManager.ttflist:
        if f.name == name:
            _CN_FONT = f.fname
            break
    if _CN_FONT:
        break

if _CN_FONT:
    _CN_FONT_PROP = fm.FontProperties(fname=_CN_FONT)
    plt.rcParams["font.family"] = fm.FontProperties(fname=_CN_FONT).get_name()
else:
    _CN_FONT_PROP = None
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]

plt.rcParams["axes.unicode_minus"] = False


class ChartService:
    """根据指标数据生成 matplotlib 图表，返回 base64 PNG。"""

    def render_bar_chart(
        self,
        labels: list[str],
        values: list[float],
        title: str,
        ylabel: str = "",
    ) -> str:
        """柱状图 —— 用于 group_by 场景。"""
        fig, ax = plt.subplots(figsize=(max(len(labels) * 0.8, 6), 4.5))
        colors = ["#176b87", "#219ebc", "#8ecae6", "#ffb703", "#fb8500"]
        bar_colors = [colors[i % len(colors)] for i in range(len(labels))]

        bars = ax.bar(range(len(labels)), values, color=bar_colors, width=0.6)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontproperties=_CN_FONT_PROP, fontsize=10, rotation=30)

        for bar, val in zip(bars, values, strict=True):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(values) * 0.02,
                f"{val:.1f}" if val < 1 else f"{val:,.0f}",
                ha="center",
                fontsize=9,
                fontproperties=_CN_FONT_PROP,
            )

        ax.set_title(title, fontproperties=_CN_FONT_PROP, fontsize=14, fontweight="bold")
        if ylabel:
            ax.set_ylabel(ylabel, fontproperties=_CN_FONT_PROP, fontsize=10)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()

        return self._fig_to_b64(fig)

    def render_metric_card(
        self,
        metric_name: str,
        value: float,
        unit: str = "%",
        sub_metrics: dict[str, float] | None = None,
    ) -> str:
        """单一指标卡 —— 用于无 group_by 场景。"""
        fig, ax = plt.subplots(figsize=(5, 3.5))

        display_val = f"{value:.2f}{unit}" if value < 10 else f"{value:.1f}{unit}"
        ax.text(
            0.5, 0.55, display_val, transform=ax.transAxes,
            fontsize=36, fontweight="bold", ha="center", va="center", color="#176b87",
        )
        ax.text(
            0.5, 0.25, metric_name, transform=ax.transAxes,
            fontsize=14, ha="center", va="center", color="#344054",
            fontproperties=_CN_FONT_PROP,
        )

        if sub_metrics:
            sub_text = "  |  ".join(
                f"{k}: {v:,.0f}" if v >= 1 else f"{k}: {v:.2f}"
                for k, v in sub_metrics.items()
            )
            ax.text(
                0.5, 0.08, sub_text, transform=ax.transAxes,
                fontsize=9, ha="center", va="center", color="#667085",
            )

        ax.axis("off")
        fig.tight_layout()

        return self._fig_to_b64(fig)

    def render_multi_metric_bar(
        self,
        categories: list[str],
        metric_groups: dict[str, list[float]],
        title: str,
    ) -> str:
        """分组柱状图 —— 多指标对比。"""
        n_groups = len(categories)
        n_metrics = len(metric_groups)
        fig, ax = plt.subplots(figsize=(max(n_groups * 1.2, 6), 5))

        colors = ["#176b87", "#fb8500", "#219ebc", "#ffb703"]
        bar_width = 0.7 / n_metrics
        x = list(range(n_groups))

        for i, (metric_name, values) in enumerate(metric_groups.items()):
            offset = (i - n_metrics / 2 + 0.5) * bar_width
            bars = ax.bar(
                [xi + offset for xi in x], values, bar_width,
                label=metric_name, color=colors[i % len(colors)],
            )
            for bar, val in zip(bars, values, strict=True):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(max(v) for v in metric_groups.values()) * 0.02,
                    f"{val:.1f}" if val < 1 else f"{val:,.0f}",
                    ha="center", fontsize=7,
                )

        ax.set_xticks(x)
        ax.set_xticklabels(categories, fontproperties=_CN_FONT_PROP, fontsize=10, rotation=30)
        ax.set_title(title, fontproperties=_CN_FONT_PROP, fontsize=14, fontweight="bold")
        ax.legend(loc="upper right", prop=_CN_FONT_PROP if _CN_FONT_PROP else None)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()

        return self._fig_to_b64(fig)

    def _fig_to_b64(self, fig) -> str:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()
