# Project Demonstration Script (3–5 minutes)

## Before the demo

- Prepare the Streamlit app and n8n workflows in your demonstration
  environment before the session. Do not expose credentials on screen.
- Confirm which research mode you will show. Demo Mode is fictional. Live
  Research invokes n8n and external Tavily/OpenAI services; use it only when
  those services and credentials are configured and you are ready to make a
  live request.
- Have the two exported workflows open in n8n. If showing a prior Salesforce
  execution, use a real sanitized execution record; the reported test is not
  independently verified by this documentation review.

## 0:00–0:30 — Business problem and value

**Say:** “Competitive research brings together competitor discovery, product
and news research, evidence checking, and synthesis. This project organizes
those steps into a sequential, multi-agent pipeline and presents the
structured result in a Streamlit dashboard.”

**Show:** The Streamlit dashboard title.

## 0:30–1:10 — Streamlit experience and dynamic inputs

**Show:** The sidebar fields for company, industry, competitor count, news
period, and research mode.

**Say:** “The user provides the organization and industry at runtime, selects
the analysis window, and chooses Demo Mode or Live Research. Demo Mode is
fictional and makes no webhook call. Live Research sends the selected inputs
to the n8n webhook.”

Enter a company and industry. Point out that the competitor count is fixed at
three to match the exported pipeline's three-profile output.

## 1:10–1:50 — Show a final analysis

**Preferred live presentation:** If the configured workflow is available and
the audience has been told a live external request will be made, select Live
Research and run the prepared company analysis. Show the returned summary,
comparison, SWOT, recommendations, and limitations. Do not show credentials
or unredacted execution metadata.

**Fallback:** In Demo Mode, run the analysis and emphasize the fictional-data
notice. If no verified live result is available, do not present the demo
content as Salesforce, Adobe, or any other actual company's research.

## 1:50–2:35 — Explain the n8n architecture

**Show:** The Orchestrator workflow and then the research sub-workflow.

**Say:** “The parent Orchestrator receives the webhook request, normalizes
the fields, validates the company and industry, and calls the research
sub-workflow. The pipeline then runs in sequence. This is coordinated
workflow execution—not independent agent delegation or autonomous task
routing.”

## 2:35–3:35 — Show the agent stages and evidence controls

**Show:** The Tavily request nodes, Agent 1, the product/news research nodes,
Agent 3, Agent 4's validation and claim review, and Agent 5 with its parser.

**Say:** “Tavily supplies competitor, product, and news search results. The
agents extract competitor profiles, compare cited URLs with retrieved
results, review claims, and synthesize a final briefing. The URL match is a
preliminary evidence check, not proof that a source supports a claim. The
claim-review prompt also states it has no independent web access.”

## 3:35–4:30 — Review the output and close

**Show:** The final report in Streamlit or a sanitized n8n execution output;
point to the executive summary, competitor comparison, SWOT, recommendations,
and research limitations. Explain that the final parser marks the report
`Generated - Pending Final Review`.

**Say:** “The report is structured for business review, but automated format
checks and URL matching do not replace human verification. The next steps
are to align requested competitor counts with the pipeline, secure the
webhook, retain inspectable citations, and evaluate results with documented
test evidence.”
