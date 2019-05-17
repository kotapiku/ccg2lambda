## Setup

```
virtualenv --no-site-packages --distribute -p /Users/kotapiku/.pyenv/shims/python3 py3
source py3/bin/activate
pip install lxml simplejson pyyaml -I nltk==3.0.5
python -c "import nltk; nltk.download('wordnet')"
coqc coqlib.v
```

- easyccg, C&C parserのinstall
- depccgのinstall
```
pip install depccg requests
depccg_en download
```
- `en/parser_location.txt`を追加

## Useage
- `./en/rte_en_mp_any.sh en/sample_en.txt en/semantic_templates_en_emnlp2015.yaml`
- `./en/emnlp2015exp.sh en/semantic_templates_en_emnlp2015.yaml fracas.xml`
- `./en/eval_fracas.sh <section num>`
