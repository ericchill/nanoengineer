# Copyright 2008-2009 Nanorex, Inc.  See LICENSE file for details. 
"""
ExternalBondSetDrawer.py - can draw an ExternalBondSet, and keep drawing caches
for it (e.g. display lists, perhaps for multiple drawing styles)

@author: Bruce
@version: $Id$
@copyright: 2008-2009 Nanorex, Inc.  See LICENSE file for details.

"""

from graphics.model_drawing.TransformedDisplayListsDrawer import TransformedDisplayListsDrawer

from graphics.drawing.ColorSorter import ColorSorter
from graphics.drawing.ColorSorter import ColorSortedDisplayList # not yet used?

# ==

class ExternalBondSetDrawer(TransformedDisplayListsDrawer):
    """
    """
    def __init__(self, ebset):
        # review: GL context not current now... could revise caller so it was
        self.ebset = ebset # the ExternalBondSet we'll draw
    
    def destroy(self):
        """
        remove cyclic refs, free display lists, etc
        """
        self.ebset = None
    
    def draw(self, glpane, disp, color, drawLevel): # selected? highlighted?
        # initial testing stub -- just draw in immediate mode, in the same way
        # as if we were not being used.
        # (notes for a future implem: 
        #  displist still valid (self.ebset._invalid)? culled?)


        ##### note: does not yet ever call superclass TransformedDisplayListsDrawer.draw, as of before 090211
        

        # modified from Chunk._draw_external_bonds:
        
        use_outer_colorsorter = True # not sure whether/why this is needed
        
        if use_outer_colorsorter:
            ColorSorter.start(None)

        for bond in self.ebset._bonds.itervalues():
            bond.draw(glpane, disp, color, drawLevel)
        
        if use_outer_colorsorter:
            ColorSorter.finish()

        return

    def _draw_into_displist(self, glpane, disp, drawLevel):
        color = None ###k
        for bond in self.ebset._bonds.itervalues():
            bond.draw(glpane, disp, color, drawLevel)
        return
        
    pass # end of class

# end