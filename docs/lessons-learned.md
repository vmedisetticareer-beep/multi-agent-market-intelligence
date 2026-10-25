# Lessons Learned

## JSON formatting and structured outputs

The project owner reports that malformed JSON from model-generated output
created integration problems, and that structured output parsers were added
to improve the shape and consistency of downstream data. This is an
owner-reported implementation history; consult the workflow export for the
specific parser nodes and their schemas. The Streamlit client independently
checks the final report's JSON structure and required fields before display.

Structured parsing reduces format ambiguity, but it does not establish that a
claim is true or that every required field is substantively useful. Validate
both schema and evidence content.

## Dynamic company research

The Streamlit interface accepts a company and industry at runtime, rather
than hard-coding a target company in the UI. The webhook payload also includes
the requested competitor count and news window. For the workflow to remain
dynamic, each of these values must reach the relevant agent prompts and
research queries; confirm that mapping in the exported workflow. Test with
different organizations and industries to catch prompt or expression
configuration that accidentally retains a fixed example.

## Workflow orchestration

The architecture is a parent n8n Orchestrator invoking a sequential
five-agent research pipeline. Explicit stage boundaries make it possible to
separate discovery, research, extraction, validation, and synthesis. They
also require careful mapping of intermediate data, consistent output schemas,
and clear handling of an upstream agent failure. This design is sequential
coordination, not independent delegation or autonomous task routing.

## API and webhook integration

The Streamlit app's JSON POST contract keeps the interface separate from the
workflow implementation. The app checks configuration and response shape and
surfaces transport and parsing errors. The request is synchronous from the
user's perspective: the interface waits for the n8n response up to the
configured timeout. The workflow must return a response compatible with the
frontend's documented report schema.

Credentials should remain in n8n's credential store, not in exported
documentation or source. The webhook should have access controls appropriate
to its deployment environment; non-empty input validation alone is not caller
authentication.

## Security risks identified

Static review of the exported workflow files found:

- **🟡 MEDIUM:** The active Orchestrator webhook has no configured
  authentication. If the n8n instance is reachable by untrusted callers, a
  caller can trigger research and use configured provider resources.
- **⚪ LOW:** The exports contain credential references and
  deployment-specific workflow/instance identifiers. These are metadata, not
  embedded API keys or bearer-token values, but should be sanitized before
  public release.
- **Not found:** No embedded API key, bearer-token value, or authorization
  header was identified in the workflow exports reviewed.

These are current security/publication risks, not future enhancements.
Sanitized, inactive public copies are provided under `workflow/public/`.
Original exports remain unchanged and are excluded from Git. The public copies
require provider credentials to be reselected and the Orchestrator's
sub-workflow reference to be confirmed after import.

## Evidence validation limitations

An agent can check whether a research claim appears supported by retrieved
material, but that is not equivalent to independent fact verification.
Search coverage, page availability, source authority, freshness, and conflicting
evidence all affect the result. Preserve source URLs and associate them with
individual claims so reviewers can inspect the basis for conclusions.
Represent missing or conflicting evidence as uncertainty rather than
asserting certainty.

## Resource management

The sequential workflow can make multiple external search and model calls for
one user request. Without execution logs and measurements, the cost, latency,
rate-limit behavior, and resource needs are unknown. Set realistic timeouts,
bound the requested competitor count and search scope, and monitor provider
usage. Consider asynchronous status updates if longer runs make the synchronous
request difficult to use.

## Future improvements (planned)

- Add automated tests for final JSON schema, each intermediate agent contract,
  empty input, malformed model output, and webhook error paths.
- Add a sanitized workflow fixture and documented test scenarios that can be
  repeated without live provider calls.
- Preserve and render source citations at claim level, including publication
  dates where available.
- Define explicit confidence, uncertainty, and conflict-handling rules.
- Add retry/backoff and graceful failure behavior for provider errors, while
  preventing duplicate or unbounded calls.
- Measure provider usage, end-to-end duration, failure rates, and output
  quality using a reviewed evaluation set before making quantitative claims.
- Improve long-running request UX with progress/status feedback or
  asynchronous job tracking if operational testing supports the need.
- Add webhook authentication or gateway controls and sanitize workflow
  metadata before publication. The copies are sanitized for metadata, but
  authentication has not been added; the webhook must be protected before
  activation or public exposure.
