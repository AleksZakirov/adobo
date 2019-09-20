# adobo.
#
# Description: An analysis framework for scRNA-seq data.
#  How to use: https://github.com/oscar-franzen/adobo/
#     Contact: Oscar Franzén <p.oscar.franzen@gmail.com>
"""
Summary
-------
Functions for dimensional reduction.
"""
import sys
import pandas as pd
import numpy as np
import scipy.linalg
from sklearn.preprocessing import scale as sklearn_scale
import sklearn.manifold
import umap as um

from . import irlbpy
from ._log import warning

def irlb(data_norm, ncomp=75, seed=None):
    """Truncated SVD by implicitly restarted Lanczos bidiagonalization
    
    Notes
    -----
    The augmented implicitly restarted Lanczos bidiagonalization algorithm (IRLBA) finds
    a few approximate largest singular values and corresponding singular vectors using a
    method of Baglama and Reichel.
    
    Parameters
    ----------
    data_norm : :py:class:`pandas.DataFrame`
        A pandas data frame containing normalized gene expression data.
    ncomp : `int`
        Number of components to return. Default: 75
    seed : `int`
        For reproducibility. Default: None
    
    References
    ----------
    Baglama et al (2005) Augmented Implicitly Restarted Lanczos Bidiagonalization Methods
        SIAM Journal on Scientific Computing
    https://github.com/bwlewis/irlbpy
    
    Returns
    -------
    `pd.DataFrame`
        A py:class:`pandas.DataFrame` containing the components (columns).
    `pd.DataFrame`
        A py:class:`pandas.DataFrame` containing the contributions of every gene (rows).
    """
    inp = data_norm
    lanc = irlbpy.lanczos(inp, nval=ncomp, maxit=1000, seed=seed)
    # weighing by var
    comp = np.dot(lanc.V, np.diag(lanc.s))
    comp = pd.DataFrame(comp)
    # gene contributions
    contr = pd.DataFrame(np.abs(lanc.U), index=inp.index)
    return comp, contr

def svd(data_norm, ncomp=75):
    """Principal component analysis via singular value decomposition
    
    Parameters
    ----------
    data_norm : :class:`pandas.DataFrame`
        A pandas data frame containing normalized gene expression data. Preferrably this
        should be a subset of the normalized gene expression matrix containing highly
        variable genes.
    ncomp : `int`
        Number of components to return. Default: 75
    
    References
    ----------
    (SE) https://tinyurl.com/yyt6df5x
    
    Returns
    -------
    `pd.DataFrame`
        A py:class:`pandas.DataFrame` containing the components (columns).
    `pd.DataFrame`
        A py:class:`pandas.DataFrame` containing the contributions of every gene (rows).
    """
    inp = data_norm
    inp = inp.transpose()
    s = scipy.linalg.svd(inp)
    v = s[2].transpose()
    d = s[1]
    s_d = d/np.sqrt(inp.shape[0]-1)
    retx = inp.dot(v)
    retx = retx.iloc[:, 0:ncomp]
    comp = retx
    contr = pd.DataFrame(np.abs(v[:, 0:ncomp]), index=inp.columns)
    return comp, contr

def pca(obj, method='irlb', name=None, ncomp=75, allgenes=False, scale=True,
        verbose=False, seed=None):
    """Principal Component Analysis
    
    Notes
    -----
    A wrapper function around the individual normalization functions, which can also be
    called directly. Scaling of the data is achieved by setting scale=True (default),
    which will center (subtract the column mean) and scale columns (divide by their
    standard deviation).

    Parameters
    ----------
    obj : :class:`adobo.data.dataset`
          A dataset class object.
    method : `{'irlb', 'svd'}`
        Method to use for PCA. This does not matter much. Default: irlb
    name : `str`
        The name of the normalization to operate on. If this is empty or None then the
        function will be applied on all normalizations available.
    ncomp : `int`
        Number of components to return. Default: 75
    allgenes : `bool`
        Use all genes instead of only HVG. Default: False
    scale : `bool`
        Scales input data prior to PCA. Default: True
    verbose : `bool`
        Be noisy or not. Default: False
    seed : `int`
        For reproducibility (only irlb). Default: None

    References
    ----------
    https://en.wikipedia.org/wiki/Principal_component_analysis

    Returns
    -------
    Nothing. Modifies the passed object. Results are stored in two dictonaries in the
    passed object: `dr` (containing the components) and `dr_gene_contr` (containing
    gene contributions to each component)
    """
    if not obj.norm_data:
        raise Exception('Run normalization first before running pca. See here: \
https://oscar-franzen.github.io/adobo/adobo.html#adobo.normalize.norm')
    targets = {}
    if name is None or name == '':
        targets = obj.norm_data
    else:
        targets[name] = obj.norm_data[name]
    
    for k in targets:
        item = targets[k]
        data = item['data']
        if not allgenes:
            hvg = item['hvg']['genes']
            data = data[data.index.isin(hvg)]
        elif verbose:
            print('Using all genes')
        if scale:
            d_scaled = sklearn_scale(
                            data.transpose(),  # cells as rows and genes as columns
                            axis=0,            # over genes, i.e. features (columns)
                            with_mean=True,    # subtracting the column means
                            with_std=True)     # scale the data to unit variance
            d_scaled = pd.DataFrame(d_scaled.transpose(), index=data.index)
        if verbose:
            print('Running PCA on the %s normalization (dimensions %s)' % (k, data.shape))
        if method == 'irlb':
            comp, contr = irlb(data, ncomp, seed)
        elif method == 'svd':
            comp, contr = svd(data, ncomp)
        else:
            raise Exception('Unkown PCA method spefified. Valid choices are: irlb and svd')
        obj.norm_data[k]['dr']['pca'] = {'comp' : comp,
                                         'contr' : contr,
                                         'method' : method}
        obj.set_assay(sys._getframe().f_code.co_name, method)

def tsne(obj, run_on_PCA=True, name=None, perplexity=30, n_iter=2000, seed=None,
         verbose=False, **args):
    """
    Projects data to a two dimensional space using the tSNE algorithm.
    
    Notes
    -----
    It is recommended to perform this function on data in PCA space. This function calls
    :py:func:`sklearn.manifold.TSNE`, and any additional parameters will be passed to it.

    Parameters
    ----------
    obj : :class:`adobo.data.dataset`
          A dataset class object.
    run_on_PCA : `bool`
        To run tSNE on PCA components or not. If False then runs on the entire normalized
        gene expression matrix. Default: True
    name : `str`
        The name of the normalization to operate on. If this is empty or None then the
        function will be applied on all normalizations available.
    perplexity : `float`
        From [1]: The perplexity is related to the number of nearest neighbors that
        is used in other manifold learning algorithms. Larger datasets usually require
        a larger perplexity. Consider selecting a value between 5 and 50. Different
        values can result in significanlty different results. Default: 30
    n_iter : `int`
        Number of iterations. Default: 2000
    seed : `int`
        For reproducibility. Default: None
    verbose : `bool`
        Be verbose. Default: False

    References
    ----------
    van der Maaten, L.J.P.; Hinton, G.E. Visualizing High-Dimensional Data
        Using t-SNE. Journal of Machine Learning Research 9:2579-2605, 2008.
    https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html

    Returns
    -------
    Nothing. Modifies the passed object.
    """
    if not obj.norm_data:
        raise Exception('Run normalization first before running tsne. See here: \
https://oscar-franzen.github.io/adobo/adobo.html#adobo.normalize.norm')
    targets = {}
    if name is None or name == '':
        targets = obj.norm_data
    else:
        targets[name] = obj.norm_data[name]
    if verbose and not run_on_PCA:
        warning('Running tSNE on the entire gene expression matrix is not recommended.')
    for k in targets:
        item = targets[k]
        if not run_on_PCA:
            X = item['data']
        else:
            X = item['dr']['pca']['comp']
        if verbose:
            print('Running tSNE (perplexity %s) on the %s normalization' % (perplexity, k))
        tsne = sklearn.manifold.TSNE(n_components=2,
                                     n_iter=n_iter,
                                     perplexity=perplexity,
                                     random_state=seed,
                                     verbose=verbose,
                                     **args)
        emb = tsne.fit_transform(X)
        emb = pd.DataFrame(emb)
        obj.norm_data[k]['dr']['tsne'] = {'embedding' : emb,
                                          'perplexity' : perplexity,
                                          'n_iter' : n_iter}
    obj.set_assay(sys._getframe().f_code.co_name)

def umap(obj, run_on_PCA=True, name=None, seed=None, verbose=False, **args):
    """
    Projects data to a two dimensional space using the UMAP algorithm, a non-linear
    data reduction algorithm.
    
    Notes
    -----
    The UMAP output can be tweaked using these parameters (but there are also several
    other parameters that can influence the outcome, see `help(umap.UMAP)`:
    `n_neighbors`, Default: 15
        This parameter controls the balances between local versus global structure.
    `min_dist`, Default: 0.1
        Controls how tightly points are packed together.
    `metric`, Default: 'euclidean'
        The metric to use to compute distances in high dimensional space.

    Parameters
    ----------
    obj : :class:`adobo.data.dataset`
          A dataset class object.
    run_on_PCA : `bool`
        To run tSNE on PCA components or not. If False then runs on the entire normalized
        gene expression matrix. Default: True
    name : `str`
        The name of the normalization to operate on. If this is empty or None then the
        function will be applied on all normalizations available.
    seed : `int`
        For reproducibility. Default: None
    verbose : `bool`
        Be verbose. Default: False

    References
    ----------
    McInnes L, Healy J, Melville J (2018) UMAP: Uniform Manifold Approximation and
        Projection for Dimension Reduction, https://arxiv.org/abs/1802.03426
    https://github.com/lmcinnes/umap
    https://umap-learn.readthedocs.io/en/latest/

    Returns
    -------
    Nothing. Modifies the passed object.
    """
    if not obj.norm_data:
        raise Exception('Run normalization first before running umap. See here: \
https://oscar-franzen.github.io/adobo/adobo.html#adobo.normalize.norm')
    targets = {}
    if name is None or name == '':
        targets = obj.norm_data
    else:
        targets[name] = obj.norm_data[name]
    if verbose and not run_on_PCA:
        warning('Running UMAP on the entire gene expression matrix is not recommended.')
    for k in targets:
        item = targets[k]
        if not run_on_PCA:
            X = item['data']
        else:
            X = item['dr']['pca']['comp']
        if verbose:
            print('Running UMAP on the %s normalization' % k)
        reducer = um.UMAP(random_state=seed, verbose=verbose, **args)
        emb = reducer.fit_transform(X)
        emb = pd.DataFrame(emb)
        obj.norm_data[k]['dr']['umap'] = {'embedding' : emb }
    obj.set_assay(sys._getframe().f_code.co_name)
