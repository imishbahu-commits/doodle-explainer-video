# HyperFrames skill subset — upstream provenance

Vendored from [`heygen-com/hyperframes`](https://github.com/heygen-com/hyperframes)
at commit `1b86b561273e85e09e4f1a2cc57233ceac1a2945` (2026-08-21).

Included skill directories:

- `hyperframes-core`
- `hyperframes-keyframes`
- `hyperframes-animation`
- `hyperframes-cli`

License: Apache-2.0; see `LICENSE` in this directory.

This is a deliberately narrow subset. Generic HyperFrames creative/faceless
skills are not vendored because this repository's measured
`paint-explainer-analysis-4v/style_rules.json` must override generic motion,
transition, caption, and camera defaults.

Validation note: the vendored `hyperframes-animation` directory retains its
upstream tests unchanged. `animation-map-sampling.test.mjs` is standalone. Some
cases in `animation-map.test.mjs` and `package-loader.test.mjs` intentionally
reach the excluded `hyperframes-creative` sibling or full upstream monorepo
packages, so those cases are not standalone subset tests and are not satisfied
by adding the prohibited creative skill.
