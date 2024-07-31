## HOWTO

```bash
sudo python3 src/start.py -n src/config/nested-containernet-config.yaml \
    --containernet=nuc_sz \
    -w {workspace} \
    -t src/config/one-concrete-top.yaml
```

This will run the `src/run_test.py` in a nested containernet environment. If you have installed the containernet, run the `src/run_test.py` directly:

```bash
python3 src/run_test.py {workspace} src/config/one-concrete-top.yaml
```

{workspace} is the path to the root directory of the project oasis.