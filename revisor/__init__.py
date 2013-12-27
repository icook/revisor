from diff_match_patch import diff_match_patch, patch_obj
import gzip
import json
import hashlib
import StringIO


class Revision(object):
    __slots__ = ['_diffs',
                 '_diff_dicts',
                 '_json',
                 '_hash']

    def __init__(self, diffs=None):
        if diffs:
            self._diffs = diffs
        else:
            self._diffs = []
        self._json = None
        self._hash = None
        self._diff_dicts = None

    def gzip(self):
        """ Gzips the json structure of a revision """
        s = StringIO.StringIO()
        f = gzip.GzipFile(fileobj=s, mode='w')
        f.write(self.json)
        f.close()
        return s.getvalue()

    @classmethod
    def from_gzip(cls, gzip_string):
        """ Generates a revision from gzip method above """
        stream = StringIO.StringIO(gzip_string)
        fo = gzip.GzipFile(fileobj=stream, mode='r')
        inst = cls.from_dict(json.load(fo))
        fo.close()
        return inst

    @property
    def diff_dicts(self):
        """ Lazy Loaded list of dictionary representations of internal diffs
        """
        if self._diff_dicts is None:
            self._diff_dicts = []
            for d in self._diffs:
                dct = dict(d=d.diffs,
                           s1=d.start1,
                           s2=d.start2,
                           l1=d.length1,
                           l2=d.length2)
                self._diff_dicts.append(dct)
        return self._diff_dicts

    @property
    def json(self):
        """ Lazily dumps the json of the revision's data stored as a dictionary
        """
        if self._json is None:
            self._json = json.dumps(self.dict)
        return self._json

    @property
    def dict(self):
        """ Serializes all the unique attributes into a dictionary """
        return dict(d=self.diff_dicts,
                    h=self.hash())

    def hash(self, recalc=False):
        """ Lazy calculated hash of the internal diffs. Recalc will force
        a recheck even if already populated and Assert hash match"""
        if self._hash is None or recalc is True:
            hsh = hashlib.sha256(json.dumps(self.diff_dicts)).hexdigest()
            self._hash = hsh
            if recalc:
                # check matching hash
                assert hsh == self._hash
        return self._hash

    @classmethod
    def from_dict(cls, dct):
        """ Creates an instance of revision from a dictionary serialization """
        inst = cls()
        for item in dct['d']:
            p = patch_obj()
            p.diffs = item['d']
            p.start1 = item['s1']
            p.start2 = item['s2']
            p.length1 = item['l1']
            p.length2 = item['l2']
            inst._diffs.append(p)
        inst._hash = dct['h']
        return inst

    @classmethod
    def from_text(cls, text, text_old=""):
        """ A simple wrapper for the diff-patch-match method """
        return cls(diff_match_patch().patch_make(text_old, b=text))

    def apply(self, text):
        return diff_match_patch().patch_apply(self._diffs, text)


class RevisionHistory(object):
    __slots__ = ['_revisions']

    def __init__(self):
        self._revisions = []

    def gzip(self):
        s = StringIO.StringIO()
        f = gzip.GzipFile(fileobj=s, mode='w')
        # write opening json structure
        f.write('[')
        first = True
        for rev in self._revisions:
            if first:
                first = False
            else:
                f.write(',')
            f.write(rev.json)
        f.write(']')
        f.close()
        return s.getvalue()

    def add_revision(self, rev):
        try:
            next_rev = self._revisions[-1].rev + 1
        except IndexError:
            next_rev = 0
        rev.rev = next_rev
        self._revisions.append(rev)

    def rebuild(self):
        """ Reconstructs a document based on revision history """
        patch_list = []
        for rev in self._revisions:
            patch_list += rev._diffs
        return diff_match_patch().patch_apply(patch_list, "")[0]

    def check_rebuild(self, string):
        """ Rebuilds the history and checks it against a string """
        return self.rebuild() == string

    def check(self):
        for rev in self._revisions:
            rev.hash(recalc=True)

    @classmethod
    def from_gzip(cls, gzip_string):
        """ Generates a revision history from gzip method above """
        inst = cls()
        stream = StringIO.StringIO(gzip_string)
        fo = gzip.GzipFile(fileobj=stream, mode='r')
        for rec_dct in json.load(fo):
            inst._revisions.append(Revision.from_dict(rec_dct))
        fo.close()
        return inst
