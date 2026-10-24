# Working on Jianying Headless

This repository is the native-draft interoperability companion to [Haoyong Video](https://github.com/Milllkey/haoyong-video). Read `README.md`, `docs/GETTING-STARTED.md`, `docs/VERIFICATION.md` and the relevant plan/export reference before changing behavior.

Current task boundary (user clarification, 2026-10-23): improve and validate reusable capabilities in this repository and Haoyong Video; Claude owns the later canvas-product integration. This research task must not edit or repair haoyongcanvas-v2, merge its prior PR, or deploy it. Provide explicit interface limits, standalone evidence and handoff notes. Keep this native bridge optional; ordinary independent rendering belongs in Haoyong Video and does not require the official app. Preserve known research without expanding native parity experiments unless they add concrete reusable value; conserve tokens and repeated test work.

- Inspect the current Git status and preserve unrelated changes. Work on a separate checkout when another task owns the same files.
- Preserve exact application, library and codec identity checks. A successful local experiment does not authorize weakening a version/profile/hash guard.
- Jianying 11.6 supports the validated build/edit/publish subset and normal official UI export. Native headless export is a separate unsupported ABI path. Do not claim UI export proves headless export.
- A publish action requires the application to be fully closed and uses the tool's independent audit directory. Keep the original draft, index backup, media and four-mirror checks. Never overwrite an unrelated user's draft to run a test.
- Maintain independent copies when editing existing projects. Preserve unknown native fields. Unsupported fields or shapes must produce explicit reports rather than being silently discarded.
- Register every discovered native feature and control, including unavailable, paid, cloud and resource-dependent functions. Implementation, access or licensing limits affect status and execution choices, not whether the feature is inventoried. Separate normal-UI measurements, UI-only observations, static findings and hypotheses; keep incomplete enumeration explicit.
- Tests belong in `tests/` or the existing engine test modules. Pure offline tests must not mutate the official application or the user's real project library. Native/UI experiments use clearly named synthetic projects and explicit evidence.
- Keep official binaries, libraries, weights, fonts, accounts, user media and local paths out of Git. Preserve required licenses/provenance. Remove obsolete promotions, contacts and commercial referral text from product-facing materials.
- Delete only proven disposable intermediates or byte-verified duplicates. Keep unique inputs, paid outputs and validation evidence; record material cleanup.
- Shared feature implementations live in Haoyong Video. This repository should document its tested handoff and avoid copying the independent renderer into the native bridge.

## Checks and handoff

Run `python3 -m unittest discover -s tests -v` for offline regression. Run relevant native checks only with the exact prepared environment and profile; list skips separately. A successful build or valid draft is not proof of opening, saving, reopening or exporting in the official application.

Read `CONTRIBUTING.md` for code entry points, supported handoff and next steps. Keep docs version-specific, retain negative evidence and report exact commands/results. Do not commit local evidence directories under `work/`.
