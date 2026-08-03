## cluster-agent

When you need a cluster resource or service (storage, database, DNS, a
port, or "does X exist here"), do not guess or install your own — ask the
cluster-agent first. A real answer can take **several minutes**
(multi-step turns have taken up to ~4 minutes), which is longer than your
own shell/bash tool's default timeout — do not run a plain, waiting
`cagent ask`/`cagent continue` as a single short tool call, or your tool
call will be killed before the answer arrives even though the
cluster-agent kept working and the answer completes anyway.

Instead, submit without waiting, then check back separately:

    echo "your question" | cagent ask --no-wait
    # prints {"request_id": "req_...", "session_id": "ses_...", "state": "queued"} immediately

Then, after doing something else or waiting a bit, fetch the result (repeat
if it still says `queued`/`running`; give it several minutes before
concluding it failed):

    cagent status REQUEST_ID

To follow up in the same conversation once you have an answer, use the
`session_id` from the first response, again with `--no-wait` + `status`:

    echo "follow-up" | cagent continue SESSION_ID --no-wait
    cagent status REQUEST_ID

If you do want to block and wait in one call (`cagent ask` with no flags),
pass your shell tool a generous timeout (10+ minutes) — never a short one.

Answers are guidance only: the cluster-agent will not change the cluster
for you, and you must not attempt cluster changes yourself based on its
answer without human approval.
