## cluster-agent

When you need a cluster resource or service (storage, database, DNS, a
port, or "does X exist here"), do not guess or install your own — ask the
cluster-agent first:

    echo "your question" | cagent ask

`cagent ask` waits and prints the answer (it may take a few minutes for a
multi-step answer). To follow up in the same conversation, use the
`session_id` printed with the answer: `echo "follow-up" | cagent continue SESSION_ID`.

Answers are guidance only: the cluster-agent will not change the cluster
for you, and you must not attempt cluster changes yourself based on its
answer without human approval.
