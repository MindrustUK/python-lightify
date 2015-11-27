python-lightify
===============

Python module for Osram Lightify

It communicates with a Lightify gateway connected to the same LAN via
TCP port 4000 using a binary protocol.

This is a work in progress.

Forked from https://github.com/mikma/python-lightify to port to Python 3.x and to add some support for https://home-assistant.io/
Populating Lights, Turning them On and Off works. Only tested with Osram A60 RGBW Bulbs. I'll try and find some time to get Colour and Brightness going as well.

Code is probably pretty horrible for anyone who actually knows Python well so comments on refactoring / improving things happily received.
