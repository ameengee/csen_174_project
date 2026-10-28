#!/bin/sh
# Search LinkedIn Jobs for the job targets proposed by /profile/analyze. Read-only.
# Needs Chrome open, logged into LinkedIn, with the Claude in Chrome extension.
# Usage: curl -F file=@profile.pdf localhost:8000/profile/analyze > analysis.json
#        ./scripts/find_jobs.sh analysis.json
# The prompt goes first: --allowedTools takes a list and would swallow it.
claude -p "My job-search analysis: $(cat "$1")

Open a new Chrome tab and use LinkedIn Jobs (I'm logged in) to search the first 2
example_titles of each job target in my preferred locations. Read-only: never apply, save, message, or follow.
Return the 10 best-fitting postings as JSON: [{title, company, location, url, why_it_fits}]" \
  --chrome --allowedTools "mcp__claude-in-chrome"
