%include menu.tpl
<div class="row-fluid" xmlns="http://www.w3.org/1999/html">
    <div class="span3">
        <div class="well well-small">
            <ul class="nav nav-list">
                <li class="nav-header"><i class="icon-list"></i> Navigation</li>
                {{!navi}}
            </ul>
        </div>
    </div>
    <div class="span8">
        <h4>Documentation browser</h4>
        {{!content}}
    </div>

</div>


%rebase boilerplate title = "{{title}}"
