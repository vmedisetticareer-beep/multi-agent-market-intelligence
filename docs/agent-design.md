# Agent and Orchestrator Design

## Execution model

The exported implementation is a parent Orchestrator calling a sequential
research workflow. It does not implement agents independently delegating
tasks, choosing routes autonomously, or running as a parallel agent team.
Three Tavily search HTTP Request nodes and the data-processing nodes are part
of the workflow's ordered main path. OpenAI Chat Model nodes provide language
model reasoning to selected agent nodes.

## Orchestrator — Market Intelligence Orchestrator

- **Inputs:** Webhook POST values `company`, `industry`, `competitor_count`,
  and `news_days`; also supports a manual trigger.
- **Processing:** Maps values from the request body with root-level fallbacks.
  Missing `company` and `industry` become empty strings; missing numeric
  options default to 3 competitors and 30 news days. Validation rejects a
  blank trimmed company or industry. No numeric bounds are configured in this
  validation node.
- **Tool/integration:** Calls the `Market Intelligence` research sub-workflow
  with the four normalized values. The workflow export does not specify the
  Execute Workflow node's execution mode.
- **Outputs:** Valid requests return the sub-workflow result as JSON with
  HTTP 200. Invalid requests return HTTP 400 and
  `{"success": false, "error": "Company name and industry are required."}`.
- **Dependencies:** The research sub-workflow and its downstream Tavily,
  OpenAI, and parser/validation stages.

## Agent 1 — Competitor Discovery

- **Inputs:** Target company, industry, requested competitor count, and
  results from the preceding Tavily competitor search.
- **Processing:** Selects direct competitors supported by retrieved evidence.
  Prompt instructions request company name, competing product, rationale,
  target customers, source URLs, and confidence; prohibit invented
  competitors/products/URLs; and instruct the model to ignore instructions in
  retrieved content.
- **Tools:** A preceding Tavily HTTP Request searches general web results
  with basic search depth, up to 10 results, and no Tavily-generated answer.
  The agent is connected to an OpenAI Chat Model configured as
  `gpt-4.1-mini`.
- **Outputs:** JSON with a `competitors` array, followed by the
  `Parse Competitor JSON` node.
- **Dependencies:** The normalized request and Tavily search results.
- **Review note:** The Streamlit frontend fixes the requested count at three,
  consistent with the “top 3” system prompt and downstream requirement for
  exactly three profiles.

## Agent 2 — Product and News Research

In this export, Agent 2 is implemented as two Tavily HTTP Request nodes, not
as a separate OpenAI Agent node.

- **Inputs:** Parsed competitor records and their company/product context;
  the news node also uses `news_days`.
- **Processing:** Product search targets pricing, plans, features,
  capabilities, and target customers. The subsequent news search targets
  announcements, AI features, partnerships, and launches.
- **Tools:** Tavily POST requests to the public search API. Both use basic
  search depth and disable Tavily's generated answer. Product search uses
  general topic and up to 7 results; news search uses news topic and up to 5
  results with the configured time range. Authentication is by n8n
  credential reference; secret material is not documented here.
- **Outputs:** Product and news search result items for consolidation and
  extraction. Exact item fields follow the Tavily result structure.
- **Dependencies:** Agent 1's parsed competitor records and normalized
  `news_days`.

## Agent 3 — Intelligence Extraction

- **Inputs:** Consolidated competitor identity plus product-search and
  news-search data.
- **Processing:** Extracts comparable competitor facts. Its instructions
  limit claims to supplied evidence, prohibit invented facts, citations, and
  dates, and tell it to ignore instructions in retrieved content.
- **Tools:** OpenAI Chat Model configured as `gpt-4.1-mini`.
- **Outputs:** A JSON-style profile with `company_name`,
  `competing_product`, `pricing` (`model`, `published_prices`, `sources`),
  `core_features`, `target_customers`, `market_positioning`, `recent_news`,
  and `source_urls`. A following `Parse Intelligence JSON` node processes
  the output. No Structured Output Parser node is connected to this agent in
  the export.
- **Dependencies:** Consolidated competitor research.

## Agent 4 — Evidence and Claim Validation

Agent 4 consists of a deterministic evidence-matching node followed by an
OpenAI claim-review node. The two stages perform different checks and should
not be conflated.

### Evidence Validation

- **Inputs:** Extracted competitor profiles, consolidated Tavily search
  records, and cited `source_urls`.
- **Processing:** Matches profile to research by normalized company name.
  Compares cited URLs with product/news result URLs after trimming whitespace
  and trailing slashes. Marks a profile `Needs Review` if any cited URL is
  unmatched or no cited URL matches; otherwise marks it `Preliminary Pass`.
  Also records source, feature, and news counts and whether pricing is
  present.
- **Tools:** Workflow processing/code node; no independent web retrieval is
  configured for this check.
- **Outputs:** Profile with preliminary URL-match status and research
  metadata.
- **Dependencies:** Agent 3 extraction and consolidated Tavily records.

### Claim Verification

- **Inputs:** Extracted profile and preliminary evidence-validation results.
- **Processing:** Reviews pricing, features, positioning, and news; flags
  missing/unmatched citations and suspicious or potentially outdated claims;
  recommends corrective actions. The prompt explicitly says the agent has no
  independent web access, must not claim it opened or verified source pages,
  and must not treat a URL match as proof of claim accuracy.
- **Tools:** OpenAI Chat Model configured as `gpt-4.1-mini`, with a connected
  Structured Output Parser. The export includes additional Chat Model and
  parser connections for this agent; all exported Chat Model nodes use
  `gpt-4.1-mini`.
- **Outputs:** Claim-review JSON with `company_name`,
  `validation_summary`, `claims_needing_review` (claim, reason, recommended
  action), `pricing_review`, `news_review`, `recommended_actions`, and
  `overall_status`.
- **Dependencies:** Evidence Validation and Agent 3 profile.

The URL check confirms that a citation URL appeared in retrieved results; it
does not prove that the page supports the cited claim. A `Preliminary Pass`
must not be represented as independent factual verification.

## Agent 5 — Comparative Analysis

- **Inputs:** Target company and industry, plus three competitor profiles
  joined to their claim-verification reports by normalized company name.
- **Processing:** Synthesizes supplied evidence into a comparison, SWOT,
  opportunities, recommendations, and limitations. Instructions prohibit
  inventing facts or URLs, require distinguishing facts from interpretations,
  and tell the model to ignore instructions embedded in research material.
- **Tools:** OpenAI Chat Model configured as `gpt-4.1-mini`, with a
  Structured Output Parser connection. The export includes additional Chat
  Model and parser connections for this agent; all exported Chat Model nodes
  use `gpt-4.1-mini`.
- **Outputs:** Intended JSON fields include `target_company`, `industry`,
  `executive_summary`, `competitor_comparison`, `swot_analysis`,
  `market_opportunities`, `strategic_recommendations`,
  `research_limitations`, and `overall_conclusion`. The parser checks for
  `target_company`, `executive_summary`, `competitor_comparison`,
  `swot_analysis`, and `strategic_recommendations`, requires exactly three
  competitor comparison records, and adds
  `report_status: "Generated - Pending Final Review"`.
- **Dependencies:** Exactly three combined validated competitor profiles and
  the target company/industry context.

## Pipeline consistency notes

- The Streamlit control is fixed at three, matching Agent 1's system prompt,
  profile-combination check, and final parser.
- A direct/manual start of the research pipeline defaults missing target
  values to Salesforce and CRM software. The Orchestrator path rejects blank
  company or industry before calling the sub-workflow.
- The final parser's required-field checks are not identical to the
  Streamlit app's. The app also requires `research_limitations` and validates
  the SWOT sections. Verify compatibility with an actual exported execution
  response.
