# RDT-Client for Home Assistant — experimental beta

**Status:** Experimental public-beta candidate — prepared in a private staging
repository. Publication has not been authorized or performed. This is not a
production-certified or official RDT-Client / Home Assistant integration.

A small, read-only Home Assistant custom integration for the independent
[RDT-Client](https://github.com/rogerfar/rdt-client) service.

## Six sensors

| Sensor | Behavior |
| --- | --- |
| Downloading count | Counts download-related states, including stalled jobs; not a measure of bytes currently transferring |
| Download speed | Uses the server-reported global download rate; nonzero live unit compatibility has not been validated |
| Last download completed | Latest valid `completion_on` timestamp visible in the queue, or Unknown |
| Premium status | Active, Inactive, or Unknown |
| Premium expiration | Provider expiration timestamp, **not a guaranteed renewal date** |
| Premium days remaining | Calendar days until provider expiration |

### Experimental completion timestamp — important

**Whether a real RDT-Client nonempty queue reports `completion_on` has not
yet been verified.** The observed live queue was empty. Missing, invalid,
future, or otherwise unusable timestamps must not be replaced with polling
times or guesses. Without a valid completion timestamp the sensor remains
**Unknown** until valid data is observed or a previously valid timestamp is
restored. A completion may be missed if its queue entry disappears between
polls. This feature is experimental.

## Privacy and security

The integration reads authenticated API endpoints for queue/transfer and
subscription metadata. It does **not** expose names, hashes, save paths,
private account records, or tokens as sensor values or attributes. The login
uses credentials entered into Home Assistant; those credentials are kept by
Home Assistant's config-entry storage, not published as sensor attributes.
Use HTTPS with certificate verification; HTTP on untrusted networks exposes
traffic and login credentials. Sensor updates poll approximately every 30 s.
No storage, disk-capacity, filesystem probe, native Linux adapter, or
administrative write functionality is included.

## Installing in a separately authorized test Home Assistant instance

This candidate has not been published as a HACS release or listed in HACS.
**Do not install into a production Home Assistant instance without separate
review and authorization.**
For an authorized isolated tester, copy `custom_components/rdt_client`
into the Home Assistant configuration directory's `custom_components`
folder. Restart only the authorized test instance and use
**Settings → Devices & services → Add integration → RDT-Client**.
Enter your existing server URL and credentials. The server must be
accessible to that test Home Assistant instance.

## Experimental beta validation and limitations

This is a proposed public-beta distribution, not a production-readiness claim.
Before public publication, confirm original-code authorship and any third-party
attribution requirements described in [ATTRIBUTION.md](docs/ATTRIBUTION.md).
A repository visibility change, HACS release, installation, or deployment
requires distinct approval. The `completion_on` feature and nonzero transfer
speed unit behavior remain unverified against a real populated queue.

The minimal API/privacy, Home Assistant compatibility smoke/lifecycle,
and security workflows apply to this clean-history distribution. Passing
automated tests does not prove live RDT-Client completion-timestamp
compatibility or production readiness.

**License:** [MIT](LICENSE), Copyright (c) 2026 kandyman6676.
See [third-party attribution assessment](docs/ATTRIBUTION.md).
This is not endorsed by or affiliated with the upstream RDT-Client
or Home Assistant projects. Distribution/publication requires separate
authorization from the repository owner.
