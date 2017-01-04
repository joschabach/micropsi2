%include("menu.tpl", version=version)

<div class="row-fluid">
    <p>
    <h2>MicroPsi Runtime</h2>
    <h3>Version {{version}}</h3>
    </p>

    <div class="row-fluid">
    <p>
       The MicroPsi Runtime is the execution environment for MicroPsi agents. It is distributed with the micropsi industries BDK, available from <a href="http://micropsi-industries.com/download">micropsi-industries.com/download</a> and documented at <a href="http://micropsi-industries.com/documentation/toc">micropsi-industries.com/documentation/toc</a>.<br/><br/>

       An MIT-licensed stand-alone version of the Runtime is available from <a href="https://github.com/joschabach/micropsi2">github.com/joschabach/micropsi2</a>.<br/><br/>
       The MicroPsi Runtime is built on Python 3, <a href="https://github.com/Theano/Theano">Theano</a>, and <a href="https://github.com/defnull/bottle">Bottle</a>.<br/><br/>
       © micropsi industries GmbH 2014-2017
    </p>
    </div>
</div>


%rebase("boilerplate.tpl", title="About MicroPsi 2")
