# axis3d.py, original mplot3d version by John Porter
# Created: 23 Sep 2005
# Parts rewritten by Reinier Heeres <reinier@heeres.eu>

import copy

import numpy as np

from matplotlib import (
    artist, cbook, lines as mlines, axis as maxis, patches as mpatches,
    rcParams)
from . import art3d, proj3d


def get_flip_min_max(coord, index, mins, maxs):
    if coord[index] == mins[index]:
        return maxs[index]
    else:
        return mins[index]


def move_from_center(coord, centers, deltas, axmask=(True, True, True)):
    '''Return a coordinate that is moved by "deltas" away from the center.'''
    coord = copy.copy(coord)
    for i in range(3):
        if not axmask[i]:
            continue
        if coord[i] < centers[i]:
            coord[i] -= deltas[i]
        else:
            coord[i] += deltas[i]
    return coord


def tick_update_position(tick, tickxs, tickys, labelpos):
    '''Update tick line and label position and style.'''

    tick.label1.set_position(labelpos)
    tick.label2.set_position(labelpos)
    tick.tick1line.set_visible(True)
    tick.tick2line.set_visible(False)
    tick.tick1line.set_linestyle('-')
    tick.tick1line.set_marker('')
    tick.tick1line.set_data(tickxs, tickys)
    tick.gridline.set_data(0, 0)


class Axis(maxis.XAxis):
    """An Axis class for the 3D plots. """
    # These points from the unit cube make up the x, y and z-planes
    _PLANES = (
        (0, 3, 7, 4), (1, 2, 6, 5),     # yz planes
        (0, 1, 5, 4), (3, 2, 6, 7),     # xz planes
        (0, 1, 2, 3), (4, 5, 6, 7),     # xy planes
    )

    # Some properties for the axes
    _AXINFO = {
        'x': {'i': 0, 'tickdir': 1, 'juggled': (1, 0, 2),
            'color': (0.95, 0.95, 0.95, 0.5)},
        'y': {'i': 1, 'tickdir': 0, 'juggled': (0, 1, 2),
            'color': (0.90, 0.90, 0.90, 0.5)},
        'z': {'i': 2, 'tickdir': 0, 'juggled': (0, 2, 1),
            'color': (0.925, 0.925, 0.925, 0.5)},
    }

    def __init__(self, adir, v_intervalx, d_intervalx, axes, *args,
                 rotate_label=None, **kwargs):
        # adir identifies which axes this is
        self.adir = adir
        # data and viewing intervals for this direction
        self.d_interval = d_intervalx
        self.v_interval = v_intervalx

        # This is a temporary member variable.
        # Do not depend on this existing in future releases!
        self._axinfo = self._AXINFO[adir].copy()
        if rcParams['_internal.classic_mode']:
            self._axinfo.update(
                {'label': {'va': 'center',
                           'ha': 'center'},
                 'tick': {'inward_factor': 0.2,
                          'outward_factor': 0.1,
                          'linewidth': rcParams['lines.linewidth'],
                          'color': 'k'},
                 'axisline': {'linewidth': 0.75,
                              'color': (0, 0, 0, 1)},
                 'grid': {'color': (0.9, 0.9, 0.9, 1),
                          'linewidth': 1.0,
                          'linestyle': '-'},
                 })
        else:
            self._axinfo.update(
                {'label': {'va': 'center',
                           'ha': 'center'},
                 'tick': {'inward_factor': 0.2,
                          'outward_factor': 0.1,
                          'linewidth': rcParams.get(
                              adir + 'tick.major.width',
                              rcParams['xtick.major.width']),
                          'color': rcParams.get(
                              adir + 'tick.color',
                              rcParams['xtick.color'])},
                 'axisline': {'linewidth': rcParams['axes.linewidth'],
                              'color': rcParams['axes.edgecolor']},
                 'grid': {'color': rcParams['grid.color'],
                          'linewidth': rcParams['grid.linewidth'],
                          'linestyle': rcParams['grid.linestyle']},
                 })

        maxis.XAxis.__init__(self, axes, *args, **kwargs)
        self.set_rotate_label(rotate_label)

    def init3d(self):
        self.line = mlines.Line2D(
            xdata=(0, 0), ydata=(0, 0),
            linewidth=self._axinfo['axisline']['linewidth'],
            color=self._axinfo['axisline']['color'],
            antialiased=True)

        # Store dummy data in Polygon object
        self.pane = mpatches.Polygon(
            np.array([[0, 0], [0, 1], [1, 0], [0, 0]]),
            closed=False, alpha=0.8, facecolor='k', edgecolor='k')
        self.set_pane_color(self._axinfo['color'])

        self.axes._set_artist_props(self.line)
        self.axes._set_artist_props(self.pane)
        self.gridlines = art3d.Line3DCollection([])
        self.axes._set_artist_props(self.gridlines)
        self.axes._set_artist_props(self.label)
        self.axes._set_artist_props(self.offsetText)
        # Need to be able to place the label at the correct location
        self.label._transform = self.axes.transData
        self.offsetText._transform = self.axes.transData

    @cbook.deprecated("3.1")
    def get_tick_positions(self):
        majorLocs = self.major.locator()
        majorLabels = self.major.formatter.format_ticks(majorLocs)
        return majorLabels, majorLocs

    def get_major_ticks(self, numticks=None):
        ticks = maxis.XAxis.get_major_ticks(self, numticks)
        for t in ticks:
            t.tick1line.set_transform(self.axes.transData)
            t.tick2line.set_transform(self.axes.transData)
            t.gridline.set_transform(self.axes.transData)
            t.label1.set_transform(self.axes.transData)
            t.label2.set_transform(self.axes.transData)
        return ticks

    def set_pane_pos(self, xys):
        xys = np.asarray(xys)
        xys = xys[:, :2]
        self.pane.xy = xys
        self.stale = True

    def set_pane_color(self, color):
        '''Set pane color to a RGBA tuple.'''
        self._axinfo['color'] = color
        self.pane.set_edgecolor(color)
        self.pane.set_facecolor(color)
        self.pane.set_alpha(color[-1])
        self.stale = True

    def set_rotate_label(self, val):
        '''
        Whether to rotate the axis label: True, False or None.
        If set to None the label will be rotated if longer than 4 chars.
        '''
        self._rotate_label = val
        self.stale = True

    def get_rotate_label(self, text):
        if self._rotate_label is not None:
            return self._rotate_label
        else:
            return len(text) > 4

    def _get_coord_info(self, renderer):
        minx, maxx, miny, maxy, minz, maxz = self.axes.get_w_lims()
        if minx > maxx:
            minx, maxx = maxx, minx
        if miny > maxy:
            miny, maxy = maxy, miny
        if minz > maxz:
            minz, maxz = maxz, minz
        mins = np.array((minx, miny, minz))
        maxs = np.array((maxx, maxy, maxz))
        centers = (maxs + mins) / 2.
        deltas = (maxs - mins) / 12.
        mins = mins - deltas / 4.
        maxs = maxs + deltas / 4.

        vals = mins[0], maxs[0], mins[1], maxs[1], mins[2], maxs[2]
        tc = self.axes.tunit_cube(vals, renderer.M)
        avgz = [tc[p1][2] + tc[p2][2] + tc[p3][2] + tc[p4][2]
                for p1, p2, p3, p4 in self._PLANES]
        highs = np.array([avgz[2*i] < avgz[2*i+1] for i in range(3)])

        return mins, maxs, centers, deltas, tc, highs

    def draw_pane(self, renderer):
        renderer.open_group('pane3d')

        mins, maxs, centers, deltas, tc, highs = self._get_coord_info(renderer)

        info = self._axinfo
        index = info['i']
        if not highs[index]:
            plane = self._PLANES[2 * index]
        else:
            plane = self._PLANES[2 * index + 1]
        xys = [tc[p] for p in plane]
        self.set_pane_pos(xys)
        self.pane.draw(renderer)

        renderer.close_group('pane3d')

    @artist.allow_rasterization
    def draw(self, renderer):
        self.label._transform = self.axes.transData
        renderer.open_group('axis3d')

        ticks = self._update_ticks()

        info = self._axinfo
        index = info['i']

        mins, maxs, centers, deltas, tc, highs = self._get_coord_info(renderer)

        # Determine grid lines
        minmax = np.where(highs, maxs, mins)

        # Draw main axis line
        juggled = info['juggled']
        edgep1 = minmax.copy()
        edgep1[juggled[0]] = get_flip_min_max(edgep1, juggled[0], mins, maxs)

        edgep2 = edgep1.copy()
        edgep2[juggled[1]] = get_flip_min_max(edgep2, juggled[1], mins, maxs)
        pep = proj3d.proj_trans_points([edgep1, edgep2], renderer.M)
        centpt = proj3d.proj_transform(
            centers[0], centers[1], centers[2], renderer.M)
        self.line.set_data((pep[0][0], pep[0][1]), (pep[1][0], pep[1][1]))
        self.line.draw(renderer)

        # Grid points where the planes meet
        xyz0 = np.tile(minmax, (len(ticks), 1))
        xyz0[:, index] = [tick.get_loc() for tick in ticks]

        # Draw labels
        peparray = np.asanyarray(pep)
        # The transAxes transform is used because the Text object
        # rotates the text relative to the display coordinate system.
        # Therefore, if we want the labels to remain parallel to the
        # axis regardless of the aspect ratio, we need to convert the
        # edge points of the plane to display coordinates and calculate
        # an angle from that.
        # TODO: Maybe Text objects should handle this themselves?
        dx, dy = (self.axes.transAxes.transform([peparray[0:2, 1]]) -
                  self.axes.transAxes.transform([peparray[0:2, 0]]))[0]

        lxyz = 0.5*(edgep1 + edgep2)

        # A rough estimate; points are ambiguous since 3D plots rotate
        ax_scale = self.axes.bbox.size / self.figure.bbox.size
        ax_inches = np.multiply(ax_scale, self.figure.get_size_inches())
        ax_points_estimate = sum(72. * ax_inches)
        deltas_per_point = 48 / ax_points_estimate
        default_offset = 21.
        labeldeltas = (
            (self.labelpad + default_offset) * deltas_per_point * deltas)
        axmask = [True, True, True]
        axmask[index] = False
        lxyz = move_from_center(lxyz, centers, labeldeltas, axmask)
        tlx, tly, tlz = proj3d.proj_transform(lxyz[0], lxyz[1], lxyz[2],
                                              renderer.M)
        self.label.set_position((tlx, tly))
        if self.get_rotate_label(self.label.get_text()):
            angle = art3d._norm_text_angle(np.rad2deg(np.arctan2(dy, dx)))
            self.label.set_rotation(angle)
        self.label.set_va(info['label']['va'])
        self.label.set_ha(info['label']['ha'])
        self.label.draw(renderer)

        # Draw Offset text

        # Which of the two edge points do we want to
        # use for locating the offset text?
        if juggled[2] == 2:
            outeredgep = edgep1
            outerindex = 0
        else:
            outeredgep = edgep2
            outerindex = 1

        pos = copy.copy(outeredgep)
        pos = move_from_center(pos, centers, labeldeltas, axmask)
        olx, oly, olz = proj3d.proj_transform(
            pos[0], pos[1], pos[2], renderer.M)
        self.offsetText.set_text(self.major.formatter.get_offset())
        self.offsetText.set_position((olx, oly))
        angle = art3d._norm_text_angle(np.rad2deg(np.arctan2(dy, dx)))
        self.offsetText.set_rotation(angle)
        # Must set rotation mode to "anchor" so that
        # the alignment point is used as the "fulcrum" for rotation.
        self.offsetText.set_rotation_mode('anchor')

        #----------------------------------------------------------------------
        # Note: the following statement for determining the proper alignment of
        # the offset text. This was determined entirely by trial-and-error
        # and should not be in any way considered as "the way".  There are
        # still some edge cases where alignment is not quite right, but this
        # seems to be more of a geometry issue (in other words, I might be
        # using the wrong reference points).
        #
        # (TT, FF, TF, FT) are the shorthand for the tuple of
        #   (centpt[info['tickdir']] <= peparray[info['tickdir'], outerindex],
        #    centpt[index] <= peparray[index, outerindex])
        #
        # Three-letters (e.g., TFT, FTT) are short-hand for the array of bools
        # from the variable 'highs'.
        # ---------------------------------------------------------------------
        if centpt[info['tickdir']] > peparray[info['tickdir'], outerindex]:
            # if FT and if highs has an even number of Trues
            if (centpt[index] <= peparray[index, outerindex]
                    and len(highs.nonzero()[0]) % 2 == 0):
                # Usually, this means align right, except for the FTT case,
                # in which offset for axis 1 and 2 are aligned left.
                if highs.tolist() == [False, True, True] and index in (1, 2):
                    align = 'left'
                else:
                    align = 'right'
            else:
                # The FF case
                align = 'left'
        else:
            # if TF and if highs has an even number of Trues
            if (centpt[index] > peparray[index, outerindex]
                    and len(highs.nonzero()[0]) % 2 == 0):
                # Usually mean align left, except if it is axis 2
                if index == 2:
                    align = 'right'
                else:
                    align = 'left'
            else:
                # The TT case
                align = 'right'

        self.offsetText.set_va('center')
        self.offsetText.set_ha(align)
        self.offsetText.draw(renderer)

        # Draw grid lines
        if self.axes._draw_grid and len(ticks):
            # Grid points at end of one plane
            xyz1 = xyz0.copy()
            newindex = (index + 1) % 3
            newval = get_flip_min_max(xyz1[0], newindex, mins, maxs)
            xyz1[:, newindex] = newval

            # Grid points at end of the other plane
            xyz2 = xyz0.copy()
            newindex = (index + 2) % 3
            newval = get_flip_min_max(xyz2[0], newindex, mins, maxs)
            xyz2[:, newindex] = newval

            lines = np.stack([xyz1, xyz0, xyz2], axis=1)
            self.gridlines.set_segments(lines)
            self.gridlines.set_color(info['grid']['color'])
            self.gridlines.set_linewidth(info['grid']['linewidth'])
            self.gridlines.set_linestyle(info['grid']['linestyle'])
            self.gridlines.draw(renderer, project=True)

        # Draw ticks
        tickdir = info['tickdir']
        tickdelta = deltas[tickdir]
        if highs[tickdir]:
            ticksign = 1
        else:
            ticksign = -1

        for tick in ticks:

            # Get tick line positions
            pos = copy.copy(edgep1)
            pos[index] = tick.get_loc()
            pos[tickdir] = (
                edgep1[tickdir]
                + info['tick']['outward_factor'] * ticksign * tickdelta)
            x1, y1, z1 = proj3d.proj_transform(pos[0], pos[1], pos[2],
                                               renderer.M)
            pos[tickdir] = (
                edgep1[tickdir]
                - info['tick']['inward_factor'] * ticksign * tickdelta)
            x2, y2, z2 = proj3d.proj_transform(pos[0], pos[1], pos[2],
                                               renderer.M)

            # Get position of label
            default_offset = 8.  # A rough estimate
            labeldeltas = (
                (tick.get_pad() + default_offset) * deltas_per_point * deltas)

            axmask = [True, True, True]
            axmask[index] = False
            pos[tickdir] = edgep1[tickdir]
            pos = move_from_center(pos, centers, labeldeltas, axmask)
            lx, ly, lz = proj3d.proj_transform(pos[0], pos[1], pos[2],
                                               renderer.M)

            tick_update_position(tick, (x1, x2), (y1, y2), (lx, ly))
            tick.tick1line.set_linewidth(info['tick']['linewidth'])
            tick.tick1line.set_color(info['tick']['color'])
            tick.draw(renderer)

        renderer.close_group('axis3d')
        self.stale = False

    def get_view_interval(self):
        # docstring inherited
        return self.v_interval

    def set_view_interval(self, vmin, vmax, ignore=False):
        # docstring inherited
        if ignore:
            self.v_interval = vmin, vmax
        else:
            Vmin, Vmax = self.get_view_interval()
            self.v_interval = min(vmin, Vmin), max(vmax, Vmax)

    # TODO: Get this to work properly when mplot3d supports
    #       the transforms framework.
    def get_tightbbox(self, renderer):
        # Currently returns None so that Axis.get_tightbbox
        # doesn't return junk info.
        return None


# Use classes to look at different data limits


class XAxis(Axis):
    def get_data_interval(self):
        # docstring inherited
        return self.axes.xy_dataLim.intervalx


class YAxis(Axis):
    def get_data_interval(self):
        # docstring inherited
        return self.axes.xy_dataLim.intervaly


class ZAxis(Axis):
    def get_data_interval(self):
        # docstring inherited
        return self.axes.zz_dataLim.intervalx
