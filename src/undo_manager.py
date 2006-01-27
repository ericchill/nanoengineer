# Copyright (c) 2005-2006 Nanorex, Inc.  All rights reserved.
'''
undo_manager.py

Own and manage an UndoArchive, feeding it info about user-command events
(such as when to make checkpoints and how to describe the diffs generated by user commands),
and package the undo/redo ops it offers into a reasonable UI.

$Id$

[060117 -- for current status see undo_archive.py module docstring]
'''
__author__ = 'bruce'


from debug import register_debug_menu_command_maker
import platform

from undo_archive import AssyUndoArchive #060117 revised
import undo_archive # for debug_undo2
from constants import noop
import env
from HistoryWidget import orangemsg, greenmsg, redmsg
from debug_prefs import debug_pref, Choice_boolean_True, Choice_boolean_False
from qt import SIGNAL
import time

class UndoManager:
    """[abstract class] [060117 addendum: this docstring is mostly obsolete or nim]
    Own and manage an undo-archive, in such a way as to provide undo/redo operations
    and a current-undo-point within the archive [addendum 060117: undo point might be in model objects or archive, not here,
      and since objects can't be in more than one archive or have more than one cur state (at present), this doesn't matter much]
    on top of state-holding objects which would otherwise not have these undo/redo ops
    (though they must have the ability to track changes and/or support scanning of their state).
       Assume that no other UndoManager or UndoArchive is tracking the same state-holding objects
    (i.e. we own them for undo-related purposes).
       #e future: Perhaps also delegate all command-method-calls to the state-holding objects...
    but for now, tolerate external code directly calling command methods on our state-holding objects,
    just receiving begin/end calls related to those commands and their subroutines or calling event-handlers,
    checkpoint calls from same, and undo/redo command callbacks.
    """
    pass

class AssyUndoManager(UndoManager):
    "An UndoManager specialized for handling the state held by an assy (an instance of class assembly)."
    def __init__(self, assy, menus = ()): # called from assy.__init__
        "Do what can be done early in assy.__init__; that must also (subsequently) call self.init1()"
        # assy owns the state whose changes we'll be managing...
        # [semiobs cmt:] should it have same undo-interface as eg chunks do??
        self._current_main_menu_ops = {}
        self.assy = assy
        self.menus = menus
        return

    def init1(self):
        "Do what we might do in __init__ except that it might be too early during assy.__init__ then"
        assy = self.assy
        self.archive = AssyUndoArchive(assy) # does initial checkpoint
        assy._u_archive = self.archive ####@@@@ still safe in 060117 stub code??
            # [obs??] this is how model objects in assy find something to report changes to (typically in their __init__ methods);
            # we do it here (not in caller) since its name and value are private to our API for model objects to report changes
##        self.archive.subscribe_to_checkpoints( self.remake_UI_menuitems )
##        self.remake_UI_menuitems() # so it runs for initial checkpoint and disables menu items, etc
        if platform.is_macintosh(): 
            win = assy.w
            win.editRedoAction.setAccel(win._MainWindow__tr("Ctrl+Shift+Z")) # set up incorrectly (for Mac) as "Ctrl+Y"
        self.connect_or_disconnect_menu_signals(True)
        self.auto_checkpoint_pref() # exercise this, so it shows up in the debug-prefs submenu right away
            # (fixes bug in which the pref didn't show up until the first undoable change was made) [060125]
        self.remake_UI_menuitems() # try to fix bug 1387 [060126]
        return
        
    def deinit(self):
        self.connect_or_disconnect_menu_signals(False)
        # and effectively destroy self... [060126 precaution; not thought through]
        self.archive.destroy()
        self._current_main_menu_ops = {}
        self.assy = self.menus = None
        #e more??
        return
    
    def connect_or_disconnect_menu_signals(self, connectQ): # this is a noop as of 060126
        win = self.assy.w
        if connectQ:
            method = win.connect
        else:
            method = win.disconnect
        for menu in self.menus:
            # this is useless, since we have to keep them always up to date for sake of accel keys and toolbuttons [060126]
            ## method( menu, SIGNAL("aboutToShow()"), self.remake_UI_menuitems ) ####k
            pass
        return
    
    def clear_undo_stack(self, *args, **kws):
        return self.archive.clear_undo_stack(*args, **kws)
    
    def menu_cmd_checkpoint(self):
        self.checkpoint( cptype = 'user_explicit' )

    def checkpoint(self, *args, **kws):
        res = self.archive.checkpoint( *args, **kws )
        # I hope this is safe even if auto-checkpointing is disabled; or maybe it's never called then [060126]
        self.remake_UI_menuitems() # needed here for toolbuttons and accel keys; not called for initial cp during self.archive init
            # (though for menu items themselves, the aboutToShow signal would be sufficient)
            #e relevant bugs: 1387, since toolbuttons need to get updated from the beginning
            # (this might not be called then, not sure) [060126] ####@@@@
        return res # maybe no retval, this is just a precaution

    def auto_checkpoint_pref(self):
        return debug_pref('undo auto-checkpointing? (slow)', Choice_boolean_False,
                        prefs_key = 'A7/undo/auto-checkpointing',
                        non_debug = True)
        
    def undo_checkpoint_before_command(self, cmdname = ""):
        """###doc
        [returns a value which should be passed to undo_checkpoint_after_command;
         we make no guarantees at all about what type of value that is, whether it's boolean true, etc]
        """
        #e should this be renamed begin_cmd_checkpoint() or begin_command_checkpoint() like I sometimes think it's called?
        # recheck the pref every time
        auto_checkpointing = self.auto_checkpoint_pref()
        if not auto_checkpointing:
            return False
        # (everything before this point must be kept fast)
        cmdname2 = cmdname or "command"
        if undo_archive.debug_undo2:
            env.history.message("debug_undo2: begin_cmd_checkpoint for %r" % (cmdname2,))
        # this will get fancier, use cmdname, worry about being fast when no diffs, merging ops, redundant calls in one cmd, etc:
        self.checkpoint( cptype = 'begin_cmd', cmdname_for_debug = cmdname )
        if cmdname:
            self.archive.current_command_info(cmdname = cmdname) #060126
        return True # this code should be passed to the matching undo_checkpoint_after_command (#e could make it fancier)

    def undo_checkpoint_after_command(self, begin_retval):
        assert begin_retval in [False, True], "begin_retval should not be %r" % (begin_retval,)
        if begin_retval:
            # this means [as of 060123] that debug pref for undo checkpointing is enabled
            if undo_archive.debug_undo2:
                env.history.message("  debug_undo2: end_cmd_checkpoint")
            # this will get fancier, use cmdname, worry about being fast when no diffs, merging ops, redundant calls in one cmd, etc:
            self.checkpoint( cptype = 'end_cmd' )
            pass
        return

    def current_command_info(self, *args, **kws):
        self.archive.current_command_info(*args, **kws)
    
    def undo_redo_ops(self):
        # copied code below [dup code is in undo_manager_older.py, not in cvs]
        ops = self.archive.find_undoredos() # state_version - now held inside UndoArchive.last_cp (might be wrong) ###@@@
        undos = []
        redos = []
        d1 = {'Undo':undos, 'Redo':redos}
        for op in ops:
            optype = op.optype()
            d1[optype].append(op) # sort ops by type
        # remove obsolete redo ops
        if redos:
            lis = [ (redo.cps[1].cp_counter, redo) for redo in redos ]
            lis.sort()
            only_redo = lis[-1][1]
            redos = [only_redo]
            for obs_redo in lis[:-1]:
                if undo_archive.debug_undo2:
                    print "obsolete redo:",obs_redo
                pass #e discard it permanently? ####@@@@
        return undos, redos
    
    def undo_cmds_menuspec(self, widget):
        """return a menu_spec for including undo-related commands in a popup menu
        (to be shown in the given widget, tho i don't know why the widget could matter)
        """
        del widget
        archive = self.archive
        # copied code below [dup code is in undo_manager_older.py, not in cvs]
        res = []
        res.append(( 'undo checkpoint (in RAM only)', self.menu_cmd_checkpoint ))

        undos, redos = self.undo_redo_ops()
        ###e sort each list by some sort of time order (maybe of most recent use of the op in either direction??), and limit lengths
        
        # there are at most one per chunk per undoable attr... so for this test, show them all, don't bother with submenus
        if not undos:
            res.append(( "Nothing we can Undo", noop, 'disabled' ))
                ###e should figure out whether "Can't Undo XXX" or "Nothing to Undo" is more correct
        for op in undos + redos:
            # for now, we're not even including them unless as far as we know we can do them, so no role for "Can't Undo" unless none
            arch = archive # it's on purpose that op itself has no ref to model, so we have to pass it [obs cmt?]
            cmd = lambda _guard1_ = None, _guard2_ = None, arch = arch: arch.do_op(op) #k guards needed? (does qt pass args to menu cmds?)
            ## text = "%s %s" % (op.type, op.what())
            text = op.menu_desc()
            res.append(( text , cmd ))
        if not redos:
            res.append(( "Nothing we can Redo", noop, 'disabled' ))
        return res

    def remake_UI_menuitems(self):
        #e see also: void QPopupMenu::aboutToShow () [signal], for how to know when to run this (when Edit menu is about to show);
        # to find the menu, no easy way (only way: monitor QAction::addedTo in a custom QAction subclass - not worth the trouble),
        # so just hardcode it as edit menu for now. We'll need to connect & disconnect this when created/finished,
        # and get passed the menu (or list of them) from the caller, which is I guess assy.__init__.
        if undo_archive.debug_undo2:
            print "debug_undo2: running remake_UI_menuitems (could be direct call or signal)"
        undos, redos = self.undo_redo_ops()
        win = self.assy.w
        undo_mitem = win.editUndoAction
        redo_mitem = win.editRedoAction
        for ops, action, optype in [(undos, undo_mitem, 'Undo'), (redos, redo_mitem, 'Redo')]: #e or could grab op.optype()?
            extra = ""
            if undo_archive.debug_undo2:
                extra = " (%s)" % str(time.time()) # show when it's updated in the menu text (remove when works) ####@@@@
            if ops:
                action.setEnabled(True)
                assert len(ops) == 1 #e there will always be just one for now
                op = ops[0]
                text = op.menu_desc() + extra #060126
                action.setMenuText(text)
                fix_tooltip(action, text) # replace description, leave (accelkeys) alone (they contain unicode chars on Mac)
                self._current_main_menu_ops[optype] = op #e should store it into menu item if we can, I suppose
            else:
                action.setEnabled(False)
                ## action.setText("Can't %s" % optype) # someday we might have to say "can't undo Cmdxxx" for certain cmds
                ## action.setMenuText("Nothing to %s" % optype)
                text = "%s" % optype + extra
                action.setMenuText(text) # for 061117 commit, look like it used to look, for the time being
                fix_tooltip(action, text)
                self._current_main_menu_ops[optype] = None
            pass
        return
        ''' the kinds of things we can set on one of those actions include:
        self.setViewFitToWindowAction.setText(self.__tr("Fit to Window"))
        self.setViewFitToWindowAction.setMenuText(self.__tr("&Fit to Window"))
        self.setViewFitToWindowAction.setToolTip(self.__tr("Fit to Window (Ctrl+F)"))
        self.setViewFitToWindowAction.setAccel(self.__tr("Ctrl+F"))
        self.setViewRightAction.setStatusTip(self.__tr("Right View"))
        self.helpMouseControlsAction.setWhatsThis(self.__tr("Displays help for mouse controls"))
        '''
    # main menu items (their slots in MWsemantics forward to assy which forwards to here)
    def editUndo(self):
        ## env.history.message(orangemsg("Undo: (prototype)"))
        self.do_main_menu_op('Undo')

    def editRedo(self):
        ## env.history.message(orangemsg("Redo: (prototype)"))
        self.do_main_menu_op('Redo')

    def do_main_menu_op(self, optype):
        "optype should be Undo or Redo"
        try:
            op = self._current_main_menu_ops.get(optype)
            if op:
                undo_xxx = op.menu_desc()
                env.history.message("%s" % undo_xxx) #e add history sernos #e say Undoing rather than Undo in case more msgs??
                self.archive.do_op(op)
            else:
                print "no op to %r; not sure how this slot was called, since it should have been disabled" % optype
                env.history.message(redmsg("Nothing to %s (and it's a bug that this message was printed)" % optype))
            pass
        except:
            print_compact_traceback()
            env.history.message(redmsg("Bug in %s; see traceback in console" % optype))
        return
    
    pass # end of class AssyUndoManager

# ==

#e refile
def fix_tooltip(qaction, text): #060126
    """Assuming qaction's tooltip looks like "command name (accel keys)" and might contain unicode in accel keys
    (as often happens on Mac due to symbols for Shift and Command modifier keys),
    replace command name with text, leave accel keys unchange (saving result into actual tooltip).
    """
    whole = unicode(qaction.toolTip()) # str() on this might have an exception
    try:
        if 1: #bruce 060127 kluge to fix bug 1405; ok for now since only fake command names contain parens
            text = text.replace('(','[')
            text = text.replace(')',']')
        sep = u' ('
        parts = whole.split(sep, 1) #e is it safe to assume the whitespace is a single blank? should generalize...
        parts[0] = text
        whole = sep.join(parts)
        # print "formed tooltip",`whole` # printing whole might have an exception, but printing `whole` is ok
        qaction.setToolTip(whole) # no need for __tr, I think?
    except:
        print_compact_traceback("exception in fix_tooltip(%r, %r): " % (qaction, text) )
    return

# == debugging code - invoke undo/redo from debug menu (only) in initial test implem

def undo_cmds_maker(widget):
    ###e maybe this belongs in assy module itself?? clue: it knows the name of assy.undo_manager; otoh, should work from various widgets
    "[widget is the widget in which the debug menu is being put up right now]"
    #e in theory we use that widget's undo-chain... but in real life this won't even happen inside the debug menu, so nevermind.
    # for now just always use the assy's undo-chain.
    # hmm, how do we find the assy? well, ok, i'll use the widget.
    try:
        assy = widget.win.assy
    except:
        import platform
        if platform.atom_debug:
            return [('atom_debug: no undo in this widget', noop, 'disabled')]
        return []
##    if 'kluge' and not hasattr(assy, 'undo_manager'):
##        assy.undo_manager = UndoManager(assy) #e needs review; might just be a devel kluge, or might be good if arg type is unciv
    mgr = assy.undo_manager #k should it be an attr like this, or a sep func?
    return mgr.undo_cmds_menuspec(widget)

register_debug_menu_command_maker( "undo_cmds", undo_cmds_maker)
    # fyi: this runs once when the first assy is being created, but undo_cmds_maker runs every time the debug menu is put up.

# end
