"use strict";

var path = require("path"),
    fs = require("fs"),
    crypto = require("crypto"),
    shasum = crypto.createHash("sha1");

var cwd = process.cwd();

var cachePath    = path.join(cwd, ".sublime-gulp.cache");
var tmpfilePath  = path.join(cwd, ".sublime-gulp-tmp.js");
var gulpfilePath = (function() {
    var allowedExtensions = [".babel.js", ".js"];
    for(var i = 0; i < allowedExtensions.length; i++) {
        var filepath = path.join(cwd, "gulpfile" + allowedExtensions[i]);
        if (fs.existsSync(filepath)) {
            return filepath;
        }
    }
})();

var requireGulp = function(gulpfilePath) {
    // Creates a temporal file exporting gulp at the end (so it can be retrived by node) and then requires it (related: http://goo.gl/QYzRAO)
    var fileSrc = fs.readFileSync(gulpfilePath);
    fileSrc += "\n/**/;module.exports = gulp;";
    fs.writeFileSync(tmpfilePath, fileSrc);
    try {
        return require(tmpfilePath);
    } catch(ex) {
        fs.unlink(tmpfilePath);
        throw ex;
    }
};
var generatesha1 = function(filepath) {
    var content = fs.readFileSync(filepath);
    shasum.update("blob " + content.length + "\0", "utf8");
    shasum.update(content);
    return shasum.digest("hex");
};
var getJSONFromFile = function(filepath) {
    if(fs.existsSync(filepath)) {
        var content = fs.readFileSync(filepath, { encoding: "utf8" });
        return JSON.parse(content);
    }
};
var forEachTask = function(fn) {
    if(gulp.tasks) {
        _forEachTask3x(fn);
    } else {
        _forEachTask4x(fn);
    }
};

var _forEachTask3x = function(fn) {
    for(var task in gulp.tasks) {
        if (gulp.tasks.hasOwnProperty(task)) {
            fn(gulp.tasks[task].name, gulp.tasks[task].dep);
        }
    }
};

var _forEachTask4x = function(fn) {
    var tasksTree = gulp.tree({ deep: true })
    var iterable = tasksTree.forEach ? tasksTree : tasksTree.nodes

    iterable.forEach(function(task) {
        if (task.type === "task") {
            var deps = [];
            task.nodes.forEach(function(node) {
              var innerDeps = node.nodes.map(function(dep) {
                if (dep.type === "task") {
                  return dep.label;
                }
              });
              deps = deps.concat(innerDeps);
            });
            
            fn(task.label, deps);
        }
    });
};

var gulp = requireGulp(gulpfilePath);
var sha1 = generatesha1(gulpfilePath);
var gulpsublimecache = getJSONFromFile(cachePath) || {};

if (!gulpsublimecache[gulpfilePath] || gulpsublimecache[gulpfilePath].sha1 !== sha1) {
    var tasks = {};

    forEachTask(function(name, deps) {
        tasks[name] = {
            name: name,
            dependencies: deps.join(" ")
        };
    });

    gulpsublimecache[gulpfilePath] = gulpsublimecache[gulpfilePath] || {};
    gulpsublimecache[gulpfilePath] = {
        sha1: sha1,
        tasks: tasks
    };

    fs.writeFileSync(cachePath, JSON.stringify(gulpsublimecache));
}

fs.unlink(tmpfilePath);