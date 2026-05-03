"""Build an AI-first Obsidian vault from Dr. Cheryl Wellington's publications.

Pulls author + works data from OpenAlex (https://openalex.org), then renders
one note per paper, person, and topic — every note follows the AI-first vault
rules from the obsidian-second-brain skill (`## For future Claude` preamble,
rich frontmatter, [[wikilinks]] for every cross-reference).
"""

__version__ = "0.1.0"
