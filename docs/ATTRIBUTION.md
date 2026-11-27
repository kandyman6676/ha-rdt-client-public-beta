# Third-party attribution assessment — experimental beta

Copyright (c) 2026 kandyman6676. Project source is offered under the
[MIT License](../LICENSE). Retain the MIT copyright and license notice
in distributed substantial copies.

- This integration imports Home Assistant APIs, aiohttp and voluptuous;
  those dependencies are **not vendored** in this source tree. Their
  respective upstream licensing applies to separately obtained packages.
- The independent RDT-Client service is accessed through its HTTP API;
  no RDT-Client application source or executable is included.
- CI workflows reference GitHub-maintained Actions rather than bundling
  those Actions' source.
- The candidate code, tests and documentation were inspected for obvious
  vendored external source, copied upstream headers and third-party binaries.
  No separate third-party NOTICE obligation was identified in the reviewed
  source snapshot. This is a **scoped assessment, not independent proof
  of every contribution's authorship**.
- Before public publication, the rights holder should confirm whether
  any code was copied or adapted from third-party sources. If so, retain
  their required notices and reassess the licenses. Re-review if new
  third-party code, assets, or bundled dependencies are introduced.

This source is an **experimental public-beta candidate**, not an official
RDT-Client or Home Assistant project. Public distribution requires separate
authorization from the repository owner and confirmation of the necessary
rights to distribute the code. This assessment is not independent proof of
authorship or third-party provenance. Any copied or adapted source must retain
its required notices and comply with applicable licenses.
