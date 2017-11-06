# -*- coding: utf-8 -*-
"""
Copyright 2014-2016 Jean-Sebastien Gosselin
email: jean-sebastien.gosselin@ete.inrs.ca

last modification: 27/09/2016

"""
import matplotlib as mpl
import matplotlib.pyplot as plt

# bbox are structured in the the following way:   [[ Left , Bottom ],
#                                                  [ Right, Top    ]]


###############################################################################


class FigureMod(mpl.figure.Figure):

    def __init__(self, *args, **kargs):
        super(FigureMod, self).__init__(*args, **kargs)
        self.set_facecolor('white')

    def set_ylabel(ax, text, fontsize=12, labelpad=5):

        fig = ax.get_figure()
        renderer = fig.canvas.get_renderer()
        fig.canvas.draw()

        if ax.yaxis.get_label_position() == 'left':
            bbox, _ = ax.yaxis.get_ticklabel_extents(renderer)
            bbox = ax.transAxes.inverted().transform(bbox)

            padding = mpl.transforms.ScaledTranslation(-labelpad/72., 0,
                                                       fig.dpi_scale_trans)
            transform = ax.transAxes + padding

            x = bbox[0, 0]
            y = (bbox[0, 1] + bbox[1, 1]) / 2.

            ax.ylabel = ax.text(x, y, text, fontsize=fontsize, va='center',
                                ha='right', rotation=90, transform=transform)

        elif ax.yaxis.get_label_position() == 'right':
            _, bbox = ax.yaxis.get_ticklabel_extents(renderer)
            bbox = ax.transAxes.inverted().transform(bbox)

            padding = mpl.transforms.ScaledTranslation(labelpad/72., 0,
                                                       fig.dpi_scale_trans)
            transform = ax.transAxes + padding

            x = bbox[1, 0]
            y = (bbox[0, 1] + bbox[1, 1]) / 2.

            ax.ylabel = ax.text(x, y, text, fontsize=fontsize, va='center',
                                ha='left', rotation=90, transform=transform)


###############################################################################


def set_ylabel(ax, text, fontsize=12, labelpad=5, position='left'):

    ax.yaxis.set_label_position(position)

    fig = ax.get_figure()
    renderer = fig.canvas.get_renderer()
    fig.canvas.draw()

    if ax.yaxis.get_label_position() == 'left':
        bbox, _ = ax.yaxis.get_ticklabel_extents(renderer)
        bbox = ax.transAxes.inverted().transform(bbox)

        padding = mpl.transforms.ScaledTranslation(-labelpad/72., 0,
                                                   fig.dpi_scale_trans)
        transform = ax.transAxes + padding

        x = bbox[0, 0]
        y = (bbox[0, 1] + bbox[1, 1]) / 2.

        ax.ylabel = ax.text(x, y, text, fontsize=fontsize, va='center',
                            ha='right', rotation=90, transform=transform)

    elif ax.yaxis.get_label_position() == 'right':
        _, bbox = ax.yaxis.get_ticklabel_extents(renderer)
        bbox = ax.transAxes.inverted().transform(bbox)

        padding = mpl.transforms.ScaledTranslation(labelpad/72., 0,
                                                   fig.dpi_scale_trans)
        transform = ax.transAxes + padding

        x = bbox[1, 0]
        y = (bbox[0, 1] + bbox[1, 1]) / 2.

        ax.ylabel = ax.text(x, y, text, fontsize=fontsize, va='center',
                            ha='left', rotation=90, transform=transform)


def set_xlabel(ax, text, fontsize=12, labelpad=5):

    fig = ax.get_figure()
    renderer = fig.canvas.get_renderer()
    fig.canvas.draw()

    bbox, _ = ax.xaxis.get_ticklabel_extents(renderer)
    bbox = ax.transAxes.inverted().transform(bbox)

    padding = mpl.transforms.ScaledTranslation(0, -labelpad/72,
                                               fig.dpi_scale_trans)
    transform = ax.transAxes + padding

    x = (bbox[0, 0] + bbox[1, 0]) / 2.
    y = bbox[0, 1]

    ax.xlabel = ax.text(x, y, text, fontsize=fontsize, va='top',
                        ha='center', transform=transform, clip_on=False)


def set_yunit(ax, unit, ypad=5, fs=14):  # ====================================
    fig = ax.get_figure()
    renderer = fig.canvas.get_renderer()
#    ax_bbox = ax.get_window_extent(renderer)

    if ax.yaxis.get_label_position() == 'left':
        bbox, _ = ax.yaxis.get_ticklabel_extents(renderer)
    elif ax.yaxis.get_label_position() == 'right':
        _, bbox = ax.yaxis.get_ticklabel_extents(renderer)

    bbox = ax.transAxes.inverted().transform(bbox)
    x = (bbox[1, 0] + bbox[0, 0])/2
    y = 1

    padding = mpl.transforms.ScaledTranslation(0, ypad/72, fig.dpi_scale_trans)
    transform = ax.transAxes + padding

    ax.text(x, y, unit, fontsize=fs, va='bottom',
            ha='center', transform=transform, clip_on=False)


def set_xunit(ax, unit, xpad=3, fs=14):  # ====================================

    fig = ax.get_figure()
    renderer = fig.canvas.get_renderer()

    bbox, _ = ax.xaxis.get_ticklabel_extents(renderer)
    bbox = ax.transAxes.inverted().transform(bbox)
    x = bbox[1, 0]
    y = bbox[0, 1]

    padding = mpl.transforms.ScaledTranslation(xpad/72, 0, fig.dpi_scale_trans)
    transform = ax.transAxes + padding

    ax.text(x, y, unit, fontsize=fs, va='bottom',
            ha='left', transform=transform, clip_on=False)


def align_ylabels(fig):  # ====================================================

    Ext = []

    for ax in fig.axes:
        try:
            Ext.append(ax.ylabel.get_position()[0])
        except:
            pass

    for ax in fig.axes:
        try:
            if ax.yaxis.get_label_position() == 'left':
                ax.ylabel.set_x(min(Ext))
            elif ax.yaxis.get_label_position() == 'right':
                ax.ylabel.set_x(max(Ext))
        except:
            pass

    fig.canvas.draw()


def set_margins(fig, borderpad=3):  # =========================================

    renderer = fig.canvas.get_renderer()
    fig.canvas.draw()
    plt.show()

    fig_bbox = fig.get_window_extent(renderer)

    MargLeft = []
    MargRight = []
    MargBottom = []
    MargTop = []
    for ax in fig.axes:
        ax_bbox = ax.get_window_extent(renderer)

        # Taking into account any other text in the figure --------------------

        for text in ax.texts:
            text_bbox = text.get_window_extent(renderer)

            MargBottom.append((ax_bbox.y0-text_bbox.y0)/fig_bbox.height)
            MargTop.append((text_bbox.y1 - ax_bbox.y1)/fig_bbox.height)

            MargLeft.append((ax_bbox.x0 - text_bbox.x0)/fig_bbox.width)
            MargRight.append((text_bbox.x1 - ax_bbox.x1)/fig_bbox.width)

        # xlabel vertical extent ----------------------------------------------

        try:
            xlabel_bbox = ax.xlabel.get_window_extent(renderer)
            xaxis_bbox, _ = ax.xaxis.get_ticklabel_extents(renderer)
            MargBottom.append((ax_bbox.y0-xlabel_bbox.y0)/fig_bbox.height)
        except:
            pass

        # ylabel horizontal extent --------------------------------------------

        try:
            ylabel_bbox = ax.ylabel.get_window_extent(renderer)
            MargLeft.append((ax_bbox.x0 - ylabel_bbox.x0)/fig_bbox.width)
            MargRight.append((ylabel_bbox.x1 - ax_bbox.x1)/fig_bbox.width)
        except:
            pass

        # yaxis vertical and horizontal extent --------------------------------

        try:
            yleft_bbox, yright_bbox = ax.yaxis.get_ticklabel_extents(renderer)

            if ax.yaxis.get_label_position() == 'left':
                MargBottom.append(
                    (ax_bbox.y0 - yleft_bbox.y0)/fig_bbox.height)
            elif ax.yaxis.get_label_position() == 'right':
                MargBottom.append(
                    (ax_bbox.y0 - yright_bbox.y0)/fig_bbox.height)

            MargTop.append((yleft_bbox.y1 - ax_bbox.y1)/fig_bbox.height)
            MargTop.append((yright_bbox.y1 - ax_bbox.y1)/fig_bbox.height)

            MargLeft.append((ax_bbox.x0 - yleft_bbox.x0)/fig_bbox.width)
            MargRight.append((yright_bbox.x1 - ax_bbox.x1)/fig_bbox.width)
        except:
            pass

        # xaxis vertical and horizontal extent --------------------------------

        try:
            xlow_bbox, xtop_bbox = ax.xaxis.get_ticklabel_extents(renderer)

            if ax.xaxis.get_label_position() == 'bottom':
                MargBottom.append((ax_bbox.y0 - xlow_bbox.y0)/fig_bbox.height)
                MargLeft.append((ax_bbox.x0 - xlow_bbox.x0)/fig_bbox.width)
                MargRight.append((xlow_bbox.x1 - ax_bbox.x1)/fig_bbox.width)
            elif ax.xaxis.get_label_position() == 'top':
                MargTop.append((xtop_bbox.y1 - ax_bbox.y1)/fig_bbox.height)
                MargLeft.append((ax_bbox.x0 - xtop_bbox.x0)/fig_bbox.width)
                MargRight.append((xtop_bbox.x1 - ax_bbox.x1)/fig_bbox.width)
        except:
            pass

        # Legend vertical extent ----------------------------------------------

        try:
            lg_bbox = ax.get_legend().get_window_extent(renderer)

            MargBottom.append((ax_bbox.y0 - lg_bbox.y0) / fig_bbox.height)
            MargTop.append((lg_bbox.y1 - ax_bbox.y1) / fig_bbox.height)
        except:
            pass

        # Legend horizontal extent --------------------------------------------

        try:
            lg_bbox = ax.get_legend().get_window_extent(renderer)

            MargLeft.append((ax_bbox.x0 - lg_bbox.x0)/fig_bbox.width)
            MargRight.append((lg_bbox.x1 - ax_bbox.x1)/fig_bbox.width)
        except:
            pass

    MargBottom = max(max(MargBottom), 0)
    MargBottom = MargBottom + borderpad/72/fig.get_figheight()

    MargTop = max(max(MargTop), 0)
    MargTop = MargTop + borderpad/72/fig.get_figheight()

    MargLeft = max(max(MargLeft), 0)
    MargLeft = MargLeft + borderpad/72/fig.get_figwidth()

    MargRight = max(max(MargRight), 0)
    MargRight = MargRight + borderpad/72/fig.get_figwidth()

    for ax in fig.axes:
        ax.set_position([MargLeft, MargBottom,
                         1 - MargLeft - MargRight,
                         1 - MargBottom - MargTop])

    # --------------------------------------------- Update labels position ----

    fig.canvas.draw()

    for ax in fig.axes:
        try:
            bbox, _ = ax.xaxis.get_ticklabel_extents(renderer)
            bbox = ax.transAxes.inverted().transform(bbox)

            x = (bbox[0, 0] + bbox[1, 0]) / 2.
            y = bbox[0, 1]

            ax.xlabel.set_position((x, y))
        except:
            pass

        try:
            if ax.yaxis.get_label_position() == 'left':
                bbox, _ = ax.yaxis.get_ticklabel_extents(renderer)
                bbox = ax.transAxes.inverted().transform(bbox)

                x = bbox[0, 0]
                y = (bbox[0, 1] + bbox[1, 1]) / 2.

                ax.ylabel.set_position((x, y))

            elif ax.yaxis.get_label_position() == 'right':
                _, bbox = ax.yaxis.get_ticklabel_extents(renderer)
                bbox = ax.transAxes.inverted().transform(bbox)

                x = bbox[1, 0]
                y = (bbox[0, 1] + bbox[1, 1]) / 2.

                ax.ylabel.set_position((x, y))
        except:
            pass


###############################################################################


if __name__ == '__main__':

    plt.close('all')

    fig = plt.figure(figsize=(8.5, 6.5), FigureClass=FigureMod)

    # ------------------------------------------------------ AXES CREATION ----

    ax = fig.add_axes([0, 0, 1, 1], frameon=True)
    ax2 = ax.twinx()

    for loc in ['top', 'bottom', 'right', 'left']:
        ax.spines[loc].set_linewidth(0.5)

    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')
    ax2.yaxis.set_ticks_position('right')

    ax.tick_params(axis='x', direction='out', labelsize=16)
    ax.tick_params(axis='y', direction='out', labelsize=16)
    ax2.tick_params(axis='y', direction='out', labelsize=16)

    set_xlabel(ax, 'Exemple de xLabel', fontsize=24, labelpad=25)
    set_ylabel(ax, 'Exemple de yLabel on left axis', fontsize=24,
               labelpad=25, position='left')
    set_ylabel(ax2, 'Exemple de yLabel on right axis', fontsize=24,
               labelpad=25, position='right')

    set_margins(fig, borderpad=5)

    fig.savefig('mplJS.pdf')
    plt.show()
