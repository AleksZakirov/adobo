# adobo.
#
# Description: An analysis framework for scRNA-seq data.
#  How to use: https://github.com/oscar-franzen/adobo/
#     Contact: Oscar Franzén <p.oscar.franzen@gmail.com>
"""
Summary
-------
Functions for plotting scRNA-seq data.
"""
from collections import Counter
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns

from ._constants import CLUSTER_COLORS_DEFAULT, YLW_CURRY
from ._colors import unique_colors

def reads_per_cell(obj, barcolor='#E69F00', title='sequencing reads', filename=None):
    """Generates a bar plot of read counts per cell

    Parameters
    ----------
    obj : :class:`adobo.data.dataset`
        A data class object.
    barcolor : `str`
        Color of the bars. Default: "#E69F00"
    title : `str`
        Title of the plot. Default: "sequencing reads"
    filename : `str`, optional
        Write plot to file instead of showing it on the screen.

    Returns
    -------
    None
    """
    count_data = obj.count_data
    cell_counts = count_data.sum(axis=0)
    plt.clf()
    colors = [barcolor]*(len(cell_counts))
    plt.gca().get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    plt.bar(np.arange(len(cell_counts)), sorted(cell_counts, reverse=True),
            color=colors)
    plt.ylabel('raw read counts')
    plt.xlabel('cells (sorted on highest to lowest)')
    plt.title(title)
    plt.tight_layout()
    if filename:
        plt.savefig(filename, bbox_inches='tight')
    else:
        plt.show()
    plt.close()
    
def genes_per_cell(obj, barcolor='#E69F00', title='expressed genes', filename=None):
    """Generates a bar plot of number of expressed genes per cell

    Parameters
    ----------
    obj : :class:`adobo.data.dataset`
          A data class object
    barcolor : `str`
        Color of the bars. Default: "#E69F00"
    title : `str`
        Title of the plot. Default: "sequencing reads"
    filename : `str`, optional
        Write plot to file instead of showing it on the screen.

    Returns
    -------
    None
    """
    count_data = obj.count_data
    genes_expressed = [ np.sum(r[1]>0) for r in count_data.transpose().iterrows() ]
    plt.clf()
    plt.gca().get_yaxis().set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    plt.bar(np.arange(len(genes_expressed)), sorted(genes_expressed, reverse=True),
            color=[barcolor]*len(genes_expressed))
    plt.ylabel('number of genes')
    plt.xlabel('cells (sorted on highest to lowest)')
    plt.title(title)
    if filename:
        plt.savefig(filename, bbox_inches='tight')
    else:
        plt.show()
    plt.close()

def pca_contributors(obj, name=None, dim=[0, 1, 2], top=10, color='#fcc603',
                     fontsize=6, fig_size=(10, 5), filename=None, verbose=False,
                     **args):
    """Examine the top contributing genes to each PCA component
    
    Note
    ----
    Genes are ranked by their absolute value. Additional parameters are passed into
    :py:func:`matplotlib.pyplot.savefig`.
    
    Parameters
    ----------
    obj : :class:`adobo.data.dataset`
          A data class object
    name : `str`
        The name of the normalization to operate on. If this is empty or None then the
        function will be applied on all normalizations available.
    dim : `list`
        A list of indices specifying components to plot. First component has index zero.
    top : `int`
        Specifies the number of top scoring genes to include. Default: 10
    color : `str`
        Color of the bars. As a string or hex code. Default: "#fcc603"
    fontsize : `int`
        Specifies font size. Default: 8
    fig_size : `tuple`
        Figure size in inches. Default: (10, 10)
    filename : `str`, optional
        Write to a file instead of showing the plot on screen.
    verbose : `bool`
        Be verbose or not. Default: False
        
    Returns
    -------
    Nothing.
    """
    targets = {}
    if name is None or name == '':
        targets = obj.norm_data
    else:
        targets[name] = obj.norm_data[name]
    f, ax = plt.subplots(nrows=len(targets), ncols=len(dim), figsize=fig_size)
    if ax.ndim==1:
        ax = [ax]
    f.subplots_adjust(wspace=1)
    for row, k in enumerate(targets):
        item = targets[k]
        if verbose:
            print('Running clustering on the %s normalization' % k)
        contr = item['dr']['pca']['contr'][dim]
        idx = 0
        for i, d in contr.iteritems():
            d = d.sort_values(ascending=False)
            d = d.head(top)
            y_pos = np.arange(len(d))
            ax[row][idx].barh(y_pos, d.values, color=YLW_CURRY)
            ax[row][idx].set_yticks(y_pos)
            ax[row][idx].set_yticklabels(d.index.values, fontsize=fontsize)
            ax[row][idx].set_xlabel('abs(PCA score)', fontsize=fontsize)
            ax[row][idx].set_title('comp. %s' % (i+1), fontsize=fontsize)
            ax[row][idx].invert_yaxis() # labels read top-to-bottom
            
            if idx == 0:
                ax[row][idx].set_ylabel(k)
            idx += 1
    plt.tight_layout()
    if filename != None:
        plt.savefig(filename, **args)
    else:
        plt.show()

def cell_viz(obj, reduction='tsne', name=(), clustering=('leiden',), metadata=(),
             genes=(), filename=None, marker_size=0.8, font_size=8, colors='adobo',
             title=None, legend=True, min_cluster_size=10,
             fig_size=(10, 10), verbose=False):
    """Generates a 2d scatter plot from an embedding

    Parameters
    ----------
    obj : :class:`adobo.data.dataset`
          A data class object
    reduction : `{'tsne', 'umap', 'irlb', 'svd'}`
        The dimensional reduction to use. Default: tsne
    name : `tuple`
        A tuple of normalization to use. If it has the length zero, then all available
        normalizations will be used.
    clustering : `tuple`, optional
        Specifies the clustering outcomes to plot.
    metadata : `tuple`, optional
        Specifies the metadata variables to plot.
    genes : `tuple`, optional
        Specifies genes to plot.
    filename : `str`, optional
        Name of an output file instead of showing on screen.
    marker_size : `float`
        The size of the markers.
    font_size : `float`
        Font size. Default: 8
    colors : `{'default', 'random'}` or `list`
        Can be: (i) "adobo" or "random"; or (ii) a `list` of colors with the same
        length as the number of factors. If colors is set to "adobo", then colors are
        retrieved from :py:attr:`adobo._constants.CLUSTER_COLORS_DEFAULT` (but if the
        number of clusters exceed 50, then random colors will be used). Default: adobo
    title : `str`
        Title of the plot. By default the title is set to the reduction technique.
    legend : `bool`
        Add legend or not. Default: True
    min_cluster_size : `int`
        Can be used to prevent clusters below a certain number of cells to be plotted.
        Default: 10
    fig_size : `tuple`
        Figure size in inches. Default: (10, 10)
    verbose : `bool`
        Be verbose or not. Default: True

    Returns
    -------
    None
    """
    available_reductions = ('tsne', 'umap', 'pca')
    if not reduction in available_reductions:
        raise Exception('`reduction` must be one of %s.' % ', '.join(available_reductions))
    if marker_size<0:
        raise Exception('`marker_size` cannot be negative.')
    # cast to tuple if necessary
    if type(clustering) == str:
        clustering = (clustering,)
    if type(metadata) == str:
        metadata = (metadata,)
    if type(genes) == str:
        genes = (genes,)
    if type(name) == str:
        name = (name,)
    # setup colors
    if colors == 'adobo':
        colors = CLUSTER_COLORS_DEFAULT
    n_plots = len(clustering) + len(metadata) + len(genes) # per row
    if n_plots == 1:
        n_plots = 2
    plt.rc('xtick', labelsize=font_size)
    plt.rc('ytick', labelsize=font_size)
    targets = {}
    if len(name) == 0:
        targets = obj.norm_data
    else:
        targets[name] = obj.norm_data[name]
    # setup plotting grid
    fig, aa = plt.subplots(nrows=len(targets),
                           ncols=n_plots,
                           figsize=fig_size)
    if aa.ndim == 1:
        aa = [aa]
    for row, l in enumerate(targets):
        item = targets[l]
        # the embedding
        E = item['dr']['tsne']['embedding']
        pl_idx = 0 # plot index
        # plot clusterings
        for cl_algo in clustering:
            cl = item['clusters'][cl_algo]['membership']
            groups = np.unique(cl)
            if min_cluster_size > 0:
                z = pd.Series(dict(Counter(cl)))
                remove = z[z<min_cluster_size].index.values
                groups = groups[np.logical_not(pd.Series(groups).isin(remove))]
            for i, k in enumerate(groups):
                idx = np.array(cl) == k
                e = E[idx]
                col = colors[i]
                aa[row][pl_idx].scatter(e.iloc[:, 0], e.iloc[:, 1], s=marker_size,
                                        color=col)
            aa[row][pl_idx].set_title(cl_algo, size=font_size)
            if pl_idx == 0:
                aa[row][pl_idx].set_ylabel(l)
            if legend:
                aa[row][pl_idx].legend(list(groups), loc='upper left', markerscale=5,
                                       bbox_to_anchor=(1, 1), prop={'size': 5})
            pl_idx += 1
        # plot meta data variables
        for meta_var in metadata:
            m_d = obj.meta_cells.loc[obj.meta_cells.status=='OK', meta_var]
            if m_d.dtype.name == 'category':
                groups = np.unique(m_d)
                for i, k in enumerate(groups):
                    idx = np.array(m_d) == k
                    e = E[idx]
                    col = colors[i]
                    aa[row][pl_idx].scatter(e.iloc[:, 0], e.iloc[:, 1], s=marker_size,
                                            color=col)
                if legend:
                    aa[row][pl_idx].legend(list(groups), loc='upper left', markerscale=5,
                                           bbox_to_anchor=(1, 1), prop={'size': 7})
            else:
                # If data are continuous
                cmap = sns.cubehelix_palette(as_cmap=True)
                po = aa[row][pl_idx].scatter(E.iloc[:, 0], E.iloc[:, 1], s=marker_size,
                                        c=m_d.values, cmap=cmap)
                cbar = fig.colorbar(po, ax=aa[row][pl_idx])
                #cbar.set_label('foobar')
            aa[row][pl_idx].set_title(meta_var, size=font_size)
            pl_idx += 1
        # plot genes
        for gene in genes:
            ge = item['data'].loc[gene, :]
            cmap = sns.cubehelix_palette(as_cmap=True)
            po = aa[row][pl_idx].scatter(E.iloc[:, 0], E.iloc[:, 1], s=marker_size,
                                         c=ge.values, cmap=cmap)
            cbar = fig.colorbar(po, ax=aa[row][pl_idx])
            aa[row][pl_idx].set_title(gene, size=font_size)
            pl_idx += 1
    plt.subplots_adjust(wspace=0.4, hspace=0.3)
    if filename != None:
        plt.savefig(filename, **args)
    else:
        plt.show()
