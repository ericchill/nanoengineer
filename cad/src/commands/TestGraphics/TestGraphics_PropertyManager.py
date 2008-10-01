# Copyright 2008 Nanorex, Inc.  See LICENSE file for details. 
"""
TestGraphics_PropertyManager.py

@author: Bruce
@version: $Id$
@copyright: 2008 Nanorex, Inc. See LICENSE file for details.

"""
import foundation.env as env

from widgets.DebugMenuMixin import DebugMenuMixin

from PyQt4.Qt import SIGNAL
from PM.PM_Dialog   import PM_Dialog
from PM.PM_Slider   import PM_Slider
from PM.PM_GroupBox import PM_GroupBox
from PM.PM_ComboBox import PM_ComboBox
from PM.PM_CheckBox import PM_CheckBox

from PM.PM_Constants     import PM_DONE_BUTTON
from PM.PM_Constants     import PM_WHATS_THIS_BUTTON

from utilities.prefs_constants import levelOfDetail_prefs_key


from utilities.GlobalPreferences import KEEP_SIGNALS_ALWAYS_CONNECTED

# ==

class TestGraphics_PropertyManager( PM_Dialog, DebugMenuMixin ):
    """
    The TestGraphics_PropertyManager class provides a Property Manager 
    for the Test Graphics command. 

    @ivar title: The title that appears in the property manager header.
    @type title: str

    @ivar pmName: The name of this property manager. This is used to set
                  the name of the PM_Dialog object via setObjectName().
    @type name: str

    @ivar iconPath: The relative path to the PNG file that contains a
                    22 x 22 icon image that appears in the PM header.
    @type iconPath: str
    """

    title         =  "Test Graphics"
    pmName        =  title
    iconPath      =  None ###k "ui/actions/View/Stereo_View.png" ### FIX - use some generic or default icon


    def __init__( self, command ):
        """
        Constructor for the property manager.
        """
        self.command = command

        # review: some of the following are probably not needed:
        self.w = self.command.w
        self.win = self.command.w
        self.pw = self.command.pw
        self.o = self.win.glpane

        PM_Dialog.__init__(self, self.pmName, self.iconPath, self.title) # todo: clean up so superclass knows attrnames?

        DebugMenuMixin._init1( self )

        self.showTopRowButtons( PM_DONE_BUTTON |
                                PM_WHATS_THIS_BUTTON)

        msg = "Test the performance effect of graphics settings below. " \
              "(To avoid bugs, choose testCase before bypassing paintGL.)"

        self.updateMessage(msg)
        
        if KEEP_SIGNALS_ALWAYS_CONNECTED:
            self.connect_or_disconnect_signals(True)
            

    def show(self):
        """
        Shows the Property Manager. Overrides PM_Dialog.show.
        """
        PM_Dialog.show(self)
        
        if not KEEP_SIGNALS_ALWAYS_CONNECTED:
            self.connect_or_disconnect_signals(True)

    def close(self):
        """
        Closes the Property Manager. Overrides PM_Dialog.close.
        """
        if not KEEP_SIGNALS_ALWAYS_CONNECTED:
            self.connect_or_disconnect_signals(False)
            
        PM_Dialog.close(self)

    def _addGroupBoxes( self ):
        """
        Add the Property Manager group boxes.
        """
        self._pmGroupBox1 = PM_GroupBox( self, 
                                         title = "Settings") ### fix title
        self._loadGroupBox1( self._pmGroupBox1 )

    def _loadGroupBox1(self, pmGroupBox):
        """
        Load widgets in group box.
        """
        from widgets.prefs_widgets  import ObjAttr_StateRef ### toplevel
        
        self._cb1 = \
            PM_CheckBox(pmGroupBox,
                        text         = 'bypass paintGL',
                        )
        self._cb1.connectWithState( ObjAttr_StateRef( self.command, 'bypass_paintgl' ))

        self._cb2 = \
            PM_CheckBox(pmGroupBox,
                        text         = 'redraw continuously',
                        )        
        self._cb2.connectWithState( ObjAttr_StateRef( self.command, 'redraw_continuously' ))

        self._cb3 = \
            PM_CheckBox(pmGroupBox,
                        text         = 'spin model',
                        )        
        self._cb3.connectWithState( ObjAttr_StateRef( self.command, 'spin_model' ))

        self._cb4 = \
            PM_CheckBox(pmGroupBox,
                        text         = 'print fps to console',
                        )        
        self._cb4.connectWithState( ObjAttr_StateRef( self.command, 'print_fps' ))

        self.testCase_ComboBox = PM_ComboBox(pmGroupBox, 
                                      label =  "testCase:", labelColumn = 0,
                                      choices = self.command.testCaseChoicesText,
                                      setAsDefault = False )
        self.testCase_ComboBox.setCurrentIndex(self.command.testCaseIndex)
        
        self.detail_level_ComboBox = PM_ComboBox(pmGroupBox, 
                                      label =  "Level of detail:", labelColumn = 0,
                                      choices = ["Low", "Medium", "High", "Variable"],
                                      setAsDefault = False )
        lod = env.prefs[levelOfDetail_prefs_key]
        if lod == -1:
            lod = 3
        self.detail_level_ComboBox.setCurrentIndex(lod)

##        self._updateWidgets()
    
    def _addWhatsThisText( self ):
        """
        What's This text for widgets in the Stereo Property Manager.  
        """
        pass

    def _addToolTipText(self):
        """
        Tool Tip text for widgets in the Stereo Property Manager.  
        """
        pass

    def connect_or_disconnect_signals(self, isConnect):
        """
        Connect or disconnect widget signals sent to their slot methods.
        This can be overridden in subclasses. By default it does nothing.
        @param isConnect: If True the widget will send the signals to the slot 
                          method. 
        @type  isConnect: boolean
        """
        if isConnect:
            change_connect = self.win.connect
        else:
            change_connect = self.win.disconnect 

        change_connect(self.detail_level_ComboBox,
                       SIGNAL("currentIndexChanged(int)"),
                           # in current code, SIGNAL("activated(int)")
                       self.set_level_of_detail )

        change_connect(self.testCase_ComboBox,
                       SIGNAL("currentIndexChanged(int)"),
                       self.command._set_testCaseIndex )

        return

    # ==
    
    def set_level_of_detail(self, level_of_detail_item): # copied from other code
        """
        Change the level of detail, where <level_of_detail_item> is a value
        between 0 and 3 where:
            - 0 = low
            - 1 = medium
            - 2 = high
            - 3 = variable (based on number of atoms in the part)

        @note: the prefs db value for 'variable' is -1, to allow for higher LOD
               levels in the future.
        """
        lod = level_of_detail_item
        if level_of_detail_item == 3:
            lod = -1
        env.prefs[levelOfDetail_prefs_key] = lod

        if lod != -1:
            # kluge: not synced at init, -1 should be disallowed, should be in self.command
            import prototype.test_drawing as test_drawing
            test_drawing.DRAWSPHERE_DETAIL_LEVEL = lod
        
#        self.glpane.gl_update()
        # the redraw this causes will (as of tonight) always recompute the
        # correct drawLevel (in Part._recompute_drawLevel),
        # and chunks will invalidate their display lists as needed to
        # accomodate the change. [bruce 060215]
        return

##    def _updateWidgets(self):
##        """
##        Update stereo PM widgets.
##        """
##        if self._cb1.isChecked():
##            self.stereoModeComboBox.setEnabled(True)
##            self.stereoSeparationSlider.setEnabled(True)
##            self.stereoAngleSlider.setEnabled(True)
##            self._updateSeparationSlider()
##        else:
##            self.stereoModeComboBox.setEnabled(False)
##            self.stereoSeparationSlider.setEnabled(False)
##            self.stereoAngleSlider.setEnabled(False)
##            