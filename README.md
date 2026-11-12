# f3decomp coding-style map

An evidence-backed catalogue of C++ source patterns explored while contributing to [f3decomp](https://f3decomp.com/), the Fallout 3 matching-decompilation project.

**[Read the coding-style map](docs/coding-style-map.md)** · **[Browse evidence metadata](docs/evidence.md)** · **[Structured data](data/style-map.json)**

The public snapshot contains **276 locally exact examples**, supporting **222 observations** across six tentative style or library clusters. The observations cover gameplay code, ownership and initialization, containers, numeric code, scene updates, and infrastructure. Each records what helped, how to apply it, and what the evidence cannot establish.

## What it is useful for

- Choosing the next source-level experiment when the right behavior still produces different machine code.
- Recognizing effects of native constructors, inline helpers, typed return values, aliasing, and object lifetimes.
- Retaining unsuccessful comparisons and limits instead of treating every near match as a general rule.
- Distinguishing an exact local checker result from successful integration into the complete project.

For example, a float-backed scalar wrapper helped reproduce two collision functions of 802 and 513 bytes, both subsequently server-verified. The second function also needed a reference-based product for one component. Related callers still failed to match with the same pattern, so the observation records both the successes and the transfer limits. See D43 in the map.

A later audio-update function matched all 1,068 bytes after an active-state call was passed directly to a constructor instead of stored in a named boolean. That result also depended on faithful helper definitions and float-rounding boundaries; see B40 for the controls and limits.

A 1,908-byte matrix inversion matched after three explicit column-elimination steps reused one scalar factor. Separate factors and 24 loop-variable declaration orders did not match. The server verified the result under corrected compiler settings; see D46 for the comparison and its limits.

## What the evidence means

An exact local match supports a reconstructed source shape. It does **not** establish unique original source code, original names or formatting, or the identity of a developer. The clusters are hypotheses about related code or libraries, with low author-attribution confidence.

Server verdicts are snapshots. `verified` means a recorded server acceptance; `unfit` means integration was rejected despite a local match; `pending` means no verdict yet; `unknown` means no retained verdict was available to this exporter. Unknown entries must not be counted as verified.

This public repo contains analysis and metadata. It contains no game executable, executable extracts, disassembly, private context packs, candidate implementations, credentials, or private server diagnostics. The published hashes identify local candidate artifacts; their source is not included. Consequently, **this repo alone cannot independently reproduce the historical binary matches**. Its checks validate the catalogue and reproducible documentation, not the game build.

## Build and check

Python 3.10 or newer is sufficient; there are no third-party dependencies.

```sh
python tools/build_style_map.py
python tools/build_style_map.py --check
python -m unittest discover -s tests -v
```

The generator reads `data/style-map.json` and produces both documents in `docs/`. `--check` fails if the data is invalid or the committed documents are stale. GitHub Actions runs these checks on pushes and pull requests.

## Exporting an updated private workspace snapshot

The optional exporter accepts the existing workspace's generated map. It copies a fixed list of public fields and omits source paths, source text, receipt identifiers, staging-unit identifiers, and raw diagnostics. It can merge a submission ledger and a recent status snapshot to retain known server verdicts.

```sh
python tools/export_style_map.py /path/to/workspace/reference/coding-style-map.json --ledger /path/to/workspace/private/continuation-submissions.json --status /path/to/workspace/private/status-latest.json
python tools/build_style_map.py
python -m unittest discover -s tests -v
```

Review the exported diff before publishing. The exporter does not access the network, load credentials, compile candidates, or inspect the game executable. It preserves existing local-check metadata rather than creating a new binary-match attestation.

## Contributing

Edit the structured data, then regenerate the documentation. Every observation must cite existing evidence and distinguish source behavior, compiler/ABI effects, and tentative attribution. Keep failed integration results and uncertainty visible. Do not add private project material or infer author identities from compiler behavior alone.

This is an independent contributor's research catalogue, not an official f3decomp release.

## Licence

The tooling and authored catalogue are released under the [MIT License](LICENSE). This licence does not grant rights to Fallout 3 or other third-party materials.
