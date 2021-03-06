# python3
# coding=<UTF-8>

from lxml import etree

from ..params_container import Container
from ..target import Target
from ..exceptions import EmptyPageException

__author__ = 'maria-terekhina'
__doc__ = \
'''
JuKuu: Japanese-Chinese Subcorpus
=================================

API for Japanese-Chinese subcorpus of JuKuu corpus (http://www.jukuu.com/)

**Search Parameters**

query: str or list([str])
    query or queries (currently only exact search by word or phrase is available)
n_results: int, default 100
    number of results wanted (100 by default, also 100 is the maximum possible quantity for this corpus)
kwic: bool, default True
    kwic format (True) or a sentence (False)
query_language: str
    language of the 'query'

Example
-------

.. code-block:: python

    corp = lingcorpora.Corpus('jpn_zho')
    results = corp.search('錬', n_results = 10, query_language='jpn')
    for result in results:
        for i,target in enumerate(result):
            print(i+1,target.text)

.. parsed-literal::

    "錬": 100%|██████████| 10/10 [00:04<00:00,  2.08docs/s]

    1  粗銅を精錬して純銅にする 
    2  鉄鉱石を溶かして精錬する 
    3  鉱石から金属を製錬する 
    4  百戦錬磨を経てきた軍隊 
    5  百戦錬磨の老戦士 
    6  このうえさらに体の鍛錬を必要とする 
    7  心身を修錬する 
    8  てつを製錬する 
    9  百戦錬磨を経る 
    10  金属を製錬する 

'''

TEST_DATA = {'test_single_query': {'query': 'のも', 'query_language': 'jpn'},
             'test_multi_query': {'query': ['のも', 'ある'], 'query_language': 'jpn'}
             }


class PageParser(Container):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__seed = ''
        self.__temp = 'temptree.xml'
        self.__xpath = ".//*[@class='e'] | .//*[@class='c']"
        self.__dpp = 100
        self.__stop_flag = False
        self.__c_page = 0
        self.__targets_seen = 0

        self.__dom = 'http://www.jukuu.com/display-'
        self.__post = '%s-%d.html'

        if self.query_language is None:
            raise ValueError('Please specify "query_language" parameter')

    def __get_ana(self, word):
        _ana = dict()
        for ana in word.findall('ana'):
            # iter over values of current ana of target (lex, sem, m, ...)
            for ana_type in ana.findall('el'):
                _ana[ana_type.attrib['name']] = [x.text for x in ana_type.findall('el-group/el-atom')]
        return _ana

    def __parse_docs(self, docs_tree, analyses=True):
        """
        a generator over documents tree
        """
        _text = str()
        _transl = str()
        _target_idxs = list()
        _ana = list()
        _lang = str()
        _meta = str()
        lq = len(self.query)

        if self.query_language is 'zho':
            original = False
        else:
            original = True

        for el in docs_tree:
            if original:
                _text = "".join(el.getchildren()[1].itertext())

                for k, sym in enumerate(_text):
                    if _text[k:k + lq] == self.query:
                        _target_idxs.append((k, k + lq))

                original = False

            else:
                _transl = "".join(el.getchildren()[1].itertext())
                if el.attrib['class'] == 'e':
                    _lang = 'zho'
                else:
                    _lang = 'jpn'
                original = True

            if _target_idxs and (_transl != str()):
                for ixs in _target_idxs:
                    yield _text, ixs, _meta, _ana, _transl, _lang
                _text = str()
                _transl = str()
                _target_idxs = list()

            else:
                continue

    def get_page(self):
        """
        return documents tree
        """
        params = (self.query,
                  self.__c_page)

        post = self.__post % (params)
        parser = etree.HTMLParser(recover=True)
        return etree.parse(self.__dom + post, parser=parser)

    def get_results(self):
        docs_tree = self.page.xpath(self.__xpath)

        if not docs_tree:
            raise EmptyPageException

        for doc in self.__parse_docs(docs_tree, analyses=self.get_analysis):
            self.__targets_seen += 1
            if self.__targets_seen <= self.n_results:
                yield Target(*doc)
            else:
                self.__stop_flag = True
                return

    def extract(self):
        """
        streamer to Query
        """

        while not self.__stop_flag:
            try:
                self.page = self.get_page()
                yield from self.get_results()

            except EmptyPageException:
                self.__stop_flag = True

            self.__c_page += 1

            if self.__c_page > 9:
                self.__stop_flag = True
                return
