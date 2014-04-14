# Sublime Gulp

A Gulp task runner for Sublime Text. This package is a port of the awesome [sublime-grunt](https://github.com/tvooo/sublime-grunt).

Currently under development :).

## Usage

### Run Tasks
To run a task, first choose `Gulp` from the command pallete, the package will search for a gulpfile.js in an open folder and create a cache (`.sublime-gulp.cache`) with it (the first run might be a little slow).

The package will display all the tasks in a list, selecting one will run it.

To show the task output the package uses a panel or a new tab (depends on your [settings](https://github.com/NicoSantangelo/sublime-gulp#settings)), you can  add a keybinding to open the panel like this:

`{ "keys": ["{KEYS}"], "command": "show_panel", "args": { "panel": "output.gulp_output" } }`

Keep in mind that, the package creates the first cache using [node](http://nodejs.org/), so for it to work you might need to add your node_modules path to NODE_PATH, for example (for Unix):

`export NODE_PATH=/usr/local/lib/node_modules`

### Kill tasks
To kill running tasks like `watch` you can pick the command `Gulp: Kill running tasks`. 

**Windows**
If you're running Windows, the package will use [taskkill](http://technet.microsoft.com/en-us/library/cc725602.aspx) so every child process is correctly terminated. If the executable isn't on your system, you'll need to add it for this command to work correctly.

## Settings

The file `SublimeGulp.sublime-settings` is used for configuration, you can change your user settings in `Preferences -> Package Settings -> Gulp -> Settings - User`.

The defaults are:

````json
{
	"exec_args": {},
    "results_in_new_tab": false
}
````

#### exec_args

You may override your `PATH` environment variable as follows (from [sublime-grunt](https://github.com/tvooo/sublime-grunt)):

````json
{
    "exec_args": {
        "path": "/bin:/usr/bin:/usr/local/bin"
    }
}
````

#### results_in_new_tab

If set to true, a new tab will be used instead of a panel to output the results.

## Shortcut Keys

This package doesn't bind any command to a keyboard shortcut, but you can add it like this:

````json
[
    { "keys": ["{KEYS}"], "command": "gulp" },
    { "keys": ["{KEYS}"], "command": "gulp_kill" }
]
````

You also can use a shortcut for running a specific task like this:
````json
{ "keys": ["{KEYS}"], "command": "gulp", "args": {"task_name": "watch"} },
````

## Instalation

### Manual

You can clone the repo in your `/Packages` (*Preferences -> Browse Packages...*) folder and start using/hacking it.
    
    cd ~/path/to/Packages
    git clone git://github.com/NicoSantangelo/sublime-gulp.git Gulp
