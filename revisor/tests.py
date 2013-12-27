import unittest
import os

from revisor import Revision, RevisionHistory


asset_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../test/')


class TestBasicPatch(unittest.TestCase):

    def test_empty_hist(self):
        r = RevisionHistory()
        g = r.gzip()
        assert len(RevisionHistory.from_gzip(g)._revisions) == 0

    def test_simple_rev_gzip(self):
        text = file(asset_path + '/rev0.txt').read()
        rev = Revision.from_text(text)
        gzp = rev.gzip()
        new_rev = Revision.from_gzip(gzp)
        assert new_rev.hash() == rev.hash()
        assert new_rev.apply("") == rev.apply("")
        assert new_rev.apply("")[0] == text

    def _get_hist(self, revs=[0, 1, 2, 3]):
        last = ""
        hist = RevisionHistory()
        for f in revs:
            text = file(asset_path + '/rev' + str(f) + '.txt').read()
            rev = Revision.from_text(text, text_old=last)
            hist._revisions.append(rev)
            last = text
        return hist

    def test_hist_rebuild(self):
        hist = self._get_hist()
        final_rev = file(asset_path + '/rev3.txt').read()
        assert hist.check_rebuild(final_rev)

    def test_hist_rehash(self):
        hist = self._get_hist()
        hist.check()

    def test_many_gzip(self):
        hist = self._get_hist()
        gzp = hist.gzip()
        rh = RevisionHistory.from_gzip(gzp)
        rh.check_rebuild(hist.rebuild)
        rh.check()

if __name__ == '__main__':
    unittest.main()
