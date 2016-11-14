# Sublime Gulp

A plugin to run your [Gulp](http://gulpjs.com/) tasks from within Sublime plus some handy [snippets](#snippets) too.

## Quickstart

1. Install Via [Package Control](https://packagecontrol.io) `Gulp`
2. Open your repo containing either a `gulpfile.js` file or directory
3. If you don't already have a `default` gulp task make one
4. Menu to Tools>Gulp>Run Default Task
5. Enjoy!

## Installation

### via PackageControl
If you have [PackageControl](http://wbond.net/sublime_packages/package_control) installed, you can use it to install the package.

Just type `cmd-shift-p`/`ctrl-shift-p` to bring up the command pallete and pick `Package Control: Install Package` from the dropdown, search and select the package there and you're all set.

### Manually

You can clone the repo in your `/Packages` (*Preferences -> Browse Packages...*) folder and start using/hacking it.
    
    cd ~/path/to/Packages
    git clone git://github.com/NicoSantangelo/sublime-gulp.git Gulp

### Troubleshooting

For older gulp versions, the plugin makes use of [node](http://nodejs.org/) which should already be installed if you are using Gulp. It creates a cache using node, so in some systems you might need to add your node_modules path to the NODE_PATH, for example (for Unix):

`export NODE_PATH=/usr/local/lib/node_modules`

Sublime Gulp might not work without `var gulp = require('gulp');` defined in each task file. [More info](https://github.com/NicoSantangelo/sublime-gulp/issues/12) (thanks [@smeijer](https://github.com/smeijer) for the help)

If you are having trouble running the plugin in **Mac OSX** it's possible that your path isn't being reported by your shell. In which case give the plugin [SublimeFixMacPath](https://github.com/int3h/SublimeFixMacPath) a try. It may resolve our issue.

If you still can't get it to run properly, first make sure your Gulp tasks run from a terminal (i.e. outside of sublime) and if so then submit an [issue](https://github.com/NicoSantangelo/sublime-gulp/issues).


### CoffeeScript Support

If you want to use a `gulpfile.coffee` you need to do two things:

1. Add `module.exports = gulp` to your `gulpfile.coffee` so node can use it
2. Create a gulpfile.js if it doesn't exist and add this to it:

```javascript
require('coffee-script/register');
var gulp = require('./gulpfile.coffee');
```

### Gulpfile.js

The Sublime Gulp plugin was made for those using the [Gulp Streaming Build - Task Runner System](https://github.com/gulpjs/gulp) within [Node.js](https://nodejs.org/) for their workflow.

Sublime Gulp now supports not only a basic gulpfile.js file in the root of your project but also recognizes your tasks within a directory set by the RequireDir module or within a gulpfile.js directory. So no matter how your gulp tasks are organized Sublime Gulp will find them.

## Usage

### Available Commands

Sublime Gulp supports the following commands accessible from `Tools -> Command Palette` by typing in "Gulp". They are also accesible from menus as indicated below the table. `Default.sublime-commands` also lists them.

|     Command       |  From Command Palette | From Menu                 |
|:-----------------:|:---------------------:|:------------------------:|
| [gulp](#running-a-gulp-task)                | Gulp or Gulp (silent)     | List Tasks to Run |  
| [gulp_arbitrary](#arbitrary-task)           | Gulp: Run arbitrary task  | Run Arbitrary Task |  
| [gulp_last](#run-last-task)                 | Gulp: Run last task       | Run Last Task |  
| [gulp_kill](#killing-tasks)                 | Gulp: Kill All Gulp Tasks | Kill running tasks |
| [gulp_kill_task](#killing-tasks)            | Gulp: Kill specific running task | Kill a currently running task |
| [gulp_delete_cache](#deleting-the-cache)    | Gulp: Delete Cache        | Delete Cache |
| [gulp_plugins](#listing-gulp-plugins)       | Gulp: List plugins        | List Gulp Plugins |
| [gulp_show_panel](#show-or-hide-the-panel)  | Gulp: Show panel          | Show Gulp Panel |
| [gulp_hide_panel](#show-or-hide-the-panel)  | Gulp: Hide panel          | Hide Gulp Panel |
| [gulp_exit](#quitting-sublime-killing-running-gulp-tasks)  | Gulp: Exit editor killing running tasks | Quit Killing All Gulp Tasks |

* The first five commands are available via `Tools -> Gulp` in the main menu and in `Gulp` in the sidebar context menu.
* The the 6th and 7th are available via `View -> Gulp` in the main menu.
* The last command is available via `File` at the bottom in the main menu.


### Running a Gulp Task
To run a task, first choose `Gulp` from the command pallete or `List Tasks to Run` from the menu, the package will search for your tasks in the open folder/project and create a cache (`.sublime-gulp.cache`) in the root. The first run will be slow as the cache builds but then the cache will speed up future access. You can use the [`gulp_delete_cache`](#deleting-the-cache) command to rebuild the cache if you are not seeing your newly added Gulp Tasks or some have gone missing.

The plugin will then display all the Gulp tasks in a list. Selecting one will run that task. To show the task's standard output the plugin uses a panel or a new tab (depends on your [settings](#settings)). After a first task has been run you can use the hide and show panel commands as desired. (see table above) 

If you want to run the normal `Gulp` command without standard output to the panel use instead `Gulp (silent)`. 

#### Arbitrary task

If you want to run an arbitrary task you need to choose `Gulp: Run arbitrary task` from the command pallete or `Run arbitrary task` from the menu. The package will then prompt an input panel where you can write what you want to add as a sufix to `gulp`.

#### Run last task

The command will re-run the last task ran by any of the package commands (if there's one).

### Customized Task Access

Out of the box Sublime Gulp has a menu item `Run Default Task` under `Tools -> Gulp` that will run your `default` Gulp task. Most Gulp users have a default task defined (like running their development tasks).

If you want to run other of your tasks from a menu item or [keyboard shortcut](#shortcut-keys) you can customize both.  

For example to add a menu item in the tools menu for a `sass` task do this. In your sublime user directory add following json in the `Main.sublime-menu` file (create one if you don't have one).

```json
[
    {
        "id": "tools",
        "children": [
             { "caption": "Run Sass Task", "command": "gulp", "args": { "task_name": "sass" } }
         ]
    }
]
```

_Note_: You can run any command silently by adding `"silent": true` to the `args`.

or you also can use a [keyboard shortcut](#shortcut-keys) to do the same. Edit `Preferences -> Key Bindings - User` to access the user key bindings file to which add this line:

````json
{ "keys": ["KEYS"], "command": "gulp", "args": { "task_name": "sass" } }
````

For more detailed information on [shortcut keys](#shortcut-keys) and [binding specific tasks](#bind-specific-tasks) below.

### Killing Tasks
To kill running tasks like `watch` you have two options, you can pick the command `Gulp: Kill running tasks` to kill all currently running tasks or `Gulp: Kill specific running task` to choose from the command pallete which task to kill. 

If you want to supress the command output, you can map it to a keyboard shortcut and pass `true` to the `silent` argument like this:

```json
{ "keys": ["KEYS"], "command": "gulp_kill", "args": { "silent": true } }

{ "keys": ["KEYS"], "command": "gulp_kill_task", "args": { "silent": true } }
```

For more detailed information on [shortcut keys](#shortcut-keys) and [binding specific tasks](#bind-specific-tasks) below.

**Windows**

If you're running Windows, the package will use [taskkill](http://technet.microsoft.com/en-us/library/cc725602.aspx) so every child process is correctly terminated. If the executable isn't on your system, you'll need to add it for this command to work correctly.

###  Show or Hide the Panel
`Gulp: Show Panel` shows the closed output panel (just the panel, it won't re-open the tab if you're using the `results_in_new_tab` [setting](#settings)). Alternatively typing `<esc>` will also close/hide an open panel.

### Listing Gulp Plugins
Running `Gulp: List plugins` from the command palette will display all gulp plugins available on a searcheable list. Picking one will open its github repo on your default browser.

### Deleting The Cache
Running `Gulp: Delete cache` will delete the `.sublime-gulp.cache` file for you, forcing a re-parse of the `gulpfile.js`.

### Quitting Sublime Killing Running Gulp Tasks
This command will close Sublime Text, but first it'll kill any running tasks. It's the same as running `Gulp: Kill running tasks` and immediately exiting the editor. If error occurs killing the tasks or no running tasks are found, the editor will close anyways.

You can select `Gulp: Exit editor killing running tasks` from the command palette or create a [keybinding](#shortcut-keys) like this:

````
{ "keys": ["KEYS"], "command": "gulp_exit" }
````

You can bind it to `alt+f4` or `super+q` so you don't have to remember it. Sadly it **won't run** if you close the editor using the close button (**x**).



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

The file `Gulp.sublime-settings` is used for configuration, you can change your user settings in `Preferences -> Package Settings -> Gulp -> Settings - User`.

The defaults are:

````json
{
    "exec_args": {},
    "recursive_gulpfile_search": false,
    "ignored_gulpfile_folders": [".git", "node_modules", "vendor", "tmp", "dist"],
    "gulpfile_paths": [],
    "results_in_new_tab": false,
    "results_autoclose_timeout_in_milliseconds": 0,
    "show_silent_errors": true,
    "log_errors": true,
    "syntax": "Packages/Gulp/syntax/GulpResults.tmLanguage",
    "nonblocking": true,
    "track_processes": true,
    "flags": {},
    "check_for_gulpfile": false,
    "tasks_on_save": {},
    "silent_tasks_on_save": {},
    "kill_before_save_tasks": false
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

##### gulp installed locally

If gulp is installed locally in the project, you have to specify the path to the gulp executable. Threfore, adjust the path to `/bin:/usr/bin:/usr/local/bin:node_modules/.bin`

#### recursive_gulpfile_search

If set to `true`, the package will search for a `gulpfile.js` file recursively through each top level folder ignoring the folders defined in `ignored_gulpfile_folders`.

If `false`, only top level folders and the ones found on `gulpfile_paths` are used.

#### ignored_gulpfile_folders

Ignored folder names for the recursive search of gulpfile.js files, used to drastically improve performance.
Example: `[".git", "node_modules", "vendor", "tmp", "dist"]`

#### gulpfile_paths

This setting is active *only* if `recursive_gulpfile_search` is `false`.

Each item in the array constitutes an additional paths to search the gulpfile in, by default only the root of each project folder is used.
Example: `["src", "nested/folder"]`

#### results_in_new_tab

If set to `true`, a new tab will be used instead of a panel to output the results.

#### results_autoclose_timeout_in_milliseconds

Defines the delay used to autoclose the panel or tab that holds the gulp results.
If false (or 0) it will remain open, so if what you want is to keep it closed check the [`silent`](#running-a-gulp-task) command.

#### show_silent_errors

If true it will open the output panel when running [`Gulp (silent)`](#running-a-gulp-task) only if the task failed

#### log_errors

Toggles the creation of `sublime-gulp.log` if any error occurs.

#### syntax

Syntax file for highlighting the gulp results. You can pick it from from the command panel as `Set Syntax: Gulp results`.

Set the setting to `false` if you don't want any colors (you may need to restart Sublime if you're removing the syntax).

#### nonblocking

When enabled, the package will read the streams from the task process using two threads, one for `stdout` and another for `stderr`. This allows all the output to be piped to Sublime live without having to wait for the task to finish.

If set to `false`, it will read first from `stdout` and then from `stderr`.

#### track_processes

Persist the long running task pids to a local file to keep track even if the editor is closed.

If set to `false` package will keep track of tasks in memory, meaning that if you run a long running task like `gulp watch` and restart Sublime Text, the process wont't necessarily die and you won't be able to kill it from the editor anymore.

If set to `true` the package will keep track of long running tasks using an internal `.sublime-gulp.cache`. So even if you close your editor and re-open it, you should still be able to list and kill running tasks.

Depending on the OS you're on, the process might die anyways without the package interverting. Sublime Gulp tries to remedy this by checking if the process is still alive before listing it, which works most of the time but it's not a reliable check.
Worst case scenario, you'll see a dead task, killing it won't do anything. _Worst and really not likely_ case scenario, you'll kill another process if the pid was reused by the OS :raised_hands:.


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

#### check_for_gulpfile

If `false` the package will run even if no `gulpfile.js` is found on the root folders currently open.

So for example, if you have *5* root folders on your Sublime sidebar and only *3* of them have a `gulpfile`, when you run `Sublime Gulp` with `check_for_gulpfile: true` it'll only show the *3* that have a `gulpfile.js`, but if you set `check_for_gulpfile` to false, it'll list _all_ *5* folders.

You might want to set it to false if you're using the `--gulpfile` flag, or if you want to leave the error reporting to gulp.

#### tasks_on_save

Allows you to run task(s) when you save a file. The key is the name of the task and the value is the string or array of glob pattern.

The base folder for glob pattern is the first folder in you project. So, if you have multiple folder, the glob pattern will only match on the first folder.

````javascript
{
    "tasks_on_save": {
        // Run browserify task when you save javasript file
        "browserify": "*.js",
        // Run sass task when you save sass file under "sass" folder
        "sass": "sass/*.scss",
        // Array of glob pattern
        "other": ["*.ext1", "*.ext2"]
    }
}
````

#### silent_tasks_on_save

Works the same way as [tasks_on_save](https://github.com/NicoSantangelo/sublime-gulp#tasks_on_save) but it runs the tasks on `silent` mode (using `Gulp (silent)`).

#### kill_before_save_tasks

If any task is defined on [tasks_on_save](https://github.com/NicoSantangelo/sublime-gulp#tasks_on_save) or [silent_tasks_on_save](https://github.com/NicoSantangelo/sublime-gulp#silent_tasks_on_save) setting this option to `true` will run [gulp_kill](#killing-tasks) before running any of them.


### Per project settings

If you want to have a per project settings, you first need to create a [project](https://www.sublimetext.com/docs/2/projects.html) going to `Project -> Save Project As` and then edit your project file (you can use `Project -> Edit Project`).
In there you can override Gulp settings like so:


````javascript
{
    "settings": {
        "results_in_new_tab": true
    },

    // Or, Sublime Text 3 only:
    "Gulp": {
        "check_for_gulpfile": false
    }
}
````

The package will search first on `"settings": {}`, then on `"Gulp": {}` (ST3 only) and lastly on the `Gulp.sublime-settings` file.

Keep in mind that the only *caveat* is that if you want to override the `syntax` key, you'll need to use `syntax_override` as key.

For a visual example go to [this comment on issue 53](https://github.com/NicoSantangelo/sublime-gulp/issues/53#issuecomment-153012155)


## Shortcut Keys

This package doesn't bind any command to a keyboard shortcut, but you can add it like this:

````json
[
    { "keys": ["KEYS"], "command": "gulp" },

    { "keys": ["KEYS"], "command": "gulp_arbitrary" },

    { "keys": ["KEYS"], "command": "gulp_last" },

    { "keys": ["KEYS"], "command": "gulp_kill" },

    { "keys": ["KEYS"], "command": "gulp_kill_task" },

    { "keys": ["KEYS"], "command": "gulp_show_panel" },

    { "keys": ["KEYS"], "command": "gulp_hide_panel" },

    { "keys": ["KEYS"], "command": "gulp_plugins" },

    { "keys": ["KEYS"], "command": "gulp_delete_cache" },

    { "keys": ["KEYS"], "command": "gulp_exit" }
]
````


#### Bind specific tasks

You can use a shortcut for running a specific task like this:

````json
{ "keys": ["KEYS"], "command": "gulp", "args": { "task_name": "watch" } }
````

and if you want to run it in [`silent`](#running-a-gulp-task) mode, you can add `"silent"` to the `args`

````json
{ "keys": ["KEYS"], "command": "gulp", "args": { "task_name": "watch", "silent": true } }
````

Lastly, you can add a flag to the command using `task_flag`. This option will override the any [flag](#flags) defined on the settings file.  

````json
{ "keys": ["KEYS"], "command": "gulp", "args": { "task_name": "build", "task_flag": "--watch" } }
````

_Note_: You can run commands like `gulp -v` if you set `task_name` to `""` (empty string) with a flag.

##Acknowledgments

This package is a merge between [Gulp Snippets](https://github.com/filipelinhares/gulp-sublime-snippets) from [@filipelinhares](https://github.com/filipelinhares) and [Gulp](https://github.com/NicoSantangelo/sublime-gulp) from [NicoSantangelo](https://github.com/NicoSantangelo) (this last one, inspired by the awesome [sublime-grunt](https://github.com/tvooo/sublime-grunt)).

Thanks to [@dkebler](https://github.com/dkebler) for re-writing the README.
