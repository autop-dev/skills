---
profile: 1
repository: acme/api
updated: 2026-10-10
branches:
  default: main
  release: main
  develop: main
  model: trunk
  tags: "v*"
ci:
  system: github-actions
  config:
    - .github/workflows/ci.yml
    - .github/workflows/deploy.yml
  gates:
    - lint
    - test
deploy:
  - name: api
    kind: cloud-run
    config:
      - Dockerfile
      - .github/workflows/deploy.yml
    trigger: push-to-release
environments:
  - name: production
    branch: main
    url: https://api.example.com
  - name: staging
    branch: main
    url: https://staging.api.example.com
services:
  - name: Stripe
    purpose: payments and subscription billing
    evidence:
      - stripe (package)
      - STRIPE_SECRET_KEY (environment key name)
  - name: Sentry
    purpose: error reporting
    evidence:
      - sentry-sdk (package)
      - SENTRY_DSN (environment key name)
data_stores:
  - name: PostgreSQL
    purpose: primary store
    managed_by: Cloud SQL
---

## Branches and delivery

Trunk-based: feature branches merge into `main` through a pull request, and
every merge to `main` is released. Releases are also tagged `v*`.

## CI/CD

GitHub Actions runs `lint` and `test` on every pull request
(`.github/workflows/ci.yml`); both must pass before a merge.
`.github/workflows/deploy.yml` builds and deploys on every push to `main`.

## Deploy and environments

The `Dockerfile` image runs on Cloud Run. A push to `main` deploys to
staging first, then to production after the staging smoke test passes.

## Third-party services

- Stripe: payments and subscription billing.
- Sentry: error reporting.

## Notes

Nothing recorded.
