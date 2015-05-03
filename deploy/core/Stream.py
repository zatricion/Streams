from SystemParameters import DEFAULT_STREAM_SIZE, DEFAULT_BUFFER_SIZE_FOR_STREAM

""" This module contains the Stream class which is
is also described in external documentation.

"""
class Stream(object):
    """
    A stream is a sequence of values. Objects can:
    (1) Append values to a stream; a stream cannot
    be modified in any other way.
    (2) Read a stream.
    (3) Subscribe to be notified when a
    value is added to a stream.

    WRITING A STREAM
    An object can add elements to a stream s by calling
    s.append(value) or s.extend(value_list); these
    operations are similar to operations on lists.

    Associated with a stream s is:
    (1) a list, s.recent. 
    (2) an index s.end into s.recent, where the slice
    s.recent[:s.end] contains the most recent values
    of stream s, and the slice s.recent[s.end:] is
    padded with pad values (either 0 or 0.0).
    (3) an index s.offset into stream s where
          recent[i] = stream[i + offset]
             for 0 <= i < s.end
    For example, if the stream s consists of range(950),
    i.e., 0, 1, .., 949, and s.offset is 900, then
    s.recent[i] = s[900+i] for i in range(50).
    Note that the number of entries in stream s is:
    s.offset + s.end

    READING A STREAM
    An object can read a stream after it registers
    with the stream as a reader. Associated with a reader
    r of stream s is an index s.start[r] into the list recent.
    Reader r only reads the slice s.recent[s.start[r] : ]
    of the list recent. Reader r informs stream s that it no
    longer needs to read values in the list recent with indices
    less than j by calling s.set_start(r, j) which causes
    s.start[r] to be set to j.

    SUBSCRIBING TO A STREAM
    An agent r subscribes to a stream s by executing s.call(r).
    When stream s is modified, s informs r that the stream
    has been modified by calling r.signal(s).

    Parameters
    ----------
    name: str (optional)
          name of the stream. Though the name is optional
          we recommend that you use a name because it helps
          with debugging.
    
    Attributes
    ----------
    recent: list
          A list of the most recent values of the stream.
    end:   index into the list recent.
          s.recent[:s.end] contains the s.end most recent
          values of stream s.
          s.recent[s.end:] contains padded values.
    offset: index into the stream.
          For a stream s:
          s.recent[i] = s[i + offset] for i in range(s.end)
    start: dict of readers.
             key = reader
             value = start index of the reader
             Reader r can read the slide recent[start[r] : ]
    signal_set: the set of objects to be notified when an
             element is added to the stream.
    _buffer_size: nonnegative integer
            Used to manage the recent list.
    _begin: index into the list recent
            recent[_begin:] is being read by some reader.
            recent[:_begin] is not being accessed by any object;
            therefore recent[:_begin] can be safely deleted.

    """
    def __init__(self, name="No Name", proc_name="Unkown Process"):
        self.name = name
        self.proc_name = proc_name
        # Create the list recent and the parameters
        # associated with garbage collecting
        # elements in the list.
        self.recent = self.create_recent(DEFAULT_STREAM_SIZE)
        self._buffer_size = DEFAULT_BUFFER_SIZE_FOR_STREAM
        self._begin = 0
        # Initially, the stream has no entries, and so
        # offset and end are both 0.
        self.offset = 0
        self.end = 0
        # Initially the stream has no readers.
        self.start = dict()
        # Initially the stream has no subscribers.
        self.signal_set = set()
        # Initially the stream is open
        self.closed = False

    def reader(self, reader, start=0):
        """
        Register a reader.
        """
        # The newly registered reader starts reading list recent
        # from index start, i.e., reads the slice recent[start:s.end]
        self.start[reader] = start

    def delete_reader(self, reader):
        """
        Delete this reader from this stream.
        """
        if reader in start: del start[reader]

    def call(self, agent):
        """
        Register a subscriber for this stream.
        """
        self.signal_set.add(agent)
    
    def signal_subscribers(self):
        """
        Signal all subscribers to this stream.
        """
        for a in self.signal_set: a.signal(stream=self.name)

    def delete_caller(self, agent):
        """
        Delete a subscriber for this stream.
        """
        self.signal_set.discard(agent)
    
    def close(self):
        """
        Close this stream."
        """
        if self.closed:
            return
        print "Stream " + self.name + " in " + self.proc_name + " closed"
        self.closed = True
        for a in self.signal_set: a.signal()
        
    def append(self, value):
        """
        Append a single value to the end of the
        stream.
        """
        if self.closed:
            raise Exception("Cannot write to a closed stream.")

        self.recent[self.end] = value
        self.end += 1
        # Inform subscribers that the stream has been
        # modified.
        self.signal_subscribers()
                            
        # Manage the list recent.
        # Set up a new version of the list
        # (if necessary) to prevent the list
        # from getting too long. 
        self.set_up_new_recent()


    def extend(self, value_list):
        """
        Extend the stream by the list of values.
        """
        if self.closed:
            raise Exception("Cannot write to a closed stream.")
        
        if len(value_list) == 0:
            return

        self.new_end = self.end + len(value_list)
        self.recent[self.end : self.new_end] = value_list
        self.end = self.new_end
        # Inform subscribers that the stream has been
        # modified.
        self.signal_subscribers()

        # Manage the list recent as for the append() method.
        self.set_up_new_recent()
                 
    def set_start(self, reader, start):
        """ The reader tells the stream that it is only accessing
        elements of recent with index start or higher.

        """
        self.start[reader] = start

    def set_up_new_recent(self):
        """
        Implement a form of garbage collection for streams
        by updating the list recent to delete elements of
        the list that are not accessed by any reader.
        """
        self._begin = 0 if self.start == {} else min(self.start.itervalues())
        if self.end < len(self.recent) - self._buffer_size: return
        self.new_recent = self.create_recent(
            len(self.recent) * (1 if self._begin > self._buffer_size else 2))
        self.new_recent[:self.end - self._begin] = \
          self.recent[self._begin : self.end]
        self.recent, self.new_recent = self.new_recent, self.recent
        del self.new_recent
        self.offset += self._begin
        for key in self.start.iterkeys():
            self.start[key] -=  self._begin
        self.end -= self._begin
        self._begin = 0

    def create_recent(self, size): return [0] * size
        
