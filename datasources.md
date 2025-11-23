## FLEMSIM DATA SOURCES
---
1. https://huggingface.co/datasets/danjacobellis/chexpert

### USAGE:
- datasets:
```python
from datasets import load_dataset
ds = load_dataset("danjacobellis/chexpert")

```
- dask:
```python
import dask.dataframe as dd

splits = {'train': 'data/train-*.parquet', 'validation': 'data/validation-00000-of-00001.parquet'}
df = dd.read_parquet("hf://datasets/danjacobellis/chexpert/" + splits["train"])
```

### Datase Files(23)

11.5 GB
data/
- train-00000-of-00023.parquet
- train-00001-of-00023.parquet
- train-00002-of-00023.parquet
- train-00003-of-00023.parquet
- train-00004-of-00023.parquet
- train-00005-of-00023.parquet
- train-00006-of-00023.parquet
- train-00007-of-00023.parquet
- train-00008-of-00023.parquet
- train-00009-of-00023.parquet
- train-00010-of-00023.parquet
- train-00011-of-00023.parquet
- train-00012-of-00023.parquet
- train-00013-of-00023.parquet
- train-00014-of-00023.parquet
- train-00015-of-00023.parquet
- train-00016-of-00023.parquet
- train-00017-of-00023.parquet
- train-00018-of-00023.parquet
- train-00019-of-00023.parquet
- train-00020-of-00023.parquet
- train-00021-of-00023.parquet
- train-00022-of-00023.parquet
- validation-00000-of-00001.parquet

---

2. https://huggingface.co/datasets/itsanmolgupta/mimic-cxr-dataset?library=datasets

### USAGE:
- datasets:
```python
from datasets import load_dataset
ds = load_dataset("itsanmolgupta/mimic-cxr-dataset")
````

- dask:
```python
import dask.dataframe as dd
df = dd.read_parquet("hf://datasets/itsanmolgupta/mimic-cxr-dataset/data/train-*.parquet")
```

### Datase Files(23)

793 MB
data/
- train-00000-of-00002.parquet - 396
- train-00001-of-00002.parquet - 397

