# pyop

Anki extension to run user supplied python as a background operation with access to selected card (`cid`), note (`nid`), deck (`did`) and collection (`col`) through `pyop` module.

## Use case

One example would be a quick script to generate notes from a website using `BeautifulSoup` with a specific deck as destination for the notes.

Example, `<addon>/user_files/parse.py`:

```py
import re, tempfile, shutil
from urllib import request
from bs4 import BeautifulSoup
from pyop import col, did

URLS = [
  ("https://something.net/subdir/one/", 10),
  ...
]

model = col.models.by_name('Flexible Cloze 2 (min)')
opener = request.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')]
request.install_opener(opener)
tmpdir = tempfile.mkdtemp()

for (url, n) in URLS:
    m = re.match(rf'^.*?/subdir/(.*?)/.*', url)
    title = m.group(1)
    html = rf"<h1>{m.group(1).replace('-', '').capitalize()}</h1>"
    cloze = 1
    for i in range(1, n+1):
        req = request.urlopen(rf'{url}{i}')
        rhtml = req.read().decode("utf8")
        req.close()
        soup = BeautifulSoup(rhtml, 'html.parser')
        imgel = soup.select_one('#something-image')
        tmpfile =  rf"{tmpdir}/{title}-{i}.{(imgel['src'].rsplit('.', 1))[1]}"
        request.urlretrieve(rf'https://something.net{imgel["src"]}', tmpfile)
        img = col.media.add_file(tmpfile)
        html += rf'<hr><img src="{img}">'

        q = []
        a = []
        for itm in soup.select('.something-question'):
            q.append(itm.get_text())
        for itm in soup.select('.something-answer'):
            a.append(itm.get_text())
        for x in range (len(q)):
            html += rf'<br><br>{q[x]}<br>' + '{{c' + rf'{cloze}::{a[x]}' + '}}'
        cloze += 1

    note = col.new_note(model)
    note['Text'] = html
    col.add_note(note, did)

shutil.rmtree(tmpdir)
```

## Use

The addon adds two context and top bar menu options:

- `Pyop: Select file`: select which file/python module to run. In the module importing `pyop` will give access to the current selection in the form of `col`, `did`, `nid` and `cid`. Depending on how the addon is launched (table context menu or main window menu etc.) some of the values may be `None`.
- `Pyop: Run <file name>`: will load the file/module from disk (and hence run the code). The module is loaded from disk every time (to avoid having to restart Anki when debugging the script).

It may be worth running Anki from the console so that you have access to standard output while testing your scripts. Storage of the user scripts can be anywhere but `<addon>/user_files` is recommended.
