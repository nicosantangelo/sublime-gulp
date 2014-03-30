# Sublime Gulp

A Gulp task runner for Sublime Text. This package is a port of the awesome [sublime-grunt](https://github.com/tvooo/sublime-grunt).

Currently under development :).

## Usage

### Run Tasks
To run a task, first choose `Gulp` from the command pallete, the package will search for a gulpfile.js or gulpfile.coffee in an open folder and create a cache (`.sublime-gulp.cache`) with it (the first run might be a little slow).

The package will display all the tasks in a list. Selecting one will run it.

To show the task output the package uses the `Build Results` window. To access it go to:

`Tools -> Build Results -> Show Build Results`

You can also add a keybinding to toggle it, like this:

`{ "keys": ["{KEYS}"], "command": "show_panel", "args": { "toggle": true, "panel": "output.exec" } }`

### Kill tasks
To kill running tasks like `watch` you can pick the command `Gulp: Kill running tasks`. This might not work as expected in some systems, I'm looking for a workaround in [this branch](https://github.com/NicoSantangelo/sublime-gulp/tree/replace_exec). Any idea is welcome!

## Settings (from [sublime-grunt](https://github.com/tvooo/sublime-grunt))

The file `SublimeGulp.sublime-settings` is used for configuration.

You may override your `PATH` environment variable as follows:

````json
{
    "exec_args": {
        "path": "/bin:/usr/bin:/usr/local/bin"
    }
}
````

You can change your user settings in `Preferences -> Package Settings -> Gulp -> Settings - User`

Also, the package creates the first cache using [node](http://nodejs.org/), so for it to work you might need to add your node_modules path to NODE_PATH, for example (for Unix):

`export NODE_PATH=/usr/local/lib/node_modules`

## Shortcut Keys

This package doesn't bind any command to a keybinding, but you can add it like this:

````json
{
    "keys": ["{KEYS}"], "command": "gulp", 
    "keys": ["{KEYS}"], "command": "gulp_kill"
}
````

## Instalation

### Manual

You can clone the repo in your `/Packages` (*Preferences -> Browse Packages...*) folder and start using/hacking it.
    
    cd ~/path/to/Packages
    git clone git://github.com/NicoSantangelo/sublime-gulp.git Gulp
