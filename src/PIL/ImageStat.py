#
# The Python Imaging Library.
# $Id$
#
# global image statistics
#
# History:
# 1996-04-05 fl   Created
# 1997-05-21 fl   Added mask; added rms, var, stddev attributes
# 1997-08-05 fl   Added median
# 1998-07-05 hk   Fixed integer overflow error
#
# Notes:
# This class shows how to implement delayed evaluation of attributes.
# To get a certain value, simply access the corresponding attribute.
# The __getattr__ dispatcher takes care of the rest.
#
# Copyright (c) Secret Labs AB 1997.
# Copyright (c) Fredrik Lundh 1996-97.
#
# See the README file for information on usage and redistribution.
#

import functools
import math
import operator


class Stat:
    def __init__(self, image_or_list, mask=None):
        try:
            self.h = image_or_list.histogram(mask) if mask else image_or_list.histogram()
        except AttributeError:
            self.h = image_or_list  # assume it to be a histogram list
        if not isinstance(self.h, list):
            raise TypeError("first argument must be image or list")
        self.bands = list(range(len(self.h) // 256))

    def __getattr__(self, id):
        """Calculate missing attribute"""
        if id[:4] == "_get":
            raise AttributeError(id)
        # calculate missing attribute
        v = getattr(self, f"_get{id}")()
        setattr(self, id, v)
        return v

    def _getextrema(self):
        """Get min/max values for each band in the image"""

        def minmax(histogram):
            n = 255
            x = 0
            for i in range(256):
                if histogram[i]:
                    n = min(n, i)
                    x = max(x, i)
            return n, x  # returns (255, 0) if there's no data in the histogram

        v = []
        for i in range(0, len(self.h), 256):
            v.append(minmax(self.h[i:]))
        return v

    def _getcount(self):
        """Get total number of pixels in each layer"""

        return [
            functools.reduce(operator.add, self.h[i : i + 256])
            for i in range(0, len(self.h), 256)
        ]

    def _getsum(self):
        """Get sum of all pixels in each layer"""

        v = []
        for i in range(0, len(self.h), 256):
            layerSum = 0.0
            for j in range(256):
                layerSum += j * self.h[i + j]
            v.append(layerSum)
        return v

    def _getsum2(self):
        """Get squared sum of all pixels in each layer"""

        v = []
        for i in range(0, len(self.h), 256):
            sum2 = 0.0
            for j in range(256):
                sum2 += (j**2) * float(self.h[i + j])
            v.append(sum2)
        return v

    def _getmean(self):
        """Get average pixel level for each layer"""

        return [self.sum[i] / self.count[i] for i in self.bands]

    def _getmedian(self):
        """Get median pixel level for each layer"""

        v = []
        for i in self.bands:
            s = 0
            half = self.count[i] // 2
            b = i * 256
            for j in range(256):
                s += self.h[b + j]
                if s > half:
                    break
            v.append(j)
        return v

    def _getrms(self):
        """Get RMS for each layer"""

        return [math.sqrt(self.sum2[i] / self.count[i]) for i in self.bands]

    def _getvar(self):
        """Get variance for each layer"""

        v = []
        for i in self.bands:
            n = self.count[i]
            v.append((self.sum2[i] - (self.sum[i] ** 2.0) / n) / n)
        return v

    def _getstddev(self):
        """Get standard deviation for each layer"""

        return [math.sqrt(self.var[i]) for i in self.bands]


Global = Stat  # compatibility
