# Matrix-Fan

Core behavior:

- [ ] in a matrix job, save some data for use in a "fan-in", summarizing job
  - implemented in the `matrix-fan-out` action
- [ ] ensure some singular job after the matrix job receives all the sent data
  - implemented in the `matrix-fan-in` action

Design goals:

- [ ] data passing

  - [ ] collect outputs -- for small data
  - [ ] collect artifacts -- for large data

- [ ] pass no parameters in most cases

  - [ ] configuration by convention: avoid separate configuration where we can
  - [ ] provide a parameter where otherwise we'd necessarily use a constant

- [ ] simplify user interface

  - fan-out: `matrix*.json` anywhere under the given `path`
  - fan-in: `matrix.json` directly under the given `path`

- [ ] provide exact matrix context data at fan-in

  - made available at `$path/$shard/gha-matrix-context.json`

- [ ] output zero-to-many json files per matrix job

- [ ] upload other data to the fan-out as well, to be archived but ignored by
      matrix-fan-in

  - e.g. upload all of `tfplan`, `tfplan.json`, and `fan-in.json`
  - only 'fan-in.json' is read by matrix-fan-in (by default)

- [ ] artifact naming both readably represents their source/destination path and
      clearly denotes which matrix-shard generated the artifact

- [x] automatically self-test these features, in GHA CI
- [x] no dependencies on parent repo -- this can (should?) be moved to its own
      actions repo
