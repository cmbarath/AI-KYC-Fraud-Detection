import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List

DARK_LAYOUT_TEMPLATE = dict(
    paper_bgcolor="#131b2e",
    plot_bgcolor="#131b2e",
    font=dict(color="#f8fafc", family="Inter, sans-serif"),
    margin=dict(l=20, r=20, t=40, b=20)
)

def create_risk_gauge(risk_score: int, risk_tier: str) -> go.Figure:
    """Builds an interactive speedometer gauge for the 0-100 fraud risk score."""
    colors = {
        "LOW": "#10b981",
        "MEDIUM": "#f59e0b",
        "HIGH": "#f97316",
        "CRITICAL": "#dc2626"
    }
    bar_color = colors.get(risk_tier, "#3b82f6")

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=risk_score,
        title={'text': f"Fraud Risk Score: {risk_tier}", 'font': {'size': 20, 'color': bar_color}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#94a3b8"},
            'bar': {'color': bar_color, 'thickness': 0.28},
            'bgcolor': "#1e293b",
            'borderwidth': 1,
            'bordercolor': "#334155",
            'steps': [
                {'range': [0, 25], 'color': 'rgba(16, 185, 129, 0.2)'},
                {'range': [25, 55], 'color': 'rgba(245, 158, 11, 0.2)'},
                {'range': [55, 80], 'color': 'rgba(249, 115, 22, 0.2)'},
                {'range': [80, 100], 'color': 'rgba(220, 38, 38, 0.25)'}
            ],
            'threshold': {
                'line': {'color': "#ffffff", 'width': 3},
                'thickness': 0.8,
                'value': risk_score
            }
        }
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f8fafc"),
        height=260,
        margin=dict(l=20, r=20, t=30, b=10)
    )
    return fig

def create_shap_waterfall_bar(top_drivers: List[Dict[str, Any]], top_mitigators: List[Dict[str, Any]]) -> go.Figure:
    """Generates horizontal bar chart showing positive and negative SHAP impact factors."""
    items = []
    for d in top_drivers:
        items.append({"label": d.get("label", d.get("feature")), "value": d.get("shap_value", 0), "type": "Risk Driver (+)"})
    for m in top_mitigators:
        items.append({"label": m.get("label", m.get("feature")), "value": m.get("shap_value", 0), "type": "Mitigating Factor (-)"})

    if not items:
        fig = go.Figure()
        fig.add_annotation(text="No SHAP explanation features available", showarrow=False)
        return fig

    labels = [i["label"] for i in items]
    vals = [i["value"] for i in items]
    colors = ["#ef4444" if v > 0 else "#10b981" for v in vals]

    fig = go.Figure(go.Bar(
        x=vals,
        y=labels,
        orientation='h',
        marker=dict(color=colors, line=dict(color="#334155", width=1))
    ))

    fig.update_layout(
        title="Key Factors Driving the Fraud Decision (SHAP)",
        xaxis_title="SHAP Value (Contribution to Fraud Probability)",
        yaxis=dict(autorange="reversed"),
        paper_bgcolor="#182238",
        plot_bgcolor="#131b2e",
        font=dict(color="#f8fafc", size=11),
        height=300,
        margin=dict(l=10, r=20, t=40, b=20)
    )
    return fig

def create_model_comparison_bar(models_metrics: Dict[str, Any]) -> go.Figure:
    """Creates benchmark comparison bar chart of accuracy, ROC-AUC, Precision, Recall, F1."""
    models = list(models_metrics.keys())
    metrics = ["roc_auc", "f1_score", "precision", "recall"]
    metric_labels = ["ROC-AUC", "F1 Score", "Precision", "Recall"]
    palette = ["#3b82f6", "#10b981", "#8b5cf6"]

    fig = go.Figure()
    for idx, model_name in enumerate(models):
        m_vals = [models_metrics[model_name].get(m, 0.0) for m in metrics]
        clean_name = model_name.replace("_", " ").title()
        fig.add_bar(
            name=clean_name,
            x=metric_labels,
            y=m_vals,
            marker_color=palette[idx % len(palette)]
        )

    fig.update_layout(
        barmode='group',
        title="ML Algorithm Benchmark Performance Comparison",
        yaxis=dict(range=[0.75, 1.02], gridcolor="#24324f"),
        paper_bgcolor="#182238",
        plot_bgcolor="#131b2e",
        font=dict(color="#f8fafc"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=320,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

def create_risk_distribution_donut(tier_counts: Dict[str, int]) -> go.Figure:
    """Creates donut chart of applications by risk tier."""
    labels = list(tier_counts.keys())
    values = list(tier_counts.values())
    colors = {
        "LOW": "#10b981",
        "MEDIUM": "#f59e0b",
        "HIGH": "#f97316",
        "CRITICAL": "#dc2626"
    }
    color_seq = [colors.get(k, "#94a3b8") for k in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.55,
        marker=dict(colors=color_seq, line=dict(color="#0f172a", width=2))
    )])

    fig.update_layout(
        title="Application Portfolio by Risk Tier",
        paper_bgcolor="#182238",
        plot_bgcolor="#131b2e",
        font=dict(color="#f8fafc"),
        height=280,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    return fig
