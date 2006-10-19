# -*- coding: utf-8 -*-
"""
    pygments.lexers.templates
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Lexers for various template engines.

    :copyright: 2006 by Armin Ronacher, Georg Brandl.
    :license: GNU LGPL, see LICENSE for more details.
"""

import re
try:
    set
except NameError:
    from sets import Set as set

from pygments.lexers.web import \
     PhpLexer, HtmlLexer, XmlLexer, JavascriptLexer, CssLexer
from pygments.lexer import \
     Lexer, DelegatingLexer, RegexLexer, do_insertions, bygroups, include, using
from pygments.token import \
     Text, Comment, Operator, Keyword, Name, String, Number, Other

__all__ = ['HtmlPhpLexer', 'XmlPhpLexer', 'CssPhpLexer',
           'JavascriptPhpLexer', 'ErbLexer', 'RhtmlLexer',
           'XmlErbLexer', 'CssErbLexer', 'JavascriptErbLexer',
           'SmartyLexer', 'HtmlSmartyLexer', 'XmlSmartyLexer',
           'CssSmartyLexer', 'JavascriptSmartyLexer', 'DjangoLexer',
           'HtmlDjangoLexer', 'CssDjangoLexer', 'XmlDjangoLexer',
           'JavascriptDjangoLexer']


class ErbLexer(Lexer):
    name = 'ERB'
    aliases = ['erb']

    _block_re = re.compile(r'(<%%|%%>|<%=|<%#|<%-|<%|-%>|%>|^%[^%].*?$)', re.M)

    def __init__(self, **options):
        from pygments.lexers.agile import RubyLexer
        self.ruby_lexer = RubyLexer(**options)
        Lexer.__init__(self, **options)

    def get_tokens_unprocessed(self, text):
        """
        Since ERB doesn't allow "<%" and other tags inside of ruby
        blocks we have to use a split approach here that fails for
        that too.
        """
        tokens = self._block_re.split(text)
        tokens.reverse()
        state = idx = 0
        try:
            while True:
                # text
                if state == 0:
                    val = tokens.pop()
                    yield idx, Other, val
                    idx += len(val)
                    state = 1
                # block starts
                elif state == 1:
                    tag = tokens.pop()
                    # literals
                    if tag in ('<%%', '%%>'):
                        yield idx, Other, tag
                        idx += 3
                        state = 0
                    # comment
                    elif tag == '<%#':
                        yield idx, Comment.Preproc, tag
                        val = tokens.pop()
                        yield idx + 3, Comment, val
                        idx += 3 + len(val)
                        state = 2
                    # blocks or output
                    elif tag in ('<%', '<%=', '<%-'):
                        yield idx, Comment.Preproc, tag
                        idx += len(tag)
                        data = tokens.pop()
                        r_idx = 0
                        for r_idx, r_token, r_value in \
                            self.ruby_lexer.get_tokens_unprocessed(data):
                            yield r_idx + idx, r_token, r_value
                        idx += len(data)
                        state = 2
                    elif tag in ('%>', '-%>'):
                        yield idx, Error, tag
                        idx += len(tag)
                        state = 0
                    # % raw ruby statements
                    else:
                        yield idx, Comment.Preproc, tag[0]
                        r_idx = 0
                        for r_idx, r_token, r_value in \
                            self.ruby_lexer.get_tokens_unprocessed(tag[1:]):
                            yield idx + 1 + r_idx, r_token, r_value
                        idx += len(tag)
                        state = 0
                # block ends
                elif state == 2:
                    tag = tokens.pop()
                    if tag not in ('%>', '-%>'):
                        yield idx, Other, tag
                    else:
                        yield idx, Comment.Preproc, tag
                    idx += len(tag)
                    state = 0
        except IndexError:
            return


class SmartyLexer(RegexLexer):
    name = 'Smarty'
    aliases = ['smarty']

    flags = re.MULTILINE | re.DOTALL

    tokens = {
        # XXX: make marty delimiters customizable somehow
        'root': [
            (r'[^{]+', Other),
            (r'(\{)(\*.*?\*)(\})',
             bygroups(Comment.Preproc, Comment, Comment.Preproc)),
            (r'(\{php\})(.*?)(\{/php\})',
             bygroups(Comment.Preproc, using(PhpLexer, startinline=True),
                      Comment.Preproc)),
            (r'(\{)(/?[a-zA-Z_][a-zA-Z0-9_]*)(\s*)',
             bygroups(Comment.Preproc, Name.Function, Text), 'smarty'),
            (r'\{', Comment.Preproc, 'smarty')
        ],
        'smarty': [
            (r'\s+', Text),
            (r'\}', Comment.Preproc, '#pop'),
            (r'#[a-zA-Z_][a-zA-Z0-9_]*#', Name.Variable),
            (r'\$[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z0-9_]+)*', Name.Variable),
            (r'[~!%^&*()+=|\[\]:;,.<>/?{}@-]', Operator),
            ('(true|false|null)\b', Keyword.Constant),
            (r"[0-9](\.[0-9]*)?(eE[+-][0-9])?[flFLdD]?|"
             r"0[xX][0-9a-fA-F]+[Ll]?", Number),
            (r'"(\\\\|\\"|[^"])*"', String.Double),
            (r"'(\\\\|\\'|[^'])*'", String.Single),
            (r'[a-zA-Z_][a-zA-Z0-9_]*', Name.Attribute)
        ]
    }


class DjangoLexer(RegexLexer):
    name = 'django template'
    aliases = ['django']

    tokens = {
        'root': [
            (r'[^\{]+', Other),
            (r'\{\{', Comment.Preproc, 'var'),
            (r'(\{\%)(\s*)(comment)(\s*)(\%\})(.*?)'
             r'(\{\%)(\s*)(endcomment)(\s*)(\%\})',
             bygroups(Comment.Preproc, Text, Keyword, Text, Comment.Preproc,
                      Comment, Comment.Preproc, Text, Keyword, Text,
                      Comment.Preproc)),
            (r'(\{\%)(\s*)([a-zA-Z_][a-zA-Z0-9_]*)',
             bygroups(Comment.Preproc, Text, Keyword), 'block'),
            (r'\{', Other)
        ],
        'varnames': [
            (r'[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)*', Name.Variable),
            (r"(\|)([a-zA-Z_][a-zA-Z0-9_]*)(:'(\\\\|\\'|[^'])*')",
             bygroups(Operator, Name.Function, String.Single)),
            (r'(\|)([a-zA-Z_][a-zA-Z0-9_]*)(:"(\\\\|\\"|[^"])*")',
             bygroups(Operator, Name.Function, String.Double)),
            (r'(\|)([a-zA-Z_][a-zA-Z0-9_]*)',
             bygroups(Operator, Name.Function))
        ],
        'var': [
            (r'\s+', Text),
            include('varnames'),
            (r'\}\}', Comment.Preproc, '#pop')
        ],
        'block': [
            (r'\s+', Text),
            (r'(in|as|reversed|not|count|and|or|with)\b', Keyword),
            (r'"(\\\\|\\"|[^"])*"', String.Double),
            (r"'(\\\\|\\'|[^'])*'", String.Single),
            include('varnames'),
            (r'\%\}', Comment.Preproc, '#pop'),
            (r'.', Text)
        ]
    }


class RhtmlLexer(DelegatingLexer):
    name = 'RHTML'
    aliases = ['rhtml', 'html+erb', 'html+ruby']
    filenames = ['*.rhtml']

    def __init__(self, **options):
        super(RhtmlLexer, self).__init__(HtmlLexer, ErbLexer, **options)


class XmlErbLexer(DelegatingLexer):
    name = 'XML+Ruby'
    aliases = ['xml+erb', 'xml+ruby']

    def __init__(self, **options):
        super(XmlErbLexer, self).__init__(XmlLexer, ErbLexer, **options)


class CssErbLexer(DelegatingLexer):
    name = 'CSS+Ruby'
    aliases = ['css+erb', 'css+ruby']

    def __init__(self, **options):
        super(CssErbLexer, self).__init__(CssLexer, ErbLexer, **options)


class JavascriptErbLexer(DelegatingLexer):
    name = 'JavaScript+Ruby'
    aliases = ['js+erb', 'javascript+erb', 'js+ruby', 'javascript+ruby']

    def __init__(self, **options):
        super(JavascriptErbLexer, self).__init__(JavascriptLexer, ErbLexer,
                                                 **options)


class HtmlPhpLexer(DelegatingLexer):
    name = 'HTML+PHP'
    aliases = ['html+php']
    filenames = ['*.phtml']

    def __init__(self, **options):
        super(HtmlPhpLexer, self).__init__(HtmlLexer, PhpLexer, **options)


class XmlPhpLexer(DelegatingLexer):
    name = 'XML+PHP'
    aliases = ['xml+php']

    def __init__(self, **options):
        super(XmlPhpLexer, self).__init__(XmlLexer, PhpLexer, **options)


class CssPhpLexer(DelegatingLexer):
    name = 'CSS+PHP'
    aliases = ['css+php']

    def __init__(self, **options):
        super(CssPhpLexer, self).__init__(CssLexer, PhpLexer, **options)


class JavascriptPhpLexer(DelegatingLexer):
    name = 'JavaScript+PHP'
    aliases = ['js+php', 'javascript+php']

    def __init__(self, **options):
        super(JavascriptPhpLexer, self).__init__(JavascriptLexer, PhpLexer,
                                                 **options)


class HtmlSmartyLexer(DelegatingLexer):
    name = 'HTML+Smarty'
    aliases = ['html+smarty']

    def __init__(self, **options):
        super(HtmlSmartyLexer, self).__init__(HtmlLexer, SmartyLexer, **options)


class XmlSmartyLexer(DelegatingLexer):
    name = 'XML+Smarty'
    aliases = ['xml+smarty']

    def __init__(self, **options):
        super(XmlSmartyLexer, self).__init__(XmlLexer, SmartyLexer, **options)


class CssSmartyLexer(DelegatingLexer):
    name = 'CSS+Smarty'
    aliases = ['css+smarty']

    def __init__(self, **options):
        super(CssSmartyLexer, self).__init__(CssLexer, SmartyLexer, **options)


class JavascriptSmartyLexer(DelegatingLexer):
    name = 'JavaScript+Smarty'
    aliases = ['js+smarty', 'javascript+smarty']

    def __init__(self, **options):
        super(JavascriptSmartyLexer, self).__init__(JavascriptLexer, SmartyLexer,
                                                    **options)


class HtmlDjangoLexer(DelegatingLexer):
    name = 'HTML+Django'
    aliases = ['html+django']

    def __init__(self, **options):
        super(HtmlDjangoLexer, self).__init__(HtmlLexer, DjangoLexer, **options)


class XmlDjangoLexer(DelegatingLexer):
    name = 'XML+Django'
    aliases = ['xml+django']

    def __init__(self, **options):
        super(XmlDjangoLexer, self).__init__(XmlLexer, DjangoLexer, **options)


class CssDjangoLexer(DelegatingLexer):
    name = 'CSS+Django'
    aliases = ['css+django']

    def __init__(self, **options):
        super(CssDjangoLexer, self).__init__(CssLexer, DjangoLexer, **options)


class JavascriptDjangoLexer(DelegatingLexer):
    name = 'JavaScript+Django'
    aliases = ['js+django', 'javascript+django']

    def __init__(self, **options):
        super(JavascriptDjangoLexer, self).__init__(JavascriptLexer, DjangoLexer,
                                                    **options)