## 1. update/generate patch

In the root directory of the project, run with:

```bash
diff -urN /containernet/mininet/link.py ./containernet/mininet/link.py > patch/0001-updated-tc-strategy.patch
```

`/containernet/mininet/link.py` is the original file, `./containernet/mininet/link.py` is the updated file in oasis.

## 2. apply patch

```bash
cd /
patch -p0 < patch/0001-updated-tc-strategy.patch
```

## 3. link.py

Don't format the file `link.py` in your IDE, edit it in vim.
