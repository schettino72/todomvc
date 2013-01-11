# collect and present stats of TodoMVC implementations
# this should be run with `doit` http://python-doit.sourceforge.net
# LOC count by http://cloc.sourceforge.net

# TODO
# =========
#
# * YUI lib not included
# * ember.js lib not minimized
# * closure use template with extension .soy (not counted)
# * ignoring gwt (too strange)
# * cloc does not support coffeescript. counting compiled JS
#


import os, os.path, fnmatch, subprocess
import json

from doit.tools import result_dep

DOIT_CONFIG = {'verbosity': 2,
               'reporter': 'executed-only',
               }


CLOC = "cloc --quiet --by-file --csv "
PROJECTS = [
    {'name': 'vanillajs', 'basepath': 'vanilla-examples'},
    {'name': 'jquery', 'assets':['jquery', 'handlebars']},
    {'name': 'agilityjs', 'assets':['jquery']},
    {'name': 'angularjs', 'lib':'libs'},
    {'name': 'angularjs-perf', 'lib':'libs'},
    {'name': 'backbone', 'assets':['jquery', 'lodash']},
    {'name': 'closure', 'lib':'compiled.js'},
    {'name': 'dojo' },
    {'name': 'emberjs', 'lib':'libs', 'assets':['jquery', 'handlebars']},
    # TODO gwt/src  java=425, XML=46
    # {'name': 'gwt', 'basepath': 'architecture-examples'},
    {'name': 'knockback', 'compiled':'coffee', 'assets':['jquery']},
    {'name': 'knockoutjs', 'assets':['director']},
    {'name': 'spine', 'compiled':'coffee', 'assets':['jquery', 'handlebars']},
    {'name': 'yui', },
    ]



def path_iter(base_path, wildcard="*"):
    """recursivilly find file names than match wildcard"""
    for root, dirnames, filenames in os.walk(base_path):
        for filename in fnmatch.filter(filenames, wildcard):
            yield os.path.join(root, filename)


def cloc(js_file):
    """execute a cloc command and return values as dict
    should get only one file at a time
    """
    # execute cloc
    cmd = CLOC + js_file
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
    result_str = process.communicate()[0]

    # process CSV result
    lines = result_str.splitlines()
    # first line is empty !
    if not lines[0]:
        lines.pop(0)
    assert 2 == len(lines), "use CLOC on only one file at a time" + str(lines)
    # check CSV file is what we expect
    columns = 'language,filename,blank,comment,code'
    assert lines[0].startswith(columns), lines[0]
    return dict(i for i in zip(columns.split(','), lines[1].split(',')))


def folder_bytes(path):
    """calculate the number of bytes from all files (recursive) in a folder"""
    if not os.path.exists(path):
        return {'lib': '0'}
    cmd = "cat `find %s` | wc --bytes" % path
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
    result_str = process.communicate()[0]
    return {'lib': "%.1f" % (int(result_str)/1024.0)}



class Project(object):
    """compute stats for a project"""
    def __init__(self, name, basepath='architecture-examples', lib='lib',
                 compiled='', assets=None):
        self.name = name
        self.path = os.path.join(basepath, self.name)
        # path containing libs (wont count LOC)
        self.lib_path = lib
        self.compiled = compiled
        self.assets = assets or []


    def js_stats(self, cloc_files):
        """sum up LOC for individual js files
        @param cloc_files list of output from cloc()
        """
        total = {'code':0, 'comment':0, 'blank':0}
        files = []
        for res in cloc_files:
            file_info = res.copy()
            # remove project path from filename
            file_info['filename'] = res['filename'][len(self.path):]
            files.append(file_info)
            for key in total.keys():
                total[key] += int(res[key])
        return {'total': total, 'files': files}


    ## Task generators:

    def gen_cloc_js(self):
        """count LOC in js files"""
        group_name = 'cloc-' + self.name
        js_path = os.path.join(self.path, 'js')
        lib_path = os.path.join(js_path, self.lib_path)
        # one task for each file
        for js_file in path_iter(js_path, "*.js"):
            if js_file.startswith(lib_path):
                continue
            yield {
                'basename': group_name,
                'name': js_file,
                'actions': [(cloc, [js_file])],
                'file_dep': [js_file],
                }
        # one task for summing up
        yield {
            'basename': 'js_loc',
            'name': self.name,
            'actions': [self.js_stats],
            'getargs': {'cloc_files': (group_name, None)},
            'uptodate': [result_dep(group_name)],
            }

    def gen_lib_size(self):
        lib_path = os.path.join(self.path, 'js', self.lib_path)
        yield {
            'basename': 'lib_size',
            'name': self.name,
            'actions': [(folder_bytes, [lib_path])],
            }


    def gen_cloc_html(self):
        """count LOC of index.html"""
        index_html = os.path.join(self.path, 'index.html')
        yield {
            'basename': 'html_loc',
            'name': self.name,
            'actions': [(cloc, [index_html])],
            'file_dep': [index_html]
            }

    def gen_result(self):
        def merge_results(js_loc, lib_size, html_loc):
            """merge all results in a single dict"""
            results = {
                'name': self.name,
                'compiled': self.compiled,
                'assets': self.assets}
            results['total'] = js_loc['total']
            results['files'] = js_loc['files']
            results.update(lib_size)
            results['html'] = {
                'code': int(html_loc['code']),
                'blank': int(html_loc['blank']),
                'comment': int(html_loc['comment']),
                }
            return results

        yield {
            'basename': 'result',
            'name': self.name,
            'actions': [merge_results],
            'getargs': {'js_loc': ('js_loc:' + self.name, None),
                        'html_loc': ('html_loc:' + self.name, None),
                        'lib_size': ('lib_size:' + self.name, None),
                        }
            }




def task_all():
    for proj_opt in PROJECTS:
        proj = Project(**proj_opt)
        yield proj.gen_cloc_js()
        yield proj.gen_lib_size()
        yield proj.gen_cloc_html()
        yield proj.gen_result()


def task_report():
    target = 'stats-data.js'
    def export(results):
        with open(target, 'w') as fp:
            fp.write('// this file is auto-generated, check dodo.py\n')
            fp.write('var STATS_DATA = ')
            fp.write(json.dumps(results, indent=2))
            fp.write(';')
    return {
        'actions': [export],
        'getargs': {'results': ('result', None)},
        'targets': [target],
        'uptodate': [result_dep('result')]
        }

# graph all results

