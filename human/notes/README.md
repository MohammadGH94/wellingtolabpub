# notes/

Write whatever you like here. Nothing in this folder is generated, and nothing deletes it.

This exists because the vault's four content folders — `vault/papers/`, `vault/people/`,
`vault/topics/` and `vault/theses/` — are wiped and rewritten from OpenAlex on every
`python -m wellington_vault build`. A note you add to any of them survives until the next build and
then disappears without warning.

So: corrections to paper metadata, reading notes, drafts, lists of people to chase, questions to
ask at lab meeting — all of it belongs here instead.

No schema, no frontmatter, no naming convention. Plain markdown.

One suggestion: if you are recording a correction to something the vault got wrong, note the paper
or person it concerns and where the error actually lives. Errors in `vault/` almost always come
from upstream OpenAlex records rather than from this repo's code, and fixing them upstream
(https://openalex.org, which accepts corrections) is what makes the fix survive a rebuild.
