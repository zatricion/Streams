from Stream import Stream, StreamArray, StreamSeries
from SystemParameters import EPSILON
from collections import namedtuple
import copy
import functools
import time
import json
import base64
import sys
import cPickle
import datetime
import dateutil.parser as date
import itertools
import copy

inputs_tuple = namedtuple('Inputs', 'recent start end offset name')

class AgentBasic(object):
    """
    The basic Agent class from which other classes of Agents are
    derived.

    Parameters
    ----------
    in_stream_list: list of Streams
               list of input streams of this agent
    out_stream_list: list of Streams
               list of output stream of this agent
    call_list: list of Streams
               list of streams to which this agent subscribes; when
               a stream s in call_list is modified, this agent is
               called with signal(s).
    name: Str (optional)
               name of this agent


    Attributes
    ----------
    call_set: set of Streams
              The set version of call_list
    ins, outs: in_stream_list, out_stream_list
    
    """
    def __init__(self, in_stream_list, out_stream_list, call_list, name=None):
        self.ins = in_stream_list
        self.outs = out_stream_list
        self.call_set = set(call_list)
        self.name = name
        for s in self.call_set: s.call(self)
        for s in self.ins: s.reader(self)

    def signal(self, stream=None):
        """
        A stream s in call_set invokes signal(s) when
        s is modified.
        """
        # Override in derived class
        return

    def __call__(self):
        """
        Use __call__() rather than signal().
        __call__() is nicer because it hides this method
        from general users who should never need to use
        this method directly.
        """
        self.signal()

class CovertAgent(AgentBasic):
    def __init__(self, in_stream_list, out_stream_list, call_list, instance, cove):
        super(CovertAgent, self).__init__(
            in_stream_list, out_stream_list, call_list)
        self.instance = instance # unused for now
        self.cove = cove
        
    def signal(self, stream=None):
        # This rule may be changed later.
        if self.ins and all(s.closed for s in self.ins):
            for i in range(len(self.outs)): self.outs[i].close()
            return
        
        for s in self.ins:
            val = s.recent[s.start[self]:s.end]
            if not val: continue 
            self.cove.send(s.name, val)
            s.set_start(self, s.end)

class AgentParametric(AgentBasic):
    """
    The automaton or state-transition agent.

    Parameters
    ----------
    in_stream_list,  out_stream_list, call_list: as in AgentBasic
    name: Str
       Can be set externally (but not in __init__).
       Useful for debugging
    state_transition_function: function
          The function is essentially the transition function for
          an automaton, i.e., a function from inputs and state to 
          outputs and a new state.
          There are, however, a few additions to a basic state
          transition.

          The function f is from values before the transition:
             (i) inputs: a list where inputs[i] consists of
                 data about in_stream_list[i]
             (ii) a state: a tuple of values
           to values after the transition:
             (i) outputs: a list where outputs[i] is a list
                 to be appended to out_stream_list[i] after
                 the transition
             (ii) a new state (tuple) and
             (iii) starts: a list where starts[i] is the earliest
                  index that this agent reads in stream
                  in_stream_list[i] after the state transition.

           inputs[i] is the following tuple where s is the
           stream in_stream_list[i], and all values are BEFORE
           the state transition:
             (i) the list s.recent
             (ii) s.start[self], i.e., the earliest index in s.recent
                  that this agent can read before the state
                  transition
             (iii) s.end, the latest index in s.recent with a
                   stream value
             (iv) s.offset, the offset of the stream with respect
                  to s.recent. (See docs for Stream.)

          After the state-transition function is executed, the
          Stream out_stream_list[i] is extended by outputs[i], for
          all i, and for the i-th input stream s, its start-index value
          is updated by s.set_start(self, starts[i]).
                
    """

    def __init__(self, in_stream_list, out_stream_list, call_list,
                 state_transition_function, state):
        super(AgentParametric, self).__init__(
            in_stream_list, out_stream_list, call_list)
        self.f = state_transition_function
        self.state = state

    def signal(self, stream=None):
        # If there is at least one input stream
        # and all input streams are closed then close all output
        # streams.
        # This rule may be changed later.
        if self.ins and all(s.closed for s in self.ins):
            for i in range(len(self.outs)): self.outs[i].close()
            return

        # Extract inputs --- the list of tuples --- from the input streams.
        inputs = \
          [inputs_tuple(s.recent, s.start[self], s.end, s.offset, s.name) for s in self.ins]

        # Carry out the state transition and compute (i) outputs --- the extensions
        # of the output streams, (ii) the new state, and (iii) starts, 
        # the new start indexes of slices that this agent can read.
        # Outputs is a list of lists or None; it is None if the list of lists
        # is empty; or it is a list with size equal to the number of output
        # streams.
        outputs, self.state, starts = self.f(inputs, self.state)
        
        if not outputs and not starts: return 
        
        # Update start --- the slice that an agent can read --- after
        # the transition for each input stream.
        for i in range(len(self.ins)): self.ins[i].set_start(self, starts[i])

        if not outputs: return 

        # Extend each output stream i by the list outputs[i] computed by 
        # the transition function.
        for i in range(len(self.outs)): self.outs[i].extend(outputs[i])
        return

    def __call__(self):
        """
        Use __call__() rather than signal().
        """
        self.signal()


# STATE-TRANSITION FUNCTIONS FOR AGENT_PARAMETRIC
# Each state transition function operates on
# (i) inputs and (ii) state and returns:
# (i) outputs, (ii) new state and (iii) new values
# for start indices, as described in AgentParametric
# attributes.
# The general structure of a transition function for
# a single input stream is found in list_operator().
# A common structure for a transition function that
# operates on a list of inputs and produces a single
# output is found in scikit_fit().
# The generic structure has the following 6 steps:
# (1) Extract elements from the state tuple.
# (2) Extract elements from inputs, the
#     list of input stream data. Each element
#     of the list is a list, start, end, offset.
# (3) Compute the output list.
# (4) Compute new starts, i.e., update the start
#     index: the new point beyond which this
#     agent reads.
# (5) Compute the new state
# (6) return (outputs, new_state, new_starts,)

def list_operator(inputs, state):
    """
    For AgentParametric()
    Applies filter or map to a single input stream.
    Analogous to the standard Python operators of
    filter and map applied to lists.

    Parameters
    ----------
    inputs: list containing a singleton. This singleton
            value describes a stream, and consists of
            the tuple (lst, start, end, offset, name,)
    state: (list_op, element_function,)
           where list_op is an operation on a list
           such as filter or map,
           and element_function is a function on each
           element of the list.

    Returns
    -------
    outputs: list containing a single value, which is also
             a list.
             Each element of the list outputs[0] is obtained
             by applying list_op and element_function on the
             recent list of the single input stream.
             For example, if:
             list_op is filter
             and element function is lambda v: v > 0
             then the output stream is extended by the
             positive values in input_stream and only
             postive values.
             Another example: if
             list_op is map
             and element function is lambda v: v*v
             then the ouput stream is extended by the
             square of the values in the input stream.
    """
    # STEP 1
    # The state consists of the list operation (e.g. filter
    # or map) and the function that operates on each element
    # of a list.
    list_op, element_function = state['list_op'], state['element_function']
    # STEP 2
    # inputs is a singleton list. Extract the list slice
    # from inputs[0].
    lst, start, end, offset, name = inputs[0]
    # STEP 3
    # outputs is a list containing a singleton. 
    outputs = [list_op(element_function, lst[start:end])]
    # STEP 4
    # This agent now only reads elements of lst with index
    # end and higher.
    # STEP 5
    # The state of the agent never changes. So, the new state
    # is the same as the old state.
    # STEP 6
    # The agent has processed the input list up to index end.
    return (outputs, state, [end],)
    
def map_multiple_streams(inputs, state):
    """
    For AgentParametric()        
    Analogous to the standard Python operation: map multiple lists.

    The state contains a function which operates on a list; the size of
    this list is the size of the list inputs. The function is applied to
    the list of input streams to produce the output.

    Parameters
    ----------
    inputs: list containing descriptors of one or more streams.
    state: (element_function,)

    Returns
    -------
    outputs: list containing a single value which is also a list.
             This list is obtained by applying element function
             to the recent lists of all the input streams.
    """
    # STEP 1
    f = state['element_function']
    # STEP 2
    # The map operation is carried out on the same number of elements
    # in each input stream. The length of the recent list of a stream
    # w is w.end - w.start. Determine the minimum length of the recent
    # lists of all the input streams.
    length = min(w.end - w.start for w in inputs)
    # STEP 3
    outputs = [map(f, *(w.recent[w.start:w.start+length] for w in inputs))]
    # STEP 4
    # Move the start pointer for each stream forward by length.
    starts = [w.start + length for w in inputs]
    # STEP 5
    # The state doesn't change.
    # STEP 6
    return (outputs, state, starts,)

def map_two_streams_with_offset(inputs, state):
    """
    Analogous to the standard Python operation: map multiple lists.
    inputs[0] is the "now" or current stream, while
    inputs[1] is the "past" stream.
    The output is:
              f(now[j], past[j - window_size])
    for j >= window_size and
              None
    for j < window_size
    where f is the element_function.

    The state contains (i) the map element_function, f, and
    (ii) window_size.
    The map element_function operates on exactly two values.
    
    window_size must be a positive integer.

    Parameters
    ----------
    inputs: list containing descriptors of exactly two streams.
    state: (element_function, window_size)
            element_function has two arguments
            window_size: positive integer

    Returns
    -------
    outputs: list containing a single value which is also a list.
             This list is obtained by applying the element function
             to the recent lists of the two input streams.
    """
    # STEP 1
    f, window_size = [state.get(k) for k in ['element_function', 'window_size']]

    now, past = inputs
    output = []    
   

    if (now.offset + now.start < window_size):
        if now.offset + now.end < window_size:
            output.extend([None] * (now.end - now.start))
            # now.start becomes now.end; so return
            # [now.end, past.start] for starts.
            # state remains unchanged
            return ([output], state, [now.end, past.start])
        else:
            output.extend([None] * (window_size - (now.start + now.offset)))
            # Move now.start forward to window_size
            now = now._replace(start=window_size)
            # Continue to step 2.
            
    if (past.end == 0 or
        past.recent[past.end-1] is None or
        now.start >= now.end or
        now.start - window_size >= past.end):
        return ([output], state, [now.start, past.start])

    # STEP 2
    # The map operation is carried out on the same number of elements
    # in each input stream. The length of the recent list of a stream
    # w is w.end - w.start. Determine the minimum length of the recent
    # lists of all the input streams.
    now_end_for_map = min(now.end, past.end + window_size)
    length = now_end_for_map - now.start
    length = max(0, length)

    # STEP 3
    output.extend(
        map(f,
            now.recent[now.start:now.start+length],
            past.recent[past.start:past.start+length]))

    # STEP 4
    # Move the start pointer for each stream forward by length.
    # This is done by returning:
    #  [now.start+length, past.start+length] for the start tuple.

    # STEP 5
    # The state doesn't change.
    # STEP 6
    return ([output], state, [now.start+length, past.start+length],)
    
def reduce_stream(inputs, state):
    """
    For AgentParametric()        
    Analogous to the standard Python operator, reduce list.
    The state contains the reduce function and the cumulated
    value obtained so far. The output stream is the reduced
    function applied to the input stream.
    """
    # STEP 1
    f, cumulant = [state.get(k) for k in ['element_function', 'cumulant']]
    # STEP 2
    lst, start, end, offset, name = inputs[0]
    # STEP 3
    output = []
    for v in lst[start:end]:
        cumulant = v if cumulant is None else f(v, cumulant)
        output.append(cumulant)
    # STEP 4
    # This agent now only reads elements with indices beyond end
    # and so return [end] for [start].
    # STEP 5
    state = (f, cumulant,)
    # STEP 6
    return([output], state, [end],)
    
def sliding_windows(inputs, state):
    """
    For AgentParametric()        
    Applies a function f to a sliding window in the input stream.
    
    Parameters
    ----------
    inputs: singleton list containing a single descriptors of one stream.
    state: (window_size, step_size, function,)

    Returns
    -------
    outputs: list containing a single value which is also a list.
             This list is obtained by applying the function
             to an entire window in the input stream. The window
             is moved forward by step_size.

    """
    window_size, step_size, f = [state.get(k) for k in ['window_size', 
                                                        'step_size',
                                                        'function']]
    lst, start, end, offset, name = inputs[0]
    num_intervals = 1 + (end - start - window_size) / step_size
    if end < start + window_size:
        return (None, state, [start],)
    output = [None] * num_intervals
    for i in range(num_intervals):
        output[i] = f(lst[start:start+window_size])
        start += step_size
    return([output], state, [start],)


def sliding_windows_multiple_streams(inputs, state):
    """
    For AgentParametric()        
    Applies a function f to sliding windows in multiple input streams.
    All windows are of the same size and move forward with the same
    step_size, as in sliding_windows()
    
    Parameters
    ----------
    inputs: list containing descriptors for one or more streams.
    state: (window_size, step_size, function,)

    Returns
    -------
    outputs: list containing a single value which is also a list.
             This list is obtained by applying the function
             to an entire window in all the input streams. The window
             is moved forward by step_size.

    """
    window_size, step_size, f = [state.get(k) for k in ['window_size', 
                                                        'step_size',
                                                        'function']]
    lst, start, end, offset, name = map(list, zip(*inputs))
    length = min(end[i] - start[i] for i in range(n))
    if length < window_size:
        return (None, state, start,)
    num_intervals = 1 + (length - window_size) / step_size
    output = [None] * num_intervals
    for t in range(num_intervals):
        output[t] = f([lst[i][start[i]:start[i]+window_size] for i in range(n)])
        for i in range(n): start[i] += step_size
    return([output], state, start,)

def sliding_windows_stateful(inputs, state):
    """
    For AgentParametric.

    inputs is a list containing a single descriptor for a
    single stream.
    state = (window_size, initializing_function, step_function,
             output_function, cumulant, ptr)
    The cumulant is the state of the sliding window;
    the cumulant is updated each time the window moves forward by a
    single step.
    The initial value of the cumulant should be None and the first
    value is obtained by applying the initializing_function to the
    first window.
    See, for example, initializing_function_mean_and_sigma(l).

    Subsequent values of the cumulant, as the window slides forward,
    are obtained by applying the step_function. See, for example,
    step_function_mean_and_sigma(cumulant, start, window_size, l)

    The output at each step is determined by the output_function
    applied to the cumulant. See, for example,
    output_function_mean_and_sigma(cumulant, start, window_size, l)
    The initial value of ptr is 0.

    See also map_two_streams_with_offset() for AgentParametric
    for a similar algorithm.
    """
    (window_size,
    initializing_function,
    step_function,
    output_function, cumulant, ptr) = [state.get(k) for k in ['window_size', 
                                                              'initializing_function',
                                                              'step_function',
                                                              'output_function',
                                                              'cumulant',
                                                              'ptr']]
    # The initial values of cumulant and ptr should be
    # None and 0.
    lst, start, end, offset, name = inputs[0]

    output = []
    # Initialization. if offset == 0, then the stream values
    # recent values are the same. If offset is not 0, then
    # we don't use ptr.
    if offset == 0:
        # ptr is the number of None values output so far,
        # provide ptr < window_size.
        # So, ptr is the number of elements in the input
        # stream processed so far, provided ptr is less
        # than window_size
        if ptr < window_size:
            # if ptr >= end, then there are no new values to
            # process; so no change to output or start.
            # ptr changes
            if ptr >= end:
                return ([output], state, [start],)
            # if end < window_size then continue to output
            # None values, so that a total of end values
            # are output
            if end < window_size:
                output.extend([None] * (end - ptr))
                # update ptr so that it is the number of None
                # values output.
                ptr = end
                # No change to start
                state['ptr'] = ptr
                return  ([output], state, [start],)
            assert (ptr < end and window_size <= end), " bad logic for ptr, end, window_size"
            # Append enough None values so that a total of window_size
            # None values are appended to output.
            output.extend([None]*(window_size - ptr))
            ptr = window_size

            # Initialize the state for the sliding window,
            # i.e., initialize cumulant.
            cumulant = initializing_function(lst[:window_size])
            output.append(output_function(cumulant, start, window_size, lst))

    # Move window forward, one step at a time in the while loop
    while end > start + window_size:
        cumulant = step_function(cumulant, start, window_size, lst)
        output.append(output_function(cumulant, start, window_size, lst))
        start += 1
    state['cumulant'] = cumulant
    return ([output], state, [start])

def list_to_stream(inputs, state):
    """
    For AgentParametric.
    input_list is a member of the state.
    Writes one element of input_list to the output
    that feeds the output stream.

    inputs is the empty list because this agent has
    no input streams.
    input_list_ptr points to the next value to be
    output from input_list.
    """
    input_list, input_list_ptr = state['input_list'], state['input_list_ptr']
    if input_list_ptr < len(input_list):
        output = [input_list[input_list_ptr]]
        input_list_ptr += 1
        state['input_list_ptr'] = input_list_ptr
        return  ([output], state, [],)

def print_stream(inputs, state):
    """
    For AgentParametric.
    Assume inputs is a singleton containing the
    descriptor of a single stream. Prints that
    stream to stdout.
    On each line prints: stream_name, single_value.
    """

    instream = inputs[0]
    for v in instream.recent[instream.start:instream.end]:
        print instream.name, v
    # No change to state, and no output
    outputs = []
    return (outputs, state, [instream.end])

def stream_to_file(inputs, state):
    """
    For AgentParametric.
    inputs is a singleton containing the
    descriptor of a single stream.
    state = (,filename)
    Prints the single input stream to the file with
    name filename.
    On each line prints: stream_name, single_value.
    """

    instream = inputs[0]
    filename = state['filename']
    with open(filename, 'w') as f:
        for v in instream.recent[instream.start:instream.end]:
            f.write(str(v))
    # No change to state, and no output
    outputs = []
    return (outputs, state, [instream.end])

def drop_from_streams(inputs, state):
    """
    For AgentParametric()        
    Drops some number of events from the start of all input streams.
    
    Parameters
    ----------
    inputs: list containing descriptors for one or more streams.
    state: (drop_n)
           drop_n is the number of events to drop from the start of each stream
           if there is more than one stream, drop_n must be a list

    Returns
    -------
    outputs: list containing values for output streams in order
    """
    drop_n = state['drop_n']
    if not isinstance(drop_n, list):
        drop_n = [drop_n]
    outputs = []
    for i, w in enumerate(inputs):
        if (w.offset + w.start >= drop_n[i]):
            outputs.append(w.recent[w.start:w.end])
        else:
            outputs.append([])
    starts = [w.end for w in inputs]
    return (outputs, state, starts,)

###                                                           ###
# Operations on Timed Streams (streams where recents[i][0] is a #
# time that can be parsed by dateutil.parser.parse()            #
###                                                           ###

def parse_timestamps(inputs, state):
    # list of streams
    all_recents = [w.recent[w.start:w.end] for w in inputs]
    
    # parse timestamps
    for stream in all_recents:
        if len(stream > 0):
            stream = map(lambda event: [date.parse(event[0])] + event[1:], stream)
    
    return (all_recents, state, [w.end for w in inputs],)

def order_by_timestamps(inputs, state):
    # the most recent timestamp
    last_timestamp = state.get('last_timestamp', None)
    
    # whether or not to drop out of order events
    drop_out_of_order_events = state.get('drop_out_of_order_events', False)
    
    # number of events to wait when one stream has no events
    ordered_window_length = state.get('ordered_window_length', 10)
    
    all_recents = [w.recent[w.start:w.end] for w in inputs]
    min_event_count = min(len(stream) for stream in all_recents)

    if (min_event_count <= ordered_window_length):
        return ([], state, [w.start for w in inputs],)
    
    output = [sorted(stream, key=lambda x: x[0]) for stream in all_recents]
    
    if drop_out_of_order_events:
        output = filter(lambda x: x[0] > last_timestamp, output)
        
    state['last_timestamp'] = output[-1][0]
    return (output, state, [w.end for w in inputs],)

def synchronize_streams(inputs, state):
    # time delta in seconds within which two events are considered to have happened concurrently
    tolerance = state.get('tolerance', 1)
    
    # default value for empty slots in the combined stream
    default = state.get('default', None)
    
    # amount of time (in seconds) to wait when one stream has no events
    time_buffer = state.get('time_buffer', 10)
    
    # number of events to wait when one stream has no events
    event_buffer = state.get('event_buffer', 3)

    # list of streams
    all_recents = [w.recent[w.start:w.end] for w in inputs]
    
    min_event_count = min(len(stream) for stream in all_recents)

    # get streams with new events
    recents = filter(lambda x: len(x) > 0, all_recents)

    # if times are parsed, use parsed tolerance and time_buffer
    if isinstance(recents[0][0], datetime.datetime):
        tolerance = datetime.timedelta(seconds = tolerance)
        time_buffer = datetime.timedelta(seconds = time_buffer)

    min_end_time = min([stream[-1][0] for stream in recents])
    min_start_time = min([stream[0][0] for stream in recents])
            
    # when one or more streams does not have any new events and we are within the time and event buffers, do nothing
    if ((min_end_time - min_start_time) <= time_buffer) or (min_event_count <= event_buffer):
        return ([], state, [w.start for w in inputs],)

    ### new start times
    lengths = []
    for stream in recents:
        index = 0
        for ind, event in enumerate(stream):
            if (ind != 0): assert event[0] > stream[ind - 1][0], "Timestamp out of order: " + str(event[0])
            if event[0] <= min_end_time:
                index = ind + 1
        lengths.append(index)
    starts = [w.start + lengths[i] for i, w in enumerate(inputs)]
            
    # combine streams
    output = (_combine_streams_by_timestamp(recents, lengths, default, tolerance))

    return ([output], state, starts,)

def _combine_streams_by_timestamp(streams, end_indices, default, tolerance):
    # get rid of excess events
    streams = [stream[:end_indices[i]] for i, stream in enumerate(streams)]
    
    # attach a tag indicating the stream position to each event in each stream
    for ind, stream in enumerate(streams): streams[ind]  = zip(itertools.repeat(ind), stream)
    
    # flatten the streams and sort events by timestampe
    sorted_events = sorted(itertools.chain(*streams), key=lambda x: x[1][0])
    
    prev_event = None
    output = []
    # write output with defaults
    for ind, event in sorted_events:
        new_event = [event[0]] + [default for i in range(len(streams))]
        if (prev_event != None) and ((event[0] - prev_event[0]) < tolerance):
            prev_event[ind+1] = event[1:] if len(event[1:]) > 1 else event[1]
        else:
            new_event[ind+1] = event[1:] if len(event[1:]) > 1 else event[1]
            prev_event = new_event
            output.append(new_event)
    
    return output