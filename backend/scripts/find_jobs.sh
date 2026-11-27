#!/bin/sh
# linkedin job search w/ claude in chrome, chrome has to be open + logged in
# ./scripts/find_jobs.sh analysis.json   (- = stdin, thats what /jobs/linkedin uses)
# prompt goes before --allowedTools or it gets swallowed
claude -p "My job search: $(cat "$1")

Open a new Chrome tab and use LinkedIn Jobs (I'm logged in) to search the first 2
example_titles of each role in my preferred locations. Read-only: never apply, save, message, or follow.
Return the 10 best-fitting postings as JSON: [{title, company, location, url, why_it_fits}]" \
  --chrome --allowedTools "mcp__claude-in-chrome"
