import json
import os
from collections.abc import Mapping
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import streamlit as st
from dotenv import load_dotenv


load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")


def get_webhook_timeout() -> float:
    raw_timeout = os.environ.get("N8N_TIMEOUT_SECONDS", "300")
    try:
        timeout = float(raw_timeout)
    except ValueError as error:
        raise ValueError("N8N_TIMEOUT_SECONDS must be a positive number.") from error
    if timeout <= 0:
        raise ValueError("N8N_TIMEOUT_SECONDS must be a positive number.")
    return timeout


def validate_report(report: object) -> dict:
    if isinstance(report, list) and len(report) == 1:
        report = report[0]
    if isinstance(report, Mapping) and isinstance(report.get("json"), Mapping):
        report = report["json"]
    if not isinstance(report, Mapping):
        raise ValueError("The webhook response must be a JSON object.")

    required_fields = (
        "executive_summary",
        "competitor_comparison",
        "swot_analysis",
        "strategic_recommendations",
        "research_limitations",
    )
    missing_fields = [field for field in required_fields if field not in report]
    if missing_fields:
        raise ValueError(
            "The webhook response is missing required report fields: "
            + ", ".join(missing_fields)
        )

    summary = report["executive_summary"]
    comparison = report["competitor_comparison"]
    swot = report["swot_analysis"]
    recommendations = report["strategic_recommendations"]
    limitations = report["research_limitations"]

    if not isinstance(summary, str):
        raise ValueError("'executive_summary' must be text.")
    if isinstance(comparison, Mapping):
        comparison = comparison.get("competitors")
    if not isinstance(comparison, list) or any(
        not isinstance(competitor, Mapping) for competitor in comparison
    ):
        raise ValueError("'competitor_comparison' must be a list of objects.")
    if not isinstance(swot, Mapping):
        raise ValueError("'swot_analysis' must be an object.")
    swot_sections = {str(section).casefold() for section in swot}
    missing_swot_sections = [
        section
        for section in ("strengths", "weaknesses", "opportunities", "threats")
        if section not in swot_sections
    ]
    if missing_swot_sections:
        raise ValueError(
            "'swot_analysis' is missing sections: " + ", ".join(missing_swot_sections)
        )
    if not isinstance(recommendations, list):
        raise ValueError("'strategic_recommendations' must be a list.")
    if not isinstance(limitations, (str, list)):
        raise ValueError("'research_limitations' must be text or a list.")

    return {
        "executive_summary": summary,
        "competitor_comparison": comparison,
        "swot_analysis": swot,
        "strategic_recommendations": recommendations,
        "research_limitations": limitations,
    }


def request_live_report(
    webhook_url: str,
    payload: dict[str, object],
    timeout: float,
) -> dict:
    parsed_url = urlparse(webhook_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("N8N_WEBHOOK_URL must be a valid HTTP or HTTPS URL.")

    request = Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            response_body = response.read()
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace").strip()
        if len(detail) > 500:
            detail = detail[:500] + "..."
        message = f"Webhook returned HTTP {error.code}."
        if detail:
            message += f" Response: {detail}"
        raise RuntimeError(message) from error
    except (TimeoutError, URLError, OSError, HTTPException) as error:
        raise RuntimeError(
            f"Could not reach the n8n webhook: {error}. "
            f"Check the URL and timeout ({timeout:g} seconds)."
        ) from error

    try:
        response_body = response_body.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("The webhook response was not valid UTF-8 text.") from error
    try:
        report = json.loads(response_body)
    except json.JSONDecodeError as error:
        raise ValueError("The webhook response was not valid JSON.") from error
    return validate_report(report)


def display_points(value: object) -> None:
    if isinstance(value, list):
        for item in value:
            st.markdown(f"- {item}")
    else:
        st.write(value)


st.set_page_config(
    page_title="Market Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 3rem; }
        .app-subtitle { color: #64748b; margin-top: -0.6rem; }
        .demo-notice {
            padding: 0.8rem 1rem;
            border: 1px solid #bfdbfe;
            border-radius: 0.5rem;
            background: #eff6ff;
            color: #1e3a8a;
            margin: 0.5rem 0 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Market Intelligence Dashboard")
st.markdown(
    '<p class="app-subtitle">A focused view of your competitive landscape.</p>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Analysis setup")
    company = st.text_input("Company Name", placeholder="e.g., Acme Analytics")
    industry = st.text_input("Industry", placeholder="e.g., Business software")
    competitor_count = st.number_input(
        "Number of Competitors",
        min_value=3,
        max_value=3,
        value=3,
        step=1,
        disabled=True,
    )
    news_period = st.selectbox(
        "News Period",
        options=[7, 30, 90],
        format_func=lambda days: f"{days} days",
    )
    research_mode = st.radio(
        "Research mode",
        options=["Demo Mode", "Live Research"],
        index=0,
    )
    run_analysis = st.button(
        "Run Competitor Analysis",
        type="primary",
        width="stretch",
    )
    if research_mode == "Live Research":
        st.caption(
            "Live Research sends the entered company and industry to the "
            "configured n8n webhook."
        )
    else:
        st.caption("Demo results are fictional and do not call n8n.")

if run_analysis:
    st.session_state.pop("demo_analysis", None)
    st.session_state.pop("live_analysis", None)

    if not company.strip() or not industry.strip():
        st.error("Enter both a company name and an industry to continue.")
    elif research_mode == "Demo Mode":
        st.session_state["demo_analysis"] = {
            "company": company.strip(),
            "industry": industry.strip(),
            "competitor_count": int(competitor_count),
            "news_period": news_period,
        }
    else:
        webhook_url = os.environ.get("N8N_WEBHOOK_URL", "").strip()
        if not webhook_url:
            st.error(
                "N8N_WEBHOOK_URL is not set. Configure it before using Live "
                "Research; Demo Mode remains available without it."
            )
        else:
            payload = {
                "company": company.strip(),
                "industry": industry.strip(),
                "competitor_count": int(competitor_count),
                "news_days": news_period,
            }
            try:
                timeout = get_webhook_timeout()
                with st.status(
                    f"Waiting for live research (up to {timeout:g} seconds)...",
                    expanded=True,
                ) as status:
                    st.write("Submitting the request and waiting for n8n.")
                    try:
                        report = request_live_report(webhook_url, payload, timeout)
                    except (ValueError, RuntimeError):
                        status.update(label="Live research failed.", state="error")
                        raise
                    status.update(label="Live research complete.", state="complete")
                st.session_state["live_analysis"] = {
                    "company": company.strip(),
                    "industry": industry.strip(),
                    "competitor_count": int(competitor_count),
                    "news_period": news_period,
                    "report": report,
                }
            except (ValueError, RuntimeError) as error:
                st.error(str(error))

demo_analysis = st.session_state.get("demo_analysis")
live_analysis = st.session_state.get("live_analysis")

if demo_analysis:
    company = demo_analysis["company"]
    industry = demo_analysis["industry"]
    competitor_count = demo_analysis["competitor_count"]
    news_period = demo_analysis["news_period"]

    st.markdown(
        '<div class="demo-notice"><strong>Demo Mode:</strong> '
        "All organizations, metrics, and market signals below are fictional "
        "illustrations, not current research.</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        f"Illustrative profile for **{company}** · {industry} · "
        f"{competitor_count} sample competitors · {news_period}-day news window"
    )

    st.header("Executive Summary")
    st.write(
        f"This fictional {news_period}-day snapshot illustrates how "
        f"{company} might assess its position in the {industry} market. "
        "The sample landscape points to an opportunity to sharpen "
        "differentiation and make customer outcomes easier to compare. "
        "No live company, competitor, or news data was gathered."
    )

    st.header("Competitor Comparison")
    sample_names = [
        "Northstar Labs",
        "Cedar Peak Systems",
        "Bluehaven Works",
        "Redwood Signal",
        "Brightline Harbor",
        "Summit Field Group",
        "Silvermaple Studio",
        "Westward Metric",
        "Openwater Collective",
        "Pinecrest Logic",
    ]
    sample_positions = [
        "Broad platform",
        "Specialist provider",
        "Value-focused",
        "Enterprise suite",
        "Product-led",
        "Service-led",
        "Emerging challenger",
        "Niche specialist",
        "Regional provider",
        "Integrated platform",
    ]
    sample_momentum = ["Growing", "Steady", "Building", "Steady", "Growing"]
    comparison_rows = [
        {
            "Fictional competitor": sample_names[index],
            "Illustrative positioning": sample_positions[index],
            "Sample momentum": sample_momentum[index % len(sample_momentum)],
        }
        for index in range(competitor_count)
    ]
    st.dataframe(comparison_rows, hide_index=True, width="stretch")

    st.header("SWOT Analysis")
    swot_columns = st.columns(4)
    swot_sections = [
        (
            "Strengths",
            [
                "Existing customer knowledge can inform clearer positioning.",
                "A focused offer may support faster iteration.",
            ],
        ),
        (
            "Weaknesses",
            [
                "Differentiators may be difficult to communicate consistently.",
                "Limited visibility can make market shifts harder to spot.",
            ],
        ),
        (
            "Opportunities",
            [
                "Clarify value around a specific customer need.",
                "Use customer outcomes to strengthen proof points.",
            ],
        ),
        (
            "Threats",
            [
                "Established providers may have stronger brand recognition.",
                "Changing buyer expectations could increase comparison pressure.",
            ],
        ),
    ]
    for column, (heading, points) in zip(swot_columns, swot_sections):
        with column:
            st.subheader(heading)
            display_points(points)

    st.header("Strategic Recommendations")
    recommendations = [
        (
            "Sharpen the value proposition",
            "Describe the primary customer, problem, and measurable outcome "
            "in language that is easy to compare.",
        ),
        (
            "Build proof around customer outcomes",
            "Collect concise examples that demonstrate the value delivered "
            "and make them easy for buyers to evaluate.",
        ),
        (
            f"Review market signals every {news_period} days",
            "Use a consistent review cadence to note changes in competitor "
            "messaging, launches, and customer priorities.",
        ),
    ]
    for index, (title, detail) in enumerate(recommendations, start=1):
        st.markdown(f"**{index}. {title}**  \n{detail}")

elif live_analysis:
    report = live_analysis["report"]
    st.caption(
        f"Live research for **{live_analysis['company']}** · "
        f"{live_analysis['industry']} · "
        f"{live_analysis['competitor_count']} competitors · "
        f"{live_analysis['news_period']}-day news window"
    )

    st.header("Executive Summary")
    st.write(report["executive_summary"])

    st.header("Competitor Comparison")
    if report["competitor_comparison"]:
        st.dataframe(
            report["competitor_comparison"],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("The report contains no competitor comparison entries.")

    st.header("SWOT Analysis")
    swot = report["swot_analysis"]
    swot_columns = st.columns(4)
    for column, heading in zip(
        swot_columns,
        ("Strengths", "Weaknesses", "Opportunities", "Threats"),
    ):
        with column:
            st.subheader(heading)
            value = next(
                (
                    item
                    for key, item in swot.items()
                    if str(key).casefold() == heading.casefold()
                ),
                "Not provided.",
            )
            display_points(value)

    st.header("Strategic Recommendations")
    recommendations = report["strategic_recommendations"]
    if recommendations:
        for index, recommendation in enumerate(recommendations, start=1):
            if isinstance(recommendation, Mapping):
                title = recommendation.get("title", f"Recommendation {index}")
                detail = recommendation.get(
                    "details",
                    recommendation.get("description", recommendation),
                )
                st.markdown(f"**{index}. {title}**")
                st.write(detail)
            else:
                st.markdown(f"{index}. {recommendation}")
    else:
        st.info("The report contains no strategic recommendations.")

    st.header("Research Limitations")
    display_points(report["research_limitations"])
else:
    st.info(
        "Enter a company and industry, then run the analysis. "
        "Demo Mode is selected by default; Live Research requires "
        "N8N_WEBHOOK_URL."
    )
