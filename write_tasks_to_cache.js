"use strict";

var path = require("path"),
    fs = require("fs"),
    crypto = require("crypto"),
    shasum = crypto.createHash("sha1");

var gulp = require("gulp");

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
    var tasks = gulp.tasks;
    for(var task in gulp.tasks) {
        if (gulp.tasks.hasOwnProperty(task)) {
            fn(gulp.tasks[task].name, gulp.tasks[task].dep);
        }
    }
};

var cwd = process.cwd();

require(cwd + "/gulpfile");

var gulpfilePath = path.join(cwd, "gulpfile.js");
var cachePath = path.join(cwd, ".sublime-gulp.cache");
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