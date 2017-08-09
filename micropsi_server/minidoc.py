#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
Minimalist documentation tool for Python projects, especially useful for APIs.
Works by setting it up with the project root; it will parse the projects and the individual files
on the fly and only on demand, and produce HTML from them, mostly be parsing the comments.
"""

import os
import urllib
from urllib import parse as urlparse
import time
import ast

__author__ = 'joscha'
__date__ = '23.11.12'

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
PREFIX = "minidoc/"
FILETYPES = [".py"]
EXCLUDED_DIRS = ["..", "test", "tests", "__pycache__", "bin", "lib", "include", "htmlcov", "cherrypy", "src", "share"]
EXCLUDED_FILES = ["__init__.py"]
EXCLUDE_HIDDEN = True
API_SORT = ["json_rpc_api", "netapi", "theano_netapi", "node_api"]
API_FILES = {
    "netapi": {
        "name": "NetAPI",
        "file": "micropsi_core/nodenet/netapi.py",
    },
    "theano_netapi": {
        "name": "Theano NetAPI",
        "file": "micropsi_core/nodenet/theano_engine/theano_netapi.py",
    },
    "node_api": {
        "name": "Node API",
        "file": "micropsi_core/nodenet/node.py",
    },
    "json_rpc_api": {
        "name": "JSON RPC API",
        "file": "micropsi_server/micropsi_app.py"
    },
}


ERROR = """<p style = 'error'>No documentation found at the given path</p>"""

def get_documentation(path=""):
    """
    create documentation as simple HTML, using the supplied path, which is interpreted as the project root.

    The documentation will be surroundeded with very basic HTML boilerplate, i.e. you probably do not want to
    use this method, which is a wrapper around get_documentation_body, and supply your own HTML boilerplate
    before and after that.
    """
    return """<HTML><head><title>Python Minidoc for """+path+"""</title></head>
        <body>
        """+get_documentation_body(path)+"""
        </body></html>"""

def get_navigation():
    """
    Deliver a simple list of directories and files, starting at the root path
    """
    realpath = _convert_url_to_path("")
    if os.path.isdir(realpath):
        return _get_dir_list(realpath, "&nbsp;&nbsp;")
    else:
        return ERROR


def get_api_navigation():
    result = ""
    for key in API_SORT:
        result += """<a href="/apidoc/%s">%s</a><br />""" % (key, API_FILES[key]['name'])
    return result


def get_documentation_body(path=""):
    """
    Create documentation as simple HTML, using the supplied path, which is interpreted as the project root.

    Arguments:
        path: a URL encoded path to the file or directory that needs documenting. We will try to cut anything
            above the project root, but beware of symlinks into your system, if you do not want to expose the
            file structure of your computer to the outside world.

    The documentation lacks HTML boilerplate, so you will have to bring your own.
    It is recommened to insert set the project root before starting your webserver, and setting up a route
    like this:
        import minidoc
        @route('/minidoc/<filepath:path>')
        def document(filepath):
            return template("doc", content = minidoc.get_documentation_body(filepath), title="Minidoc: "+filepath)

    where
        @route is a decorator supplied by your web framework to catch requests to /minidoc/ (the syntax may vary),
        template is a function of your web framework to embed a string with HTML boilerplate, and
        "doc" is the actual template.
    """

    realpath = _convert_url_to_path(path)

    if realpath is not None:
        if os.path.isdir(realpath):
            for i in EXCLUDED_DIRS:
                if realpath.endswith(i):
                    return ERROR
            return _get_dir_content(realpath)

        if os.path.isfile(realpath):
            file_name, file_ext = os.path.splitext(realpath)
            if not os.path.basename(file_name) in EXCLUDED_FILES and not os.path.basename(path) in EXCLUDED_FILES:
                if file_ext in FILETYPES:
                    return _get_file_content(realpath)

    return ERROR


def get_api_doc(key=None):
    """
    Create documentation of selected API files
    Methods without docstrings will be omitted.
    """
    if key is None:
        return ""

    elif key in API_FILES:
        file = API_FILES[key]['file']
        realpath = os.path.join(os.path.dirname(__file__), '..', file)
        return _get_file_content(realpath, ignore_undocumented=True)

    return ERROR


def _get_dir_content(realpath):
    """Helper function to turn a directory into HTML"""

    result = """<h2>%s %s/</h2>
     <div class="alert alert-info">
     <div style = "details">path: %s</div>
     <div style = "details">created: %s, last modified: %s</div></div>""" %(
        "Package:" if os.path.exists(os.path.join(realpath, "__init__.py")) else "Directory:",
        os.path.basename(realpath),
        urlparse.unquote(_convert_path_to_url(realpath)),
        time.ctime(os.path.getmtime(realpath)),
        time.ctime(os.path.getctime(realpath))
    )

    result += """<div style = "box">"""
    result += _get_dir_list(realpath)
    result += "</div>"

    return result

def _get_dir_list(realpath, indent = "&nbsp;"*4):
    """Helper function to generate an unadorned directory view"""

    result = ""
    for pathname, dirnames, filenames in os.walk(realpath):
        # prune recurse directories
        for x in EXCLUDED_DIRS:
            if x in dirnames:
                dirnames.remove(x)
        if EXCLUDE_HIDDEN:
            for x in dirnames.copy():
                if x.startswith('.'):
                    dirnames.remove(x)
        dir = os.path.basename(pathname)
        if dir not in EXCLUDED_DIRS and not (EXCLUDE_HIDDEN and dir.startswith(".")):
            url = _convert_path_to_url(pathname)
            if url:
                result += '%s<a href="/%s%s">%s/</a><br />\n' % (indent * url.count("/"), PREFIX, url, dir)

                for filename in filenames:
                    if filename not in EXCLUDED_FILES and not (EXCLUDE_HIDDEN and filename.startswith(".")):
                        file_name, file_ext = os.path.splitext(filename)
                        if not file_name in EXCLUDED_FILES and file_ext in FILETYPES:
                            url = _convert_path_to_url(os.path.join(pathname, filename))
                            result += '%s<b><a href="/%s%s">%s</a></b><br />\n' % (indent * url.count("/"), PREFIX, url, filename)
    return result

def _get_file_content(realpath, ignore_undocumented=False):
    """Helper function to turn a file into HTML"""

    result = """<h2>Module: %s</h2>
       <div class="alert alert-info">
       <div style = "details">path: %s</div>
       <div style = "details">created: %s, last modified: %s</div></div>""" %(
          os.path.basename(realpath),
          urlparse.unquote(_convert_path_to_url(realpath)),
          time.ctime(os.path.getmtime(realpath)),
          time.ctime(os.path.getctime(realpath))
    )
    with open(realpath) as sourcefile:
        code = sourcefile.readlines()
        abstract_syntax_tree = ast.parse(''.join(code))
        description = ast.get_docstring(abstract_syntax_tree)
        if description:
            result += "<h3>Summary:</h3> <div style = 'summary'>%s</div>" % _convert_str_to_html(description)
        visitor = DocVisitor()
        visitor.visit(abstract_syntax_tree)
        parsed_code = visitor.get_doc()
        entries = [ parsed_code[key] for key in sorted(parsed_code.keys())]
        for entry in entries:
            if ignore_undocumented is False or entry.get("description"):
                begin, end = entry.get("lines")
                result += '<hr /><div><pre>' + "".join(code[begin:end]).rstrip().rstrip(":") +"</pre>"
                result += _convert_str_to_html(entry.get("description"))+"</div>"

    return result

def _convert_path_to_url(path):
    """Helper function to get a url from an absolute path"""

    project_normalized = os.path.abspath(PROJECT_ROOT)
    path_normalized = os.path.abspath(path)
    if not path_normalized.startswith(project_normalized):
        return None

    path_tail = path_normalized[len(project_normalized):]

    folders=[]
    while True:
        path_tail, folder=os.path.split(path_tail)
        if folder:
            if folder in EXCLUDED_DIRS or (EXCLUDE_HIDDEN and folder.startswith(".")):
                return None
            folders.append(urlparse.quote_plus(folder))
        else:
            if path_tail:
                folders.append(urlparse.quote_plus(path_tail))
            break
    folders.reverse()

    return "/".join(folders[1:])

def _convert_url_to_path(url):
    """Helper function to turn a url into an absolute path"""

    decoded_path = urlparse.unquote(url)
    segments = [s.strip() for s in decoded_path.split("/")]
    for i in EXCLUDED_DIRS:
        if i in segments:
            return None
    if EXCLUDE_HIDDEN:
        for i in segments:
            if i.startswith('.'):
                return None

    return os.path.join(PROJECT_ROOT, *segments)

def _convert_str_to_html(string):
    """Helper function to insert <br> at line endings etc."""
    if not string: return ""
    lines = string.splitlines()
    for index, line in enumerate(lines):
        for char in line:
            if char == '\t':
                lines[index] = line.replace(char, "&nbsp;&nbsp;&nbsp;&nbsp;", 1)
            elif char == " ":
                lines[index] = line.replace(char, "&nbsp;")
            else:
                break
    return "<br />".join(lines)


class DocVisitor(ast.NodeVisitor):
    """Visits python file AST to grab docstrings."""

    def __init__(self, *args):
        ast.NodeVisitor.__init__(self, *args)
        self._docs = {}

    def recurse(self, node):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
            if not (node.name.startswith("_") and not node.name.startswith("__")): # exclude private but not builtin
                startline = node.lineno - 1
                if hasattr(node, "body") and len(node.body):
                    firstchild = node.body[0]
                    endline = node.body[0].lineno - 1

                    if isinstance(firstchild, ast.Expr): # docstring
                        try:
                            endline -= firstchild.value.s.count('\n')
                        except AttributeError:
                            pass
                else:
                    endline = startline + 1
                self._docs[node.lineno] = {
                    "lines": (startline, max(startline+1, endline)),
                    "description": ast.get_docstring(node)
                    }
        ast.NodeVisitor.generic_visit(self, node)

    def get_doc(self):
        return self._docs

    def generic_visit(self, node):
        ast.NodeVisitor.generic_visit(self, node)

    def visit_ClassDef(self, node):
        """ Visits class definitions, grab docstrings."""
        self.recurse(node)

    def visit_FunctionDef(self, node):
        """returns docstrings associated to functions"""
        self.recurse(node)

