# python3
# coding=<UTF-8>

from collections import Iterable, deque
import warnings
from time import sleep
from tqdm import tqdm
from .result import Result
from .corpora.functions import functions


class Corpus:
    
    def __init__(self, language, verbose=True, sleep_time=1, sleep_each=5):
        """
        language: str: language alias
        verbose: bool: enable tqdm progressbar

        USELESS?
        sleep_time: int: sleeping time in seconds
        sleep_each: int: sleep after each `sleep_each` request
        """
        
        self.language = language
        self.verbose = verbose
        self.__corpus = functions[self.language] 
        self.doc = self.__corpus.__doc__
        self.gr_tags_info = self.__corpus.__dict__.get('GR_TAGS_INFO')

        self.results = list()
        self.failed = deque(list())
        
        self.__warn = \
        """
        Nothing found for query "%s".\n
        Call `retry_failed` method to retry failed queries
        """

        self.__pbar_desc = '"%s"'
        self.__type_except = 'Argument `query` must be of type <str> or iterable, got <%s>'

        if sleep_each < 1:
            raise ValueError('Argument `sleep_each` must  be >= 1')
            
        self.sleep_each = sleep_each
        self.sleep_time = sleep_time
        
    def __getattr__(self, name):
        if name.lower() == 'r':
            return self.results
        
        raise AttributeError("'Corpus' object has no attribute '%s'" % name)

    def get_gr_tags_info(self):
        print(self.gr_tags_info)

    def search(self, query, *args, **kwargs):
        """
        query: str: query
        for arguments see `params_container.Container`
        """
        
        if isinstance(query, str):
            query = [query]
        
        if not isinstance(query, Iterable):
            raise TypeError(self.__type_except % type(query))
            
        _results = list()
        
        for q in query:
            parser = self.__corpus.PageParser(q, *args, **kwargs)
            R = Result(self.language, parser.__dict__)
                
            for t in tqdm(parser.extract(),
                          total=parser.n_results,
                          unit='docs',
                          desc=self.__pbar_desc % q,
                          disable=not self.verbose
            ):
                
                R.add(t)
            
            if R:
                _results.append(R)
            
            else:
                warnings.warn(self.__warn % q)
                self.failed.append(R)
        
        self.results.extend(_results)
        
        return _results

    def retry_failed(self):
        """
        Apply `.search()` to failed queries stored in `.failed`
        """
        
        if self.failed:
            n_rounds = len(self.failed)
            retrieved = list()
            
            for _ in range(n_rounds):
                R_failed = self.failed.popleft()
                
                # List[<Result>]
                results_new = self.search(R_failed.query,
                                          **R_failed.params
                )
                
                if results_new:
                    retrieved.append(results_new[0])
            
            return retrieved
        
    def reset_failed(self):
        """
        Reset `.failed`
        """
        
        self.failed = deque(list())
