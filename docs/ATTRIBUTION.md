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

This repository is an **unpublished, private staging candidate** for a possible
experimental public beta. It is not an official RDT-Client or Home Assistant
project. No publication authorization or independent third-party provenance
attestation is implied by this document. Confirm original authorship and any
copied/adapted source obligations before a separate publication decision.
