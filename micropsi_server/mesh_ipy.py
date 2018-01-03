import os
import time
from collections import deque
from itertools import chain

from jupyter_client import KernelManager
from jupyter_client.consoleapp import JupyterConsoleApp
from jupyter_client.threaded import ThreadedKernelClient
from jupyter_core import version_info
from jupyter_core.application import JupyterApp

from micropsi_server.ansi_code_processor import AnsiCodeProcessor, NewLineAction, CarriageReturnAction, BackSpaceAction


class Buffer(list):

    highlights = []

    def add_highlight(self, type, line, fromc, toc):
        self.highlights.append((type, (line, fromc, toc)))

    def add_highlight_line(self, type, line):
        self.highlights.append((type, (line, -1, -1)))

class RedirectingKernelManager(KernelManager):
    def _launch_kernel(self, cmd, **b):
        nullfile = "/dev/null" if os.name != 'nt' else 'NUL'
        self._null = open(nullfile,"wb",0)
        b['stdout'] = self._null.fileno()
        b['stderr'] = self._null.fileno()
        return super(RedirectingKernelManager, self)._launch_kernel(cmd, **b)


class JupyterMESHApp(JupyterApp, JupyterConsoleApp):
    # don't use blocking client; we override call_handlers below
    kernel_client_class = ThreadedKernelClient
    kernel_manager_class = RedirectingKernelManager
    aliases = JupyterConsoleApp.aliases #this the way?
    flags = JupyterConsoleApp.flags

    def init_kernel_client(self):

        if self.kernel_manager is not None:
            self.kernel_client = self.kernel_manager.client()
        else:
            self.kernel_client = self.kernel_client_class(
                                session=self.session,
                                ip=self.ip,
                                transport=self.transport,
                                shell_port=self.shell_port,
                                iopub_port=self.iopub_port,
                                stdin_port=self.stdin_port,
                                hb_port=self.hb_port,
                                connection_file=self.connection_file,
                                parent=self,
            )
        self.kernel_client.shell_channel.call_handlers = self.target.on_shell_msg
        self.kernel_client.iopub_channel.call_handlers = self.target.on_iopub_msg
        #self.kernel_client.stdin_channel.call_handlers = self.target.on_stdin_msg
        self.kernel_client.hb_channel.call_handlers = self.target.on_hb_msg
        self.kernel_client.start_channels()

    def initialize(self, target, argv):
        self.target = target
        super(JupyterMESHApp, self).initialize(argv)
        JupyterConsoleApp.initialize(self, argv)

class ExclusiveHandler(object):
    """Wrapper for buffering incoming messages from a asynchronous source.
    Wraps an async message handler function and ensures a previous message will
    be completely handled before next messsage is processed. Is used to avoid
    iopub messages being printed out-of-order or even interleaved.
    """
    def __init__(self, handler):
        self.msgs = deque()
        self.handler = handler
        self.is_active = False

    def __call__(self, msg):
        self.msgs.append(msg)
        if not self.is_active:
            self.is_active = True
            while self.msgs:
                self.handler(self.msgs.popleft())
            self.is_active = False


class IPythonConnection(object):
    def __init__(self):
        self.buf = None
        self.has_connection = False

        self.pending_shell_msgs = {}
        self.pending_shell_results = {}

        self.do_highlight = True

        self.hl_handler = AnsiCodeProcessor()

        # make sure one message is handled at a time
        self.on_iopub_msg = ExclusiveHandler(self._on_iopub_msg)

        self.last_msg = None

        self.max_in = 1000
        self.prompt_in = u"In[{}]: "
        self.prompt_out = u"Out[{}]: "

    def get_buffer(self):
        return {
            "lines": self.buf,
            "highlights": self.buf.highlights
        }

    def create_outbuf(self):
        if self.buf is not None:
            return
        self.buf = Buffer()

        self.hl_handler.bold_text_enabled = True

    def append_outbuf(self, data):
        lineidx = len(self.buf)-1
        lastline = self.buf[-1]

        lines = []
        chunks = []

        for chunk in chain([lastline], self.hl_handler.split_string(data)):
            if self.hl_handler.actions:
                assert len(self.hl_handler.actions) == 1
                a = self.hl_handler.actions[0]
                if isinstance(a, NewLineAction):
                    lines.append(chunks)
                    chunks = []
                elif isinstance(a, CarriageReturnAction):
                    chunks = []
                elif isinstance(a, BackSpaceAction):
                    if chunks:
                        if len(chunks[-1]) > 1:
                            chunks[-1][1] = chunks[-1][1][:-1]
                        else:
                            chunks.pop()
            elif len(chunk) > 0:
                groups = []
                if self.do_highlight:
                    bold = self.hl_handler.bold or self.hl_handler.intensity > 0
                    color = self.hl_handler.foreground_color
                    if color and color > 16: color = None

                    if color is not None:
                        if bold and color < 8:
                            color += 8 # be bright and shiny
                        groups.append("IPyFg{}".format(color))

                    if bold:
                        groups.append("IPyBold")
                chunks.append([groups, chunk])

        lines.append(chunks)

        textlines = []
        hls = []
        for i,line in enumerate(lines):
            text = ''.join(c[1] for c in line)
            textlines.append(text)
            colend = 0
            for chunk in line:
                colstart = colend
                colend = colstart + len(chunk[1])
                for hl in chunk[0]:
                    hls.append([hl, lineidx+i, colstart, colend])

        self.buf[-1:] = textlines
        return lineidx

    def connect(self, argv):

        has_previous = self.has_connection
        if has_previous:
            # TODO: kill last kernel if we owend it?
            JupyterMESHApp.clear_instance()

        self.ip_app = JupyterMESHApp.instance()
        if has_previous:
            self.ip_app.connection_file = self.ip_app._new_connection_file()

        self.ip_app.initialize(self, argv)
        self.ip_app.start()
        self.kc = self.ip_app.kernel_client
        self.km = self.ip_app.kernel_manager
        self.has_connection = True

        reply = self.waitfor(self.kc.kernel_info())
        c = reply['content']
        lang = c['language_info']['name']
        langver = c['language_info']['version']

        banner = ["mesh-ipy: Jupyter shell for MESH"] if not has_previous else []
        try:
            ipy_version = c['ipython_version']
        except KeyError:
            ipy_version = version_info
        vdesc = '.'.join(str(i) for i in ipy_version[:3])
        if len(ipy_version) >= 4 and ipy_version[3] != '':
            vdesc += '-' + ipy_version[3]
        banner.extend([
                "Jupyter {}".format(vdesc),
                "language: {} {}".format(lang, langver),
                "",
                ])

        if has_previous:
            pos = len(self.buf)
            self.buf.append(banner)
        else:
            pos = 0
            self.buf[:0] = banner
        for i in range(len(banner)):
            self.buf.add_highlight_line('Comment', pos+i)

    def disp_status(self, status):
        pass

    def handle(self, msg_id, handler):
        self.pending_shell_msgs[msg_id] = handler

    def waitfor(self, msg_id, retval=None):
        self.handle(msg_id, self.print_handler)
        while msg_id in self.pending_shell_msgs:
            time.sleep(0.1)
        return self.pending_shell_results.pop(msg_id)

    def ignore(self, msg_id):
        self.handle(msg_id, None)

    def print_handler(self, o):
        #print("Printing msg result:"+str(o))
        return o

    def ipy_connect(self, args):
        self.create_outbuf()
        self.connect(args)

    def run(self, code):
        silent = False  # bool(args[1]) if len(args) > 1 else False
        if self.km and not self.km.is_alive():
            # Todo: communicate kernel restart
            if self.km.has_kernel:
                self.km.restart_kernel(True)
            else:
                self.km.start_kernel(**self.km._launch_args)
            return

        reply = self.waitfor(self.kc.execute(code, silent=silent))
        content = reply['content']
        payload = content.get('payload',())
        for p in payload:
            if p.get("source") == "page":
                if 'text' in p:
                    self.append_outbuf(p['text'])
                else:
                    self.append_outbuf(p['data']['text/plain'])

    def ipy_write(self, args):
        self.append_outbuf(args[0])

    def autocomplete(self, line, pos):
        reply = self.waitfor(self.kc.complete(line, pos))
        content = reply["content"]
        start = content["cursor_start"] + 1
        matches = content["matches"]
        return {
            "start": start,
            "matches": matches
        }

    def history(self, item):
        reply = self.waitfor(self.kc.history())
        content = reply["content"]

        if len(content["history"]) == 0 or abs(item) > len(content["history"]):
            return 0, 0, ""

        return content["history"][item]

    def search(self, prefix, item):
        reply = self.waitfor(self.kc.history(raw=True,
                                             output=False,
                                             hist_access_type='search',
                                             pattern="%s*" % prefix,
                                             unique=True))
        content = reply["content"]

        if len(content["history"]) == 0 or abs(item) > len(content["history"]):
            return 0, 0, ""

        return content["history"][item]

    def ipy_objinfo(self, args):
        word, level = args
        #TODO: send entire line
        reply = self.waitfor(self.kc.inspect(word, None, level))

        c = reply['content']
        if c["status"] == "error":
            l = self.append_outbuf("\nerror when inspecting {}: {}\n".format(word, c.get("ename", "")))
            if self.do_highlight:
                self.buf.add_highlight("Error", l+1, 0, -1)
            if "traceback" in c:
                self.append_outbuf('\n'.join(c['traceback'])+"\n")

        elif not c.get('found'):
            l = self.append_outbuf("\nnot found: {}\n".format(word))
            if self.do_highlight:
                self.buf.add_highlight("WarningMsg", l+1, 0, -1)
        else:
            self.append_outbuf("\n"+c['data']['text/plain']+"\n")

    def ipy_interrupt(self, args):
        self.km.interrupt_kernel()

    def ipy_terminate(self, args):
        self.km.shutdown_kernel()

    def _on_iopub_msg(self, m):
        try:
            t = m['header'].get('msg_type',None)
            c = m['content']

            if t == 'status':
                status = c['execution_state']
                self.disp_status(status)
            elif t in ['pyin', 'execute_input']:
                prompt = self.prompt_in.format(c['execution_count'])
                code = c['code'].rstrip().split('\n')
                if self.max_in and len(code) > self.max_in:
                    code = code[:self.max_in] + ['.....']
                sep = '\n'+' '*len(prompt)
                line = self.append_outbuf(u'\n{}{}\n'.format(prompt, sep.join(code)))
                self.buf.add_highlight('IPyIn', line+1, 0, len(prompt))
            elif t in ['pyout', 'execute_result']:
                no = c['execution_count']
                res = c['data']['text/plain']
                prompt = self.prompt_out.format(no)
                line = self.append_outbuf((u'{}{}\n').format(prompt, res.rstrip()))
                self.buf.add_highlight('IPyOut', line, 0, len(prompt))
            elif t in ['pyerr', 'error']:
                #TODO: this should be made language specific
                # as the amt of info in 'traceback' differs
                self.append_outbuf('\n'.join(c['traceback']) + '\n')
            elif t == 'stream':
                self.append_outbuf(c['text'])
            elif t == 'display_data':
                d = c['data']['text/plain']
                self.append_outbuf(d + '\n')
        except Exception as e:
            print("Couldn't handle iopub message %r: %s", m, str(e))

    def on_shell_msg(self, m):
        self.last_msg = m
        msg_id = m['parent_header']['msg_id']
        try:
            handler = self.pending_shell_msgs.pop(msg_id)
        except KeyError:
            print('unexpected shell msg: %r', m)
            return
        if handler is not None:
            self.pending_shell_results[msg_id] = handler(m)

    def on_hb_msg(self, time_since):
        # this gets called when heartbeat is lost
        self.disp_status("DEAD")


#c = IPythonConnection()
#c.ipy_connect(["--existing"])
#c.run("print(\"wrdlbrmpfd\")")
#c.run("print(runtime)")
#print("\n".join(c.buf))
