# scratch.tf-pr-based-flow

https://www.notion.so/sentry/TACOS-Sync-8d61ee6576a24d49acd43ad796760a11?pvs=4#a505c2afaf7a46118428bb0e32568ae4

## Developers

### How-To

```
make test
```

#### Run one test

```
./manual_tests/behaviors/lock_on_pr.py
```

It will also accept all the options pytest does.

#### View coverage for one test

```
coverage-enabled ./lib/json.py
make coverage-server
```
