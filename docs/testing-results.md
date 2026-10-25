# Testing Results

## Evidence and reporting convention

This document separates user-reported executions from behavior confirmed by
source inspection. The reported workflow runs were not independently
re-executed for this documentation update. No services or external APIs were
started or called during the review. No accuracy, latency, or performance
metrics are claimed.

## User-reported successful tests (not independently verified)

The project owner reports the following successful tests:

- **Streamlit Demo Mode:** successfully displayed the dashboard's fictional
  demonstration analysis.
- **Research pipeline — Salesforce:** the n8n pipeline completed a reported
  research execution for Salesforce.
- **Research pipeline — Adobe:** the n8n pipeline completed a reported
  research execution for Adobe.
- **Streamlit-to-n8n Live Research — Salesforce:** a reported end-to-end run
  sent the Streamlit request to n8n and returned a Salesforce analysis.
- **Empty-input webhook validation:** the webhook's validation rejected a
  request with empty input, as reported by the project owner.

These results are recorded as user-reported because execution logs, saved
request/response payloads, and test records were not provided as
independently inspectable evidence in this review. The project screenshots
include the Streamlit results display and workflow layouts, but they do not
establish the accuracy of report claims or provide n8n execution records.

## Implementation behavior confirmed by source inspection (not run here)

`app.py` provides the following implementation behavior:

- Demo Mode is selected by default and renders explicitly fictional sample
  data without making the webhook request.
- Blank company or industry input is rejected in the Streamlit form.
- Competitor count is fixed at 3 to match the n8n pipeline; news-period
  choices are 7, 30, and 90 days.
- Live mode sends a JSON POST with `company`, `industry`,
  `competitor_count`, and `news_days`.
- The client validates the webhook URL and positive numeric timeout and
  surfaces HTTP, connection, timeout, decoding, JSON, and report-shape errors.
- A successful report must include `executive_summary`,
  `competitor_comparison`, `swot_analysis`, `strategic_recommendations`, and
  `research_limitations`; the SWOT object must include all four SWOT sections.
- The app accepts a single-item n8n `[{ "json": { ... } }]` response wrapper
  and displays the report sections.

This verifies that the behaviors are implemented in source, not that each was
executed in a browser or against a live webhook during this review.

## Workflow configuration confirmed by static export inspection (not executed)

The exported workflows show the following configured behavior:

- The Orchestrator routes non-empty company/industry to the research
  sub-workflow, returns its report with HTTP 200, and has a separate HTTP 400
  empty-input response.
- The research workflow contains three Tavily search requests, OpenAI
  `gpt-4.1-mini` model nodes, JSON parsing stages, and structured output
  parsers connected to claim review and comparative analysis.
- The final pipeline combines exactly three competitor profiles.
- The claim-validation flow compares cited URLs to Tavily result URLs; it
  does not independently establish that the source content supports each
  claim.

Static configuration inspection is not an execution test and does not prove
that the active deployed workflow matches the exports.

## Security review findings (static inspection)

- **🟡 MEDIUM:** The active Orchestrator webhook has no configured
  authentication. If reachable by untrusted callers, it can trigger research
  using configured Tavily/OpenAI resources.
- **⚪ LOW:** Workflow exports contain n8n credential references and
  deployment/workflow identifiers. These are sensitive operational metadata,
  not embedded provider keys or bearer tokens; sanitize them before public
  release.
- **No embedded API key, bearer-token value, or authorization header was
  found** in the reviewed workflow exports.

The review was static only. It did not test a deployed endpoint's network
reachability, authentication, or actual credentials.

## Reported issue and improvement

The project owner reports encountering malformed JSON in the agent/workflow
output and subsequently improving output reliability with structured output
parsers. The exported configuration confirms Structured Output Parser nodes
are connected to claim review and final comparative analysis, with automatic
fix enabled; other stages use explicit JSON parsing nodes. This confirms
configuration, not the reported improvement in runtime reliability. The
current frontend also rejects invalid JSON and malformed report shapes.

## Untested or unverified scenarios

- Re-execution of Demo Mode, Salesforce, Adobe, and empty-input tests by this
  review.
- Current Salesforce live analysis and other real-company research runs.
- Provider behavior, source coverage, citation quality, and factual accuracy.
- Evidence/claim validation effectiveness, including unsupported or
  conflicting-source cases.
- Workflow behavior under Tavily/OpenAI failures, rate limits, retries,
  malformed intermediate agent outputs, or n8n execution timeouts.
- Authentication and access control for a deployed webhook.
- Whether a deployed Orchestrator's final JSON response matches every field
  and validation requirement in Streamlit.
- Automated unit, integration, or end-to-end test suite; no such suite is
  included in the supplied application files.

## Recommended submission evidence

For a stronger audit trail, attach sanitized screenshots or execution
summaries for the owner-reported runs. Remove company-sensitive inputs,
personal data, webhook URLs, execution identifiers, credentials, and tokens.
For repeatable testing, document expected input, expected output, observed
result, and the matching sanitized n8n execution for each scenario.
