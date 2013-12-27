import os

from revisor import *

asset_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../test/')
revs=[0, 1, 2, 3]

def test_hist_gzip():
    last = ""
    hist = RevisionHistory()
    for f in revs:
        text = file(asset_path + '/rev' + str(f) + '.txt').read()
        rev = Revision.from_text(text, text_old=last)
        hist._revisions.append(rev)
        last = text

if __name__ == '__main__':
    import timeit
    print(timeit.timeit("test_hist_gzip()", setup="from __main__ import test_hist_gzip", number=100))
