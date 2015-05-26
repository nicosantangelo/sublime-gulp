# Sublime Gulp

A Gulp task runner with snippets for Sublime Text.

This package is a merge between [Gulp Snippets](https://github.com/filipelinhares/gulp-sublime-snippets) from [@filipelinhares](https://github.com/filipelinhares) and [Gulp](https://github.com/NicoSantangelo/sublime-gulp) from [NicoSantangelo](https://github.com/NicoSantangelo) (this last one, based of the awesome [sublime-grunt](https://github.com/tvooo/sublime-grunt)).

## Usage

### 1. Run Tasks
To run a task, first choose `Gulp` from the command pallete, the package will search for a gulpfile.js in an open folder and create a cache (`.sublime-gulp.cache`) with it (the first run might be a little slow).

The package will display all the tasks in a list, selecting one will run it (if you want, you can [run specific tasks with a keyboard shortcut](#bind-specific-tasks)).

To show the task output the package uses a panel or a new tab (depends on your [settings](#settings)), you can add a [key binding](http://docs.sublimetext.info/en/latest/reference/key_bindings.html) to open the panel (check the [`Gulp: Show Panel`](#4-show-panel) command).

Keep in mind that, the package creates the first cache using [node](http://nodejs.org/), so for it to work you might need to add your node_modules path to NODE_PATH, for example (for Unix):

`export NODE_PATH=/usr/local/lib/node_modules`

**Troubleshooting**

The plugin wont work unless you have `gulp` defined on your gulpfile.

So if you can't find why Sublime Gulp isn't working be sure to at least have `var gulp = require('gulp');` defined. [More info](https://github.com/NicoSantangelo/sublime-gulp/issues/12) (thanks [@smeijer](https://github.com/smeijer) for the help)

**CoffeeScript**

If you want to use a `gulpfile.coffee` you need to do two things:

1. Add `module.exports = gulp` to your `gulpfile.coffee` so node can use it
2. Create a gulpfile.js if it doesn't exist and add this to it:

```javascript
require('coffee-script/register');
var gulp = require('./gulpfile.coffee');
```

That's it!. Thanks to [@guillaume86](https://github.com/guillaume86) for the help in the [issue #5](https://github.com/NicoSantangelo/sublime-gulp/issues/5)

**Mac OS X**

It's possible that your path isn't being reported by your shell so if you're having troubles running the package, give [SublimeFixMacPath](https://github.com/int3h/SublimeFixMacPath) a try.

### 2. Run Tasks (silent)
Works the same way as the normal `Gulp` command, but `Gulp (silent)` will not write the results on the output panel or tab.

### 3. Kill tasks
To kill running tasks like `watch` you can pick the command `Gulp: Kill running tasks`. 

**Windows**

If you're running Windows, the package will use [taskkill](http://technet.microsoft.com/en-us/library/cc725602.aspx) so every child process is correctly terminated. If the executable isn't on your system, you'll need to add it for this command to work correctly.

### 4. Show Panel
`Gulp: Show Panel` shows the closed output panel (just the panel, it won't re-open the tab if you're using the [`results_in_new_tab` setting](#settings)).

### 5. List plugins
Running `Gulp: List plugins` from the command palette will display the gulp plugins on a searcheable list. Picking one will open it on your default browser.

### 6. Delete cache
Running `Gulp: Delete cache` will delete the `.sublime-gulp.cache` file for you, forcing a re-parse of the `gulpfile.js`.

### 7. Gulp exit
This command will close Sublime Text, but first it'll kill any running tasks. It's the same as running `Gulp: Kill running tasks` and immediately exiting the editor. If error occurs killing the tasks or no running tasks are found, the editor will close anyways.

You can select `Gulp: Exit editor killing running tasks` from the command palette or create a [keybinding](#shortcut-keys) like this:

````
{ "keys": ["KEYS"], "command": "gulp_exit" }
````

You can bind it to `alt+f4` or `super+q` so you don't have to remember it. Sadly it **won't run** if you close the editor using the close button.

## Snippets

#### vargulp
```
var gulp = require('gulp-name');
```

#### pipe
```
pipe(name('file'))
```

#### gulps - [Docs](https://github.com/gulpjs/gulp/blob/master/docs/API.md#gulpsrcglobs-options)
```
gulp.src('scriptFiles')
  .pipe(name('file'))
```

#### gulpt - [Docs](https://github.com/gulpjs/gulp/blob/master/docs/API.md#gulptaskname-deps-fn)
```
gulp.task('name',['tasks'], function() {
    // content
});
```

#### gulpd - [Docs](https://github.com/gulpjs/gulp/blob/master/docs/API.md#gulpdestpath)
```
.pipe(gulp.dest('folder'));
```

#### gulpw - [Docs](https://github.com/gulpjs/gulp/blob/master/docs/API.md#gulpwatchglob-opts-tasks)
```
gulp.watch('file', ['tasks']);
```

#### gulpwcb - [Docs](https://github.com/gulpjs/gulp/blob/master/docs/API.md#gulpwatchglob-opts-cb)
```
gulp.watch('file', function(event) {
  console.log(' File '+event.path+' was '+event.type+', running tasks...');
});
```


## Settings

The file `SublimeGulp.sublime-settings` is used for configuration, you can change your user settings in `Preferences -> Package Settings -> Gulp -> Settings - User`.

The defaults are:

````json
{
    "exec_args": {},
    "gulpfile_paths": [],
    "results_in_new_tab": false,
    "results_autoclose_timeout_in_milliseconds": 0,
    "show_silent_errors": true,
    "log_erros": true,
    "syntax": "Packages/Gulp/syntax/GulpResults.tmLanguage",
    "nonblocking": true,
    "flags": {}
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

If set to `true`, a new tab will be used instead of a panel to output the results.

#### gulpfile_paths

Additional paths to search the gulpfile in, by default only the root of each project folder is used.
Example: `["src", "nested/folder"]`

#### results_autoclose_timeout_in_milliseconds

Defines the delay used to autoclose the panel or tab that holds the gulp results.
If false (or 0) it will remain open, so if what you want if to keep it close check the [`silent`](#2-run-tasks-silent) command.

#### show_silent_errors

If true it will open the output panel when running [`Gulp (silent)`](#2-run-tasks-silent) only if the task failed

#### log_erros

Toggles the creation of sublime-gulp.log if any error occurs.

#### syntax

Syntax file for highlighting the gulp results. You can pick it from from the command pannel as `Set Syntax: Gulp results`.

Set the setting to `false` if you don't want any colors (you may need to restart Sublime if you're removing the syntax).

#### nonblocking

When enabled, the package will read the streams from the task process using two threads, one for `stdout` and another for `stderr`. This allows all the output to be piped to Sublime live without having to wait for the task to finish.

If set to `false`, it will read first from `stdout` and then from `stderr`.

#### flags

This seting lets you define custom flags for your gulp commands. The key is the name of the task and the value is the string containing the flags.

For example if you have to run `build` with the `--watch` flag, like this `gulp build --watch` you'll do:

````json
{
    "flags": {
        "build": "--watch"
    }
}
````

If you want to add a flag to a task just for a project, you can try [binding a specific task](#bind-specific-tasks).

## Shortcut Keys

This package doesn't bind any command to a keyboard shortcut, but you can add it like this:

````json
[
    { "keys": ["KEYS"], "command": "gulp" },

    { "keys": ["KEYS"], "command": "gulp_kill" },

    { "keys": ["KEYS"], "command": "gulp_show_panel" },

    { "keys": ["KEYS"], "command": "gulp_plugins" },

    { "keys": ["KEYS"], "command": "gulp_delete_cache" },

    { "keys": ["KEYS"], "command": "gulp_exit" }
]
````

#### Bind specific tasks
You also can use a shortcut for running a specific task like this:

````json
{ "keys": ["KEYS"], "command": "gulp", "args": { "task_name": "watch" } }
````

and if you want to run it in [`silent`](#2-run-tasks-silent) mode, you can add `"silent"` to the `args`

````json
{ "keys": ["KEYS"], "command": "gulp", "args": { "task_name": "watch", "silent": true } }
````

Lastly, you can add a flag to the command using `task_flag`. This option will override the any [flag](#flags) defined on the settings file. If you set it to `""` (empty string) it will run the command without flags.

````json
{ "keys": ["KEYS"], "command": "gulp", "args": { "task_name": "build", "task_flag": "--watch" } }
````

## Installation

### PackageControl
If you have [PackageControl](http://wbond.net/sublime_packages/package_control) installed, you can use it to install the package.

Just type `cmd-shift-p`/`ctrl-shift-p` to bring up the command pallete and pick `Package Control: Install Package` from the dropdown, search and select the package there and you're all set.

### Manual

You can clone the repo in your `/Packages` (*Preferences -> Browse Packages...*) folder and start using/hacking it.
    
    cd ~/path/to/Packages
    git clone git://github.com/NicoSantangelo/sublime-gulp.git Gulp
