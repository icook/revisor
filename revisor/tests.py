import unittest
import os
import codecs

from revisor import Revision, RevisionHistory


asset_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../test/')


class TestRevision(unittest.TestCase):
    def test_tuple_ascii(self):
        text = codecs.open(asset_path + '/rev1.txt', 'r', 'utf-8').read()
        orig = codecs.open(asset_path + '/rev2.txt', 'r', 'utf-8').read()
        rev = Revision.from_text(text, text_old=orig)
        serial_patches, hash = rev.to_tuple()
        assert hash == rev.hash(recalc=True)

        rev3 = Revision.from_tuple((serial_patches, hash), orig)
        assert rev3.hash() == hash
        assert rev.to_tuple() == rev3.to_tuple()

    def test_tuple_unicode(self):
        # has unicode strings in it...
        text = codecs.open(asset_path + '/rev0.txt', 'r', 'utf-8').read()
        orig = codecs.open(asset_path + '/rev1.txt', 'r', 'utf-8').read()
        rev = Revision.from_text(text, text_old=orig)
        serial_patches, hash = rev.to_tuple()
        assert hash == rev.hash(recalc=True)

        rev3 = Revision.from_tuple((serial_patches, hash), orig)
        assert rev3.hash() == hash
        assert rev.to_tuple() == rev3.to_tuple()


class TestRevisionHistory(unittest.TestCase):
    def _get_hist(self, revs=[0, 1, 2, 3]):
        last = ""
        hist = RevisionHistory()
        for f in revs:
            text = file(asset_path + '/rev' + str(f) + '.txt').read()
            rev = Revision.from_text(text, text_old=last)
            hist.revisions.append(rev)
            last = text
        return hist

    def test_hist_rebuild(self):
        hist = self._get_hist()
        final_rev = file(asset_path + '/rev3.txt').read()
        assert final_rev == hist.rebuild()

    def test_rebuild_tpl(self):
        hist = self._get_hist()
        tpls = [r.to_tuple() for r in hist.revisions]
        final_rev = file(asset_path + '/rev3.txt').read()
        assert final_rev == RevisionHistory.rebuild_from_tuple_lst(tpls)


    def test_hist_rehash(self):
        hist = self._get_hist()
        hist.check()


if __name__ == '__main__':
    unittest.main()
