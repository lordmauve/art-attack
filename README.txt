Art Attack
==========

Entry in PyWeek #12  <http://www.pyweek.org/12/>
URL: http://pyweek.org/e/TeamWasabi
Team: Team Wasabi
Members: Daniel Pope <mauve@mauvesoft.co.uk>, Glenn Jones <glenn@millenniumhand.co.uk>
License: see LICENSE.txt

Running the Game
----------------

On Windows or Mac OS X, locate the "run_game.py" file and double-click it.

Othewise open a terminal / console and "cd" to the game directory and run:

  python run_game.py

How to Play the Game
--------------------

Try to paint the picture using your clumsy brush - Nine Times the size you might
like.

The key bindings are in artattack/keybindings.py in a relatively straightforward
format. You may need to change them - refer to the Pygame Docs
(http://pygame.org/docs/ref/key.html) to see what key constants you can use.

Main controls - 

UP, DOWN, LEFT, RIGHT - Movement
INS - Paint
DEL - Cycle colour
END - Attack

Alt Controls (red in split-screen)

W, A, S, D - Movement
F - Paint
G - Cycle colour
R - Attack

Cycling colour uses an MRU system so you can toggle backwards and forwards.

Network Play
------------

The default server port is 9067. You may need to open a port in your firewall to host a game. There is a command line options for starting a server on a different port (but the option for changing the painting was taken out when I implemented the menu, stupidly).

More usefully, you can connect to a server from the commandline:

python run_game.py -c hostname-or-ip[:port]

A good place to set up games is the official #pyweek channel on Freenode.
 
Original Pictures
-----------------

You can use any picture with an indexed palette, not just the pre-supplied ones. Just drop it into data/paintings/. Images with a 3:2 ratio whose dimensions are factors of 320 and 240, with ~4-8 colours work best (players can only hold 6 colours). In network games, the client doesn't need a copy of the image, because it is transferred from the host before the game starts.

Credits
-------

Concept - Daniel Pope
Programming - Daniel Pope
Occasional Programmer - Glenn Jones
Graphics - Daniel Pope
Sound - Daniel Pope

With thanks to Jonathan Hartley, Ciarán Mooney and René Dudfield.

Support
-------

If you have any issues running this game during the PyWeek 12 judging period I will be happy to help. Drop me an e-mail at mauve@mauvesoft.co.uk and I'll do my best to resolve your problem.

Development notes 
-----------------

Creating a source distribution with::

   python setup.py sdist

You may also generate Windows executables and OS X applications::

   python setup.py py2exe
   python setup.py py2app

Upload files to PyWeek with::

   python pyweek_upload.py

Upload to the Python Package Index with::

   python setup.py register
   python setup.py sdist upload


