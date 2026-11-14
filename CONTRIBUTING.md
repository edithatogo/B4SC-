# Contributing to B4SC-

This repository contains SAS preparation and R analysis scripts for B4SC data. The numbered SAS files describe denominator creation, B4SC dataset creation, year combination, and DataLab output preparation; the R scripts analyze and present the resulting counts.

## Before you start

Search existing issues and pull requests before starting, and discuss substantial changes or new dependencies in an issue. Use an issue template when one is offered. For a bug, include the affected commit or version, environment, a minimal reproduction, and expected versus observed behavior; remove sensitive information from logs and screenshots.

## Development and validation

Read the comments and input declarations in the relevant numbered SAS script before changing it. The extraction scripts depend on an authorized DataLab environment and configurable data refresh and fiscal-year settings. Keep that access requirement explicit; a public clone is not a complete execution environment.

For R changes, review [Data_and_Functions.R](Data_and_Functions.R), [Analysis_Predictor_Rank.R](Analysis_Predictor_Rank.R), and [Produce_Outputs.R](Produce_Outputs.R). Identify required packages and input CSV schemas from the scripts. There is no repository-wide test command documented here. Validate affected joins, denominators, year boundaries, rates, and plots with small synthetic examples and independently calculated expected values. Record SAS/R versions and any checks that require unavailable restricted inputs. Share only outputs permitted for release.

## Pull requests

Work on a focused branch from the current default branch. Open a pull request explaining the problem, the resulting behavior, and any compatibility or data-format changes. Link the relevant issue and complete any existing PR template.

Add focused regression coverage for changed behavior and update affected examples or documentation. Describe the checks actually run, their results, and any checks you could not run. For documentation-only changes, verify links, examples, and rendered formatting. Use the repository's existing checks and review/merge process; preserve required checks and resolve actionable feedback without weakening the checks.

## Security and sensitive information

Follow the [account security policy](https://github.com/edithatogo/.github/blob/main/SECURITY.md). Report vulnerabilities privately through the repository's **Report a vulnerability** option if available; otherwise request a private reporting contact without posting exploit details. Never include credentials, personal information, restricted datasets, or confidential records in issues, commits, fixtures, or diagnostic output.

## Licensing and conduct

Be respectful and constructive, and follow the [account code of conduct](https://github.com/edithatogo/.github/blob/main/CODE_OF_CONDUCT.md). Preserve attribution and third-party notices. Contribute only material you are entitled to share; resolve unclear permissions before adding third-party content. This guide does not change licensing terms or introduce a CLA or DCO requirement.

## References

- [GitHub contribution guideline conventions](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors)
- [OpenSSF contribution and quality criteria](https://www.bestpractices.dev/en/criteria)
