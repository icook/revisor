from diff_match_patch import diff_match_patch, patch_obj
import gzip
import json
import hashlib
import StringIO
import msgpack

dmp = diff_match_patch()


""" Patch the diff_match_patch to include simple serialization and
deserialization of patch objects. """
def serialize(self):
    # since the diffs return encoded strings, we need to decode them
    # since this function re-encodes them
    diffs = [(op, data.decode('utf-8')) for op, data in self.diffs]
    return msgpack.packb([dmp.diff_toDelta(diffs),
                          self.length1,
                          self.length2,
                          self.start1,
                          self.start2])
patch_obj.serialize = serialize


@classmethod
def deserialize(cls, string, original_text):
    inst = cls()
    parts = msgpack.unpackb(string, encoding='utf-8')
    inst.length1 = int(parts[1])
    inst.length2 = int(parts[2])
    inst.start1 = int(parts[3])
    inst.start2 = int(parts[4])
    print parts
    print "'" + original_text[inst.start1:inst.length1 + inst.start1] + "'"
    print len(original_text[inst.start1:inst.length1 + inst.start1])
    inst.diffs = dmp.diff_fromDelta(
        original_text[inst.start1:inst.length1 + inst.start1],
        parts[0])
    return inst
patch_obj.deserialize = deserialize


class Revision(object):
    __slots__ = ['_serial_patches',
                 'patches',
                 '_json',
                 '_hash']

    def __init__(self):
        self._hash = None
        self._serial_patches = None
        self.patches = None
        self._json = None

    # Lazy loaders
    # ========================================================================
    def serial_patches(self):
        if self._serial_patches is None:
            self._serial_patches = [p.serialize() for p in self.patches]
        return self._serial_patches

    def hash(self, recalc=False):
        if self._hash is None or recalc is True:
            hsh = hashlib.sha256(''.join(self.serial_patches())).hexdigest()
            self._hash = hsh
            if recalc:
                # check matching hash
                assert hsh == self._hash
        return self._hash

    # Creation and Export methods / Classmethods
    # ========================================================================
    @classmethod
    def from_tuple(cls, tpl, original_text):
        """ Creates an instance of revision from a serialization and the source
        text """
        inst = cls()
        inst._serial_patches = tpl[0]
        inst.patches = [patch_obj.deserialize(p, original_text)
                        for p in inst._serial_patches]
        inst._hash = tpl[1]
        return inst

    def to_tuple(self):
        """ Creates an instance of revision from a dictionary serialization """
        return self.serial_patches(), self.hash()

    @classmethod
    def from_patches(cls, patches):
        """ Utility method allowing you to create a revision from
        diff_match_patch diff objects """
        inst = cls()
        inst.patches = patches
        return inst

    @classmethod
    def from_text(cls, text, text_old=""):
        """ A simple wrapper for the diff-patch-match method """
        if isinstance(text, unicode):
            text = text.encode('unicode-escape')
        if isinstance(text_old, unicode):
            text_old = text_old.encode('unicode-escape')
        return cls.from_patches(dmp.patch_make(text_old, b=text))

    # Application methods
    # ========================================================================
    def apply(self, text):
        return dmp.patch_apply(self.patches, text)


class RevisionHistory(object):
    __slots__ = ['revisions']

    def __init__(self):
        self.revisions = []

    def rebuild(self, hash=None):
        """ Reconstructs a document based on revision history """
        patch_list = []
        for rev in self.revisions:
            patch_list += rev.patches
            if hash is not None and rev.hash == hash:
                break
        else:
            if hash is not None:
                return False
        return dmp.patch_apply(patch_list, "")[0]

    @classmethod
    def rebuild_from_tuple_lst(self, iterator, hash=None):
        text = ""
        for tpl in iterator:
            rev = Revision.from_tuple(tpl, text)
            if hash is not None and rev.hash == hash:
                break
            text = dmp.patch_apply(rev.patches, text)[0]
        else:
            if hash is not None:
                return False
        return text

    def check(self):
        """ Verifies hash integrity """
        for rev in self.revisions:
            rev.hash(recalc=True)
