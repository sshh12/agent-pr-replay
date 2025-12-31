I want to build a cool stats/visualizer for AI coding agents, particularly based around claude code. 

I want you to explore
- claude --help (esp --session-id, --settings)
- the ~/.claude folder for session history

I'm thinking we do this as a cli-based python packagable thing thats easy for folks to setup on their own directly from the github repo.


overall flow is like
1. given a repo e.g. we can test with https://github.com/django/django
2. clone it somewhere tmp
3. use maybe the gh cli to find merged PRs over the last N days
4. use claude cli as an llm api to pick top K (configurable) representative (diverse and non trivla) changes
5. for those, sequentially create a worktree from the same base commit as that PR. Lets use claude cli to first reverse the diff of the PR into a prompt that a human might use to create it. Then spawn a claude with settings that allow it all common read only bash commands (find, jq, etc) and read/write in that worktree. given only that human prompt as input.
6. once done combine all the session histories (should contain all the commands) into some maybe json database that can be used for later analysis

maybe we start with this and then in phase 2 we analyze that db for cool visuals we could make.

like top cli commands used, heat map of files read, make a decision tree for how it navigated the codebase for various changes. we really want to understand how the coding agents "understand" the repo.

lets always set --model sonnet, note we are using claude as both just an llm api but also the coding agent we are evaluating

the cli we build for using this should be clean and intuitve for folks to use this with its repo

you may be able to use your own claude code docs task to also figure out settings etc you can use to build this.