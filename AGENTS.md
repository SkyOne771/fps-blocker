# Repository instructions

Keep the public documentation synchronized with the code in the same commit or
pull request. For runtime or workflow changes, update README.md or a relevant
file in docs/ to explain behavior, setup, limitations or validation. A cosmetic
change unrelated to the implementation does not satisfy this requirement.

Before pushing:

- Run `python -m unittest discover -s tests -v` and `git diff --check`.
- Run `python tools/check_docs_sync.py --base origin/main --head HEAD` on the
  committed branch. Use the previous commit as the base for a direct main update.
- Keep relative documentation links and screenshots valid.
- Distinguish display refresh rate from GPU-rendered FPS. Do not claim a physical
  hardware test, symptom resolution, or performance improvement without evidence.
- Keep private FreeSync backups and local diagnostic reports out of Git.

The GitHub documentation check detects missing accompanying documentation and
broken local link/image targets. It cannot judge whether prose is accurate;
review the documentation against the actual implementation.
