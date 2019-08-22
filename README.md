# Description
adobo for scRNA-seq

# Tutorials API-level Documentation
Classes, functions and arguments are documented here:
* https://oscar-franzen.github.io/adobo/

# Install
```bash
# pip3
```

# Quick guide to get started
### Launch Python
```bash
python3
```

### Load the adobo package
```python
import adobo as ad
```

### Basic usage - loading a dataset of raw read counts
```python
# create a new data object
data = ad.IO.load_from_file('input_single_cell_rnaseq_read_counts.mat',
                             verbose=True,
                             column_id=False)

# remove empty cells and genes
data = ad.preproc.remove_empty(data, verbose=True)

# detect and remove mitochondrial genes
data = ad.preproc.detect_mito(data, verbose=True)

# detect ERCC spikes
data = ad.preproc.detect_ERCC_spikes(data, verbose=True)
```

### Quality control and filtering
```python
# barplot of number of reads per cell
ad.plotting.barplot_reads_per_cell(data)

# barplot of number of expressed genes per cell
ad.plotting.barplot_genes_per_cell(data)

# apply a simple filter, requiring a minimum number of reads per cell and a minimum number
# of cells expressing a gene. For SMART-seq2 data, bump up the minreads option.
data = ad.preproc.simple_filter(data, minreads=1000, minexpgenes=0.001, verbose=True)
```

### Automatic detection of low quality cells
```python
# Load list of rRNA genes
import pandas as pd
rRNA = pd.read_csv('examples/rRNA_genes.txt', header=None)
rRNA = rRNA.iloc[:,0].values

d.auto_clean(rRNA_genes=rRNA, verbose=True)
```

### Normalize
```python
```

# Contact, bugs, etc
* Oscar Franzén, <p.oscar.franzen@gmail.com>
