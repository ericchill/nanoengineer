"""
CommandSequencer.py - prototype (or stub) Command Sequencer.
For now, this is just class modeMixin, which acts as the
"Command Sequencer aspect of the GLPane"; this will either
be replaced by or evolve into a real Command Sequencer.

(Until we decide, I kept the old class name to avoid a false promise
of good design, but on 071030 gave it a new module name to
make the role in the current code clear.)

$Id$

History:

- written by Bruce long ago, in modes.py, mixed into GLPane.py

- split into its own file, bruce 071009

- file (but not class) renamed to CommandSequencer, bruce 071030

TODO:

roughly: mode -> command or currentCommand, prevMode -> _prevCommand or worse,
glpane -> commandSequencer; and then on to real refactoring. Also, some of the logic
in basicMode is really part of the command sequencer (which basicMode should just
interface to rather than "try to be").
"""

from debug import print_compact_traceback, print_compact_stack
import platform
import env

from modes import nullMode

from Command import anyCommand # only needed for an isinstance assertion
from GraphicsMode_API import GraphicsMode_API 

# ==

# TODO: mode -> command or currentCommand in lots of comments, some method names

class modeMixin(object):
    """
    Mixin class for supporting command-switching in GLPane. Basically it's
    a primitive Command Sequencer which for historical reasons lives
    temporarily as a mixin in the GLPane.

    Maintains instance attributes currentCommand, graphicsMode
    (both read-only for public access), and mostly private
    attributes for access by command-sequencing code in class Command,
    such as nullmode and commandTable.
    """
    # TODO: turn this into a standalone command sequencer object,
    # which also contains some logic now in class Command
    #
    # older comment: this class will be replaced with an aspect of the command sequencer,
    # and will use self.currentCommand rather than self.mode...
    # so some code which uses glpane.mode is being changed to get commandSequencer
    # from win.commandSequencer (which for now is just the glpane; that will change)
    # and then use commandSequencer.currentCommand. But the command-changing methods
    # like userEnterCommand are being left as commandSequencer.userEnterCommand
    # until they're better understood. [bruce 071008 comment]

    # Note: see "new code" far below for comments and definitions about the
    # attributes of self which we maintain, namely mode, graphicsMode, currentCommand.

    prevMode = None #bruce 071011 added this
    
    def _init_modeMixin(self): #bruce 071010 renamed from _init1, since that name is used on several classes
        """
        call this near the start of __init__ in a subclass that mixes us in (i.e. GLPane)
        """
        self._recreate_nullmode()
        self.use_nullmode()
        return

    def _recreate_nullmode(self):
        self.nullmode = nullMode() # TODO: rename self.nullmode; note that it's semi-public
            # a safe place to absorb events that come at the wrong time
            # (in case of bugs, but also happens routinely sometimes)
        return
    
    def _reinit_modes(self): #bruce 050911 revised this
        """
        [bruce comment 040922, when I split this out from GLPane's
        setAssy method; comment is fairly specific to GLPane:]

        Call this near the end of __init__, and whenever the mode
        objects need to be remade.  Create new mode objects (one
        for each mode, ready to take over mouse-interaction
        whenever that mode is in effect).

        [As of 050911, leave self.mode as nullmode, not the default mode.]

        We redo this whenever
        the current assembly changes, since the mode objects store
        the current assembly in some menus they make. (At least
        that's one reason I noticed -- there might be more. None of
        this was documented before now.)  (#e Storing the current
        assembly in the modes might cause trouble, if our
        functionality is extended in certain ways; if we someday
        fix that, the mode objects could be retained for the
        lifetime of their command sequencer. But there's no reason we need to
        keep them longer, unless they store some other sort of
        state (like user preferences), which is probably also bad
        for them to do. So we can ignore this for now.)
        """
        if not self._raw_currentCommand.is_null:
            ###e need to give current mode a chance to exit cleanly,
            ###or refuse -- but callers have no provision for our
            ###refusing (which is a bug); so for now just abandon
            # work, with a warning if necessary
            try:
                self.currentCommand.Abandon()
            except:
                print "bug, error while abandoning old mode; ignore it if we can..." #e
        self.use_nullmode()
            # not sure what bgcolor nullmode has, but it won't last long...
        self.commandTable = {}
        # this destroys any mode objects that already existed [note,
        # this name is hardcoded into the mode objects]

        # create new mode objects; they know about our self.commandTable
        # member and add themselves to it; they know their own names
        #bruce 050911 revised this: other_mode_classes -> mode_classes (includes class of default mode)
        for mc in self.mode_classes: 
            mc(self) # kluge: new mode object adds itself to self.commandTable -- this needs to be cleaned up sometime.

        #bruce 050911 removed this; now we leave it at nullmode,
        # let direct or indirect callers put in the mode they want
        # (since different callers want different modes, and during init
        #  some modes are not ready to be entered anyway)
        ## self.start_using_mode( '$DEFAULT_MODE')
        
        return # from _reinit_modes
    
    # methods for starting to use a given mode (after it's already
    # chosen irrevocably, and any prior mode has been cleaned up)

    def stop_sending_us_events(self, command):
        """
        Semi-internal method (called by command instances):
        Stop sending events to the given command (or to any actual command
        object besides the nullCommand).
        """
        if not self.is_this_command_current(command):
            # we weren't sending you events anyway, what are you
            # talking about?!?" #k not sure this is an error
            print "fyi (for developers): stop_sending_us_events called from %r which is not currentCommand %r" % \
                  (command, self._raw_currentCommand)
        self.use_nullmode()

    def use_nullmode(self):
        self._raw_currentCommand = self.nullmode

    def is_this_command_current(self, command):
        """
        Semi-private method for use by Command.isCurrentCommand;
        for doc, see that method.
        """
        # We compare to self._raw_currentCommand in case self.currentCommand
        # has been wrapped by an API-enforcement (or any other) proxy.
        return self._raw_currentCommand is command

##    def isNullCommand(self, command):
##        return command.is_null
    
    def start_using_mode(self, mode, resuming = False, has_its_own_gui = True): #bruce 070813 added resuming option
        """
        Semi-internal method (meant to be called only from self
        (typically a GLPane) or from one of our mode objects):
        Start using the given mode (name or object), ignoring any prior mode.
        If the new mode refuses to become current
        (e.g. if it requires certain kinds of selection which are not present),
        it should emit an appropriate message and return True; we'll then
        start using our default mode, or if that fails, some always-safe mode.

        @param resuming: see _enterMode method.
                         ###TODO: describe it here, and fix rest of docstring re this.
        """
        # note: resuming option often comes from **new_mode_options in callers
        #bruce 050317: do update_parts to insulate new mode from prior one's bugs
        try:
            self.assy.update_parts()
            # Note: this is overkill (only known to be needed when leaving
            # extrude, and really it's a bug that it doesn't do this itself),
            # and potentially too slow (though I doubt it),
            # and not a substitute for doing this at the end of operations
            # that need it (esp. once we have Undo); but doing it here will make things
            # more robust. Ideally we should "assert_this_was_not_needed".
        except:
            print_compact_traceback("bug: update_parts: ")
        else:
            if platform.atom_debug:
                self.assy.checkparts() #bruce 050315 assy/part debug code
        
        #e (Q: If the new mode refuses to start,
        #   would it be better to go back to using the immediately
        #   prior mode, if different? Probably not... if so, we'd need
        #   to split this into the query to the new mode for whether
        #   it will accept, and the switch to it, so the prior mode
        #   needn't worry about its state if the new mode won't even
        #   accept.)
        if not resuming:
            self.use_nullmode()
            # temporary (prevent bug-risk of reentrant event processing by
            # current mode)

        #bruce 050911: we'll try a list of modes in order, but never try to enter the same mode-object more than once.
        modes = [mode, '$DEFAULT_MODE', '$SAFE_MODE']
        del mode
        mode_objects = [] # so we don't try the same object twice
            # Note: we keep objects, not ids, so objects are kept alive so their ids are not recycled.
            # This doesn't matter as of 050911 but it might in the future if mode objects become more transient
            # (though at that point the test might fail to avoid trying some mode-classes twice, so it will need review).
        for mode in modes:
            # mode can be mode name (perhaps symbolic) or mode object
            try:
                entering_msg = "entering/resuming some mode" # only used in case of unlikely bugs
                modename = '???' # in case of exception before (or when) we set it from mode object
                mode = self._find_mode(mode) # figure out which mode object to use
                    # [#k can this ever fail?? should it know default mode?##]
                modename = mode.modename # store this now, so we can handle exceptions later or one from this line
                if id(mode) in map(id, mode_objects):
                    continue
                entering_msg = self.__Entering_Mode_message( mode, resuming = resuming) # value saved only for error messages
                    #bruce 050515: moved this "Entering Mode" message to before _enterMode
                    # so it comes before any history messages that emits. If the new mode
                    # refuses (but has no exception), assume it will emit a message about that.
                    #bruce 050106: added this status/history message about new mode...
                    # I'm not sure this is the best place to put it, but it's the best
                    # existing single place I could find.
                refused = mode._enterMode(resuming = resuming, 
                                          has_its_own_gui = has_its_own_gui)
                    # let the mode get ready for use; it can assume self.currentCommand
                    # will be set to it, but not that it already has been.  It
                    # should emit a message and return True if it wants to
                    # refuse becoming the new mode.
            except:
                msg = "bug: exception %s" % (entering_msg,)
                print_compact_traceback("%s: " % msg)
                from utilities.Log import redmsg
                env.history.message( redmsg( "internal error entering mode, trying default or safe mode" ))
                    ###TODO: modify message when resuming is true
                    # Emit this whether or not it's too_early!
                    # Assuming not too early, no need to name mode since prior histmsg did so.
                refused = 1
            if not refused:
                # We're in the new command -- start sending glpane events to its graphicsMode
                # and other events from command sequencer directly to it.
                self._raw_currentCommand = mode
                break
                #bruce 050515: this is old location of Entering Mode histmsg, now moved before _enterMode
                # [that comment is from before the for loop existed]
            # exception or refusal: try the next mode in the list (if any)
            continue
        # if even $SAFE_MODE failed (serious bug), we might as well just stick with self.currentCommand being nullMode...
        self.update_after_new_mode()
        return # from start_using_mode
    
    def __Entering_Mode_message(self, mode, resuming = False): #bruce 050911 split this out of its sole caller
        if resuming:
            msg = "Resuming %s" % mode.default_mode_status_text
        else:
            msg = "Entering %s" % mode.default_mode_status_text
            # semi-kluge, since that text starts with "Mode: ..." by convention;
            # also, not clear if we should use get_mode_status_text instead.
        try: # bruce 050112
            # (could be made cleaner by defining too_early in HistoryWidget,
            #  or giving message() a too_early_ok option)
            too_early = env.history.too_early # true when early in init
        except AttributeError: # not defined after init!
            too_early = 0
        if not too_early:
            from utilities.Log import greenmsg
            env.history.message( greenmsg( msg), norepeat_id = msg )
        return msg
    
    def _find_mode(self, modename_or_obj = None): #bruce 050911 and 060403 revised this
        """
        Internal method: look up the specified internal mode name (e.g. 'MODIFY' for Move mode)
        or mode-role symbolic name (e.g. '$DEFAULT_MODE') in self.commandTable, and return the mode object found.
        Or if a mode object is provided, return the same-named object in self.commandTable
        (warning if it's not the same object, since this might indicate a bug).

        Exception if requested mode object is not found -- unlike pre-050911 code,
        never return some other mode than asked for -- let caller do that if desired.
        """
        import UserPrefs #bruce 060403
        assert modename_or_obj, "mode arg should be a mode object or mode name, not None or whatever it is here: %r" % (modename_or_obj,)
        if type(modename_or_obj) == type(''):
            # usual case - internal or symbolic modename string
            modename = modename_or_obj
            if modename == '$SAFE_MODE':
                modename = 'SELECTMOLS' #k
            elif modename == '$STARTUP_MODE':
                ## modename = env.prefs[startupMode_prefs_key]
                modename = UserPrefs.startup_modename()
                # Needed when Preferences | Modes | Startup Mode = Default Mode.  
                # Mark 050921.
                if modename == '$DEFAULT_MODE':
                    ## modename = env.prefs[defaultMode_prefs_key]
                    modename = UserPrefs.default_modename()
            elif modename == '$DEFAULT_MODE':
                ## modename = env.prefs[defaultMode_prefs_key]
                modename = UserPrefs.default_modename()
            return self.commandTable[ modename]
        else:
            # assume it's a mode object; make sure it's legit
            mode0 = modename_or_obj
            modename = mode0.modename
            mode1 = self.commandTable[modename] # the one we'll return
            if mode1 is not mode0:
                # this should never happen
                print "bug: invalid internal mode; using mode %r" % (modename,)
            return mode1
        pass

    # user requests a specific new mode.

    def userEnterCommand(self, modename, **options): # renamed from setMode [bruce 071011]
        """
        Public method, called from the UI when the user asks to enter
        a specific command (named by modename), e.g. using a toolbutton
        or menu item. It can also be called inside commands which want to
        change to another command.

        The modename argument can be a modename string, e.g. 'DEPOSIT',
        or a symbolic name like '$DEFAULT_MODE', or [### VERIFY THIS]
        a command instance object. (Details of modename, and all options,
        are documented in Command._f_userEnterCommand.)

        The current command has to exit (or be suspended) before the new one
        can be entered, but it's allowed to refuse to exit, and if it does
        exit it needs a chance to clean up first. So we let the current
        command implement this method and decide whether to honor the user's
        request. (If it doesn't, it should emit a message explaining why not.
        If it does, it should call the appropriate lower-level command-switching
        method [### TODO: doc what those are or where to find out].

        (If that raises an exception, we assume the current command has a bug
        and fall back to default behavior here.)

        TODO: The tool icons ought to visually indicate the current command,
        but for now this is done by ad-hoc code inside individual commands
        rather than in any uniform way. One defect of that scheme is that
        the code for each command has to know what UI buttons might invoke it;
        another is that it leads to that code assuming that a UI exists,
        complicating future scripting support. When this is improved, the
        updating of toolbutton status might be done by self.update_after_new_mode().
        [Note, that's now in GLPane but should probably move into this class.]
        
        See also: userEnterTemporaryCommand
        """
        # Note: we don't have a special case for already being in the same
        # command; individual commands can implement that if they wish.
        try:
            self.currentCommand._f_userEnterCommand(modename, **options)

            # REVIEW: the following update_after_new_mode looks redundant with
            # the one at the end of start_using_mode, if that one has always
            # run at this point (which I think, but didn't prove). [bruce 070813 comment]
            
            # TODO, maybe: let current command decide whether/how to do this update:
            self.update_after_new_mode()
                # might be unnecessary if command didn't change -- that's ok
        except:
            # This should never happen unless there's a bug in some command --
            # so don't bother trying to get into the user's requested
            # command, just get into a safe state.
            print_compact_traceback("_f_userEnterCommand: ")
            print "bug: _f_userEnterCommand(%r) had bug when in mode %r; changing back to default mode" % (modename, self.currentCommand,)
            # For some bugs, the old mode will have left its toolbar
            # up; we should probably try to call its restore_gui
            # method directly... ok, I added this, though it's
            # untested! ###k It looks safe, and only runs if there's a
            # definite bug anyway. [bruce 040924]
            try:
                self.win.setFocus() #bruce 041010 bugfix (needed in two places)
                    # (I think that was needed to prevent key events from being sent to
                    #  no-longer-shown mode dashboards. [bruce 041220])
                self.currentCommand.restore_gui()
                    ###REVIEW: restore_gui is probably wrong when options caused
                    # us merely to suspend, not exit, the old mode. [bruce 070814 comment]
            except:
                print "(...even the old mode's restore_gui method, run by itself, had a bug...)"
            self.start_using_mode( '$DEFAULT_MODE' )
        return

    def userEnterTemporaryCommand(self, modename): #bruce 071011
        """
        Temporarily enter the command with the given modename [TODO: or the given command object?],
        suspending the prior command for resumption after the new one exits,
        unless the prior command.command_can_be_suspended is false
        (usually the case if it too is a temporary command),
        in which case, the command that will be resumed then is the
        same one it was before entering the new command.
        (This means a series of temporary commands can be run,
        after which the prior non-temporary one will be resumed.)

        Note: semantics/API is likely to be revised; see code comments.

        See also: userEnterCommand
        """
        # REVIEW: do we need to generalize command.command_can_be_suspended
        # to a relation between two commands
        # that says whether one can be suspended by another,
        # or whether one can suspend another,
        # based on which commands they are?
         
        # REVIEW: should this method be an option on userEnterCommand or _f_userEnterCommand
        # rather than a separate method? Will those need to call this if the
        # command they are asked to enter is marked a temporary one?]

        # TODO: Whatever the answers, ultimately the command sequencer needs to be
        # responsible for deciding how to enter and exit each command,
        # rather than relying on the commands themselves to do this.
        # In particular, no command should override Done to know about prevMode --
        # instead, the sequencer should record how the command was entered
        # and whether it suspended prevMode then. The command can just declare its
        # type and options in ways which influence the sequencer re this.
        
        #bruce 071011 split this out of Zoom/Pan/Rotate support in ops_view.py;
        # also using it for Paste/Partlib commands in MWsemantics.py
        # (not sure it's identical to what they did, but if not it might be safer)

        # Implementation:
        #
        # If the current command is suspendable,
        # save it in self.prevMode (TODO: make that private)
        # and suspend it while entering the new one.
        # (For now we never have more than one suspended command
        #  at a time.)
        #
        # Otherwise, effectively, immediately exit the current command
        # (which is non-suspendable, probably temporary)
        # and don't change prevMode (so that the suspended
        # command to be resumed later is not changed),
        # and enter the new command in the normal way (###k??).
        #
        # But this is most easily done in a different way with the
        # same effect: exit the current command first (resuming prevMode)
        # and then immediately enter the new one (saving the same value
        # of prevMode again), entering it in the same way as otherwise.
        # [Implem revised by bruce 070814; comment updated by bruce 071011.]
        
        prior_command = self._raw_currentCommand # might be changed inside if statement below
   

        assert not prior_command.is_null # neither case below looks correct for nullmode

        if not prior_command.command_can_be_suspended:
            # (This usually means we're already in a temporary command)
            # Since we can't suspend the prior command, just exit it.
            # (If this toggles off its button and runs this method recursively,
            #  that will cause bugs. TODO -- detect that, fix it if it happens.)
            prior_command.Done(exit_using_done_or_cancel = False)
                # presumably this reenters the prior suspended command (prevMode)
                # (since there probably was one if prior_command was temporary),
                # but if so, we'll immediately resuspend it below.
            prior_command = self._raw_currentCommand # (an even more prior command)
            assert prior_command.command_can_be_suspended # also implies it's not null
        
        # Set self.prevMode (our depth-1 suspended command stack)
        self.prevMode = prior_command # bruce 070813 save command object, not modename
        self.userEnterCommand(modename, suspend_old_mode = True)
            # TODO: if this can become the only use of suspend_old_mode, make it a private option _suspend_old_mode.
            # Indeed, it's now the only use except for internal and commented out ones... [071011 eve]
        return

    # ==

    # delegation to saved commands

    def prior_command_Draw(self, calling_command):
        """
        Draw whatever the prior command (relative to calling_command, a Command object)
        would draw in its own Draw method, if it was the currentCommand.
        (Exception: the prior command is allowed to find out it's not current
         and to modify its display style in response to that.)
         
        Return True if you find a prior command and call its Draw method, False otherwise.
        """
        # Note: if we wanted, the method name 'Draw' could be an argument
        # so we could delegate anything at all to prevMode in this way.
        # We'd need a flag or variant method to say whether to call it in
        # the Command or GraphicsMode part. (Or pass a lambda?? Seems like in
        # that case we should just make prevMode public instead...)
        
        # We define "prior" relative to calling_command... but so far we only know
        # how to do that for the current command:
        assert self._raw_currentCommand is calling_command, \
               "prior_command_Draw doesn't yet work except from currentCommand %r (was called from %r)" % \
               ( self._raw_currentCommand, calling_command)
            # (Maybe we'll need to generalize that to knowing how to do it for calling_command == prevMode too,
            # which is presumably just to return False, given the depth-1 command stack we have at present.)
        prevMode = self.prevMode # really a Command object of some kind -- TODO, rename to _savedCommand or so
        if prevMode is not None:
            assert not prevMode.is_null
            prevMode.graphicsMode.Draw()
            # WARNING/TODO: this implem assumes there is at most one saved command
            # which should be drawn. If this changes, we'll need to replace
            # .prevMode with a deeper command stack in the Command Sequencer
            # which provides a way to draw whatever each suspended command
            # thinks it needs to; or we'll need to arrange for prevMode
            # to *be* that stack, delegating Draw to each stack element in turn.
            # [bruce 071011]
            return True
        return False

    # ==
    
    # new code, mostly for the transition to a real command sequencer and a separate currentCommand and graphicsMode
    # [bruce 071010]

    # Note (from point of view of class GLPane, into which we are or were mixed):
    # external code expects self.currentCommand to always be a
    # working Command object, which has certain callable methods,
    # and expects self.graphicsMode to be a working GraphicsMode object.
    # We'll make this true as soon as possible, and
    # make sure it remains true after that -- even during
    # __init__ and during transitions between commands, when
    # no events should come unless there are reentrance
    # bugs in event processing. [bruce 040922, revised 071011]

    # We store the actual currentCommand object on self.__raw_currentCommand (starts with two underscores);
    # to set that directly (only within this class's internal code),
    # use the property for self._raw_currentCommand (starts with one underscore).

    __raw_currentCommand = None

    def _get__raw_currentCommand(self):
        return self.__raw_currentCommand
    
    def _set__raw_currentCommand(self, command):
        assert isinstance(command, anyCommand)
        self.__raw_currentCommand = command
        return

    _raw_currentCommand = property( _get__raw_currentCommand, _set__raw_currentCommand)

    # Old and new code can access this in various ways;
    # these are illegal to set in new code, but setting them
    # might be allowed (with a complaint) in old code;
    # for each attribute we make a property with both set and get methods
    # (so direct sets never happen without intervention)

    # currentCommand

    def _get_currentCommand(self):
        # TODO: wrap with an API enforcement proxy for Command.
        # WARNING: if we do that, the 'is' test in isCurrentCommand will need revision!
        # (Searching for ".currentCommand is" will find that test.)
        return self._raw_currentCommand

    def _set_currentCommand(self, command):
        assert 0, "illegal to set %r.currentCommand directly" % self

    currentCommand = property( _get_currentCommand, _set_currentCommand)
    
    # graphicsMode

    def _get_graphicsMode(self):
        # TODO: wrap with an API enforcement proxy for GraphicsMode.
        # WARNING: if we do that, any 'is' test on .graphicsMode will need revision.
        # (Searching for ".graphicsMode is" will find at least one such test.)
        res = self._raw_currentCommand.graphicsMode # may or may not be same as self._raw_currentCommand ### FIX in nullMode #}
        assert isinstance(res, GraphicsMode_API)
        return res

    def _set_graphicsMode(self, command):
        assert 0, "illegal to set %r.graphicsMode directly" % self

    graphicsMode = property( _get_graphicsMode, _set_graphicsMode)

    # mode (only used by old code; in theory, no longer needed as of 071011)
    
    def _get_mode(self):
        """
        Old code is trying to get self.mode,
        which it might want for either the Command API (self.currentCommand)
        or GraphicsMode API (self.graphicsMode). We don't know which it wants.
        (TODO, if worthwhile: deduce which, print a map of code line vs which one of these to change it to.)

        This can only be supported if the currentCommand is also old, so that
        it handles both APIs.
        Print a warning if not (or assert 0?), and return the currentCommand in either case
        (but don't wrap it with an API enforcer).
        """
        # Note: when we think there are not many uses of this left,
        # we'll make every use print_compact_stack to aid in finding the rest
        # and replacing them with one or the other of currentCommand and graphicsMode.
        # Or we might print a once-per-line-number message when it's called... ### TODO
        #
        # hmm, this is true now! [bruce 071011]
        print_compact_stack("fyi: this old code still accesses glpane.mode by that deprecated name: ")
        
        raw_currentCommand = self._raw_currentCommand
        graphicsMode = self._raw_currentCommand.graphicsMode
        if raw_currentCommand is not graphicsMode:
            print "old code warning: %r is not %r and we don't know which one %r.mode should return" % \
                  (raw_currentCommand, graphicsMode, self)
            # TODO: print_compact_stack?
        return raw_currentCommand # probably not the best guess! Who knows. Note, not wrapped with API enforcer.

    def _set_mode(self, new_mode): # TODO: a search for 'self.mode =' reveals no remaining calls, so make it an assert 0 soon
        """
        Old code is trying to set self.mode.
        Assume it wants to set _raw_currentCommand, and do that, after complaining.
        Soon, this will be illegal.
        """
        print_compact_stack("bug: old code is trying to set glpane.mode directly: ")
        self._raw_currentCommand = new_mode
        return

    mode = property(_get_mode, _set_mode)

    pass # end of class modeMixin

# end
