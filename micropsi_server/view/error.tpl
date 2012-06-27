%include menu.tpl version = version

<div class="row-fluid">
    <p>
    <h1>Something went seriously wrong.</h1>
    </p>

    %if defined(msg):
    <div class="row-fluid">

        <div class="alert alert-error">
            {{msg}}
        </div>
    </div>
    %end

    <a class="btn btn-danger" href="/">Life goes on</a>
</div>

%rebase boilerplate title = "MicroPsi Error"
