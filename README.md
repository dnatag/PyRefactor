# Python refactoring made easy in Sublime Text 3#
## Introduction ##
This plugin is designed to help [rope](https://github.com/python-rope/rope.git) users to refactor python codes. It generates a temporary rope script, which refactors your codes, and then it reloads the refactored codes in Sublime Text. This is a quick and dirty hack and may not work well for very complex codes.

## Refactor Methods Implemented ##
0. Create a rope project (Ctrl+Shift+N): You must create the rope project first before performing any following refactoring actions. 
1. Undo last refactoring action (Ctrl+Shift+Z)
2. Redo last refactoring action (Ctrl+Shift+Y)
3. Rename a field
4. Rename a module
5. Transform a module to package with the same name
6. Change the signiture of a function/method
7. Extract method
8. Extract variable
9. Inline: Inline occurrences of a method/variable/parameter
10. Change a local variable to field
11. Introduce parameter to a function
12. Introduce constructor factory (select a class name to perform the refactoring)
13. Encapsulate field: Generate a getter/setter for a field and changes its occurrences to use them.
14. Use function: Try to use a function whenever possible
15. Move across module
16. Move attribute
17. Transform function to method object
18. Restructure

## Installation ##
Prerequisite: Install the [rope package](https://github.com/python-rope/rope.git) from PyPI.

1. Automatic installation via Package Control. Search for [PyRefactor](https://sublime.wbond.net/packages/PyRefactor) under Package Control.
2. Manual installation via github
Clone the git repository directly into the Packages folder

    git clone git@github.com:dnatag/PyRefactor.git

## Usage Guide ##
0. Create a rope project in the project level (Ctrl+Shift+N)
1. Use Cmd+Shift+P (Ctrl+Shift+P in Linux or Windows) and type Refactor to choose refactoring method
2. Under Tools Menu and then submenu Refactor to choose proper refactoring method

## Licence ##

You can use this under Simplified BSD License:

Copyright (c) 2014, Yi Xie All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


