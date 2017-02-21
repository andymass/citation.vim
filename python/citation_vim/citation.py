# -*- coding: utf-8 -*-

import os.path
import string
import sys
import pickle

class Citation(object):

    @staticmethod
    def connect():
        """
        Loads variables from vimscript and returns the source array.
        Prints errors from python to appear in the vim console.
        """

        try:
            import vim
            script_path = os.path.join(vim.eval('s:script_path'), '../../../python')
            sys.path.insert(0, script_path)
            from citation_vim.utils import raiseError

            context = Context()
            context.mode = vim.eval("g:citation_vim_mode")
            if context.mode == "bibtex":
                try:
                    file = vim.eval("g:citation_vim_bibtex_file")
                    context.bibtex_file  = os.path.expanduser(file)
                except:
                    raiseError(u"global variable 'g:citation_vim_bibtex_file' is not set")
            elif context.mode == "zotero":
                try:
                    file = vim.eval("g:citation_vim_zotero_path")
                    context.zotero_path = os.path.expanduser(file)
                except:
                    raiseError(u"global variable 'g:citation_vim_zotero_path' is not set")
            else:
                raiseError(u"global variable 'g:citation_vim_mode' must be set to 'zotero' or 'bibtex'")

            try:
                context.cache_path = os.path.expanduser(vim.eval("g:citation_vim_cache_path"))
            except:
                raiseError(u"global variable 'g:citation_vim_cache_path' is not set")

            context.collection   = vim.eval("g:citation_vim_collection")
            context.key_format   = vim.eval("g:citation_vim_key_format")
            context.desc_format  = vim.eval("g:citation_vim_description_format")
            context.desc_fields  = vim.eval("g:citation_vim_description_fields")
            context.wrap_chars   = vim.eval("g:citation_vim_source_wrap")
            context.et_al_limit  = vim.eval("g:citation_vim_et_al_limit")
            context.zotero_version = int(vim.eval("g:citation_vim_zotero_version"))
            context.source       = vim.eval("a:source")
            context.source_field = vim.eval("a:field")

            context.cache = True
            searchkeys_string = vim.eval("l:searchkeys")
            if len(searchkeys_string) > 0:
                context.cache = False
                context.searchkeys = searchkeys_string.split()
            else:
                context.searchkeys = []

            builder = Builder(context)
            return builder.build_source()

        except:
            import traceback
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            print("Citation.vim error:\n" + "".join(line for line in lines))

class Context(object):
    'empty context class'

class Builder(object):

    def __init__(self, context):
        self.context = context
        self.cache_file = os.path.join(self.context.cache_path, u"citation_vim_cache")
        self.cache = context.cache

    def build_source(self):
        """
        Returns source array.
        """
        if self.context.source == 'citation_collection':
            return self.get_collections()

        output = []
        for item in self.get_items():
            if self.context.collection == "" or self.context.collection in item.collections:
                description = self.describe(item)
                output.append([getattr(item, self.context.source_field),
                               description,
                               item.file,
                               item.combined,
                ])
        return output

    def get_collections(self):
        """
        Returns an array of collections.
        """
        output = [["<all>",""]]
        collections = {}
        for item in self.get_items():
            for col in item.collections:
                if not col in collections:
                    output.append([col, col])
                    collections[col] = col
        return output

    def get_items(self):
        """
        Returns items cache or runs parser and 
        creates cache
        """
        if self.cache and self.is_cached(): 
            return self.read_cache()

        parser = self.get_parser()
        items = parser.load()
        if self.cache:
            self.write_cache(items)
        return items

    def get_parser(self):
        """
        Returns a bibtex or zotero parser.
        """
        if self.context.mode == "bibtex":
            from citation_vim.bibtex.parser import bibtexParser
            parser = bibtexParser(self.context)
        elif self.context.mode == "zotero":
            from citation_vim.zotero.parser import zoteroParser
            parser = zoteroParser(self.context)
        else:
            raiseError(u"g:citation_vim_mode must be either 'zotero' or 'bibtex'")
        return parser

    def read_cache(self):
        """
        Returns items from the cache file.
        """
        try:
            with open(self.cache_file, 'rb') as in_file:
                return pickle.load(in_file)
        except Exception as e:
            raiseError(u"citation.read_cache(): %s" % e)

    def write_cache(self, items):
        """
        Writes the cache file.
        """
        try:
            with open(self.cache_file, 'wb') as out_file:
                pickle.dump(items, out_file)
        except Exception as e:
            raiseError(u"citation.write_cache(): %s" % e)

    def is_cached(self):
        """
        Returns boolean based on cache and target file dates
        """
        from citation_vim.utils import is_current
        if self.context.mode == 'bibtex':
            file_path = self.context.bibtex_file
        elif self.context.mode == 'zotero':
            zotero_database = os.path.join(self.context.zotero_path, u"zotero.sqlite")
            file_path = zotero_database
        return is_current(file_path, self.cache_file)

    def describe(self, item):
        """
        Returns visible text descriptions for unite, from user selected fields.
        """
        wrap = self.context.wrap_chars
        source_field = self.context.source_field
        desc_fields = self.context.desc_fields
        desc_strings = []
        source_string = u""

        for desc_field in desc_fields:
            try:
                getattr(item, desc_field)
            except AttributeError:
                raiseError('"{}" in g:citation_vim_description_fields.'.format(desc_field))
            desc_strings.append(getattr(item, desc_field))

        # Insert the source field if not present in the description.
        # Put brackets around it wherever it is.
        if source_field in desc_fields:
            source_index = desc_fields.index(source_field)
            desc_strings[source_index] = u'%s%s%s' % (wrap[0], desc_strings[source_index], wrap[1])
        else:
            if not source_field in ["combined","file"]:
                source_string = u'%s%s%s' % (wrap[0], getattr(item, source_field), wrap[1])

        return self.context.desc_format.format(*desc_strings) + source_string
