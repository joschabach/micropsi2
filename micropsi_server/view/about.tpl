%include menu.tpl version = version

<div class="row-fluid">
    <p>
    <h2>About MicroPsi 2</h2>
    <h3>Version {{version}}</h3>
    </p>

    <div class="row-fluid">
        <p><strong>MicroPsi</strong> is a cognitive architecture, based on Dietrich Dörner's <em>Psi Theory</em> and additional
        concepts, as laid down in the book <em>Principles of Synthetic Intelligence</em> (OUP 2009). MicroPsi allows
        the design of agents as hierarchical spreading activation networks, and includes a Multi Agent simulation
        environment.</p>
        <p>The first version of MicroPsi had been developed between 2003 and 2009 by Joscha Bach, Ronnie Vuine,
        Matthias Füssel, David Salz, Markus Dietzsch, Colin Bauer, Daniel Küstner, Julia Böttcher. It was designed
        as a PlugIn for the Eclipse IDE and written in Java.</p>
        <p>MicroPsi 2 is a completely new implementation, this time in Python. To reduce maintenance and support cost
        for different platforms, and to allow for easier access, MicroPsi 2 has been implemented as a web application.
        </p>
        <h3>License</h3>
        MicroPsi 2 is under MIT license.
    </div>

    <h2>Contact</h2>
    <ul>
        <li><a href="http://micropsi.com">micropsi.com</a></li>
        <li><a href="http://micropsi-industries.com">micropsi-industries.com</a></li>
        <li>#micropsi on freenode</li>
    </ul>
</div>


%rebase boilerplate title = "About MicroPsi 2"
