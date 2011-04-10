Art Attack
==========

Entry in PyWeek #12  <http://www.pyweek.org/12/>
URL: http://pyweek.org/e/TeamWasabi
Team: Team Wasabi
Members: Daniel Pope, Glenn Jones
License: see LICENSE.txt


Running the Game
----------------

On Windows or Mac OS X, locate the "run_game.pyw" file and double-click it.

Othewise open a terminal / console and "cd" to the game directory and run:

  python run_game.py


How to Play the Game
--------------------

Try to paint the picture using your clumsy brush - Nine Times the size you might like.

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

Note that cycling colour uses an MRU system so you can toggle backwards and forwards.

The key bindings are in artattack/keybindings.py.


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

