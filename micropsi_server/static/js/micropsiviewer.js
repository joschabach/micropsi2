/**
 * Utility functions for handling the interaction of the viewer page with the MicroPsi server
 *
 * User: joscha
 * Date: 05.06.12
 */

// enable interaction with paperscript scope; the scope may register a callback handler that can be accessed from here
callbacks = new function() {
    // register a function from the paperscript scope using callbacks["functionName", <function>]
    // call the function globally with callbacks.functionName()
    // btw: you may use all global functions in the paperscript scope as well.

    this.registerCallback = function(name, foo) {
        // warning: works with a single paperscript scope only
        this[name] = foo;
    };
}


