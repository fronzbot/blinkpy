========================
Contributing to blinkpy
========================

Everyone is welcome to contribute to blinkpy! The process to get started is described below.


Fork the Repository
-------------------

You can do this right in github: just click the 'fork' button at the top right.

Start Developing
-----------------

1. Setup Local Repository
   .. code:: bash
       
       $ git clone https://github.com/<YOUR_GIT_USERNAME>/blinkpy.git
       $ cd blinkpy
       $ git remote add upstream https://github.com/fronzbot/blinkpy.git

2. Create virtualenv and install dependencies
   
   .. code:: bash

       $ python -m venv venv
       $ source venv/bin/activate
       $ pip install -r requirements.txt
       $ pip install -r requirements_test.txt
       $ pre-commit install

3. Create a Local Branch
   
   First, you will want to create a new branch to hold your changes:
   ``git checkout -b <your-branch-name>``


4. Make changes
   
   Now you can make changes to your code.  It is worthwhile to test your code as you progress (see the **Testing** section)

5. Commit Your Changes
   
   To commit changes to your branch, simply add the files you want and the commit them to the branch.  After that, you can push to your fork on GitHub:

   .. code:: bash
   
       $ git add .
       $ git commit
       $ git push origin HEAD
   
6. Submit your pull request on GitHub
   
   - On GitHub, navigate to the `blinkpy <https://github.com/fronzbot/blinkpy>`__ repository.
   - In the "Branch" menu, choose the branch that contains your commits (from your fork).
   - To the right of the Branch menu, click New pull request.
   - The base branch dropdown menu should read ``dev``. Use the compare branch drop-down menu to choose the branch you made your changes        in.
   - Type a title and complete the provided description for your pull request.
   - Click Create pull request.
   - More detailed instructions can be found here: `Creating a Pull Request` <https://help.github.com/articles/creating-a-pull-request>`__
   
7. Prior to merge approval
   
   Finally, the ``blinkpy`` repository uses continuous integration tools to run tests prior to merging. If there are any problems, you  will see a red 'X' next to your pull request.


Testing
-------

It is important to test the code to make sure your changes don't break anything major and that they pass PEP8 style conventions.
First, you need to locally install ``tox``

.. code:: bash

    $ pip install tox


You can then run all of the tests with the following command:

.. code:: bash
    
    $ tox

**Tips**

If you only want to see if you can pass the local tests, you can run ``tox -e py37`` (or whatever python version you have installed.  Only ``py36``, ``py37``, and ``py38`` will be accepted).  If you just want to check for style violations, you can run ``tox -e lint``.  Regardless, when you submit a pull request, your code MUST pass both the unit tests, and the linters.

If you need to change anything in ``requirements.txt`` for any reason, you'll want to regenerate the virtual envrionments used by ``tox`` by running with the ``-r`` flag: ``tox -r``

If you want to run a single test (perhaps you only changed a small thing in one file) you can run ``tox -e py37 -- tests/<testname>.py -x``.  This will run the test ``<testname>.py`` and stop testing upon the first failure, making it easier to figure out why a particular test might be failing.  The test structure mimics the library structure, so if you changed something in ``sync_module.py``, the associated test file would be in ``test_sync_module.py`` (ie. the filename is prepended with ``test_``.


Catching Up With Reality
-------------------------

If your code is taking a while to develop, you may be behind the ``dev`` branch, in which case you need to catch up before creating your pull-request.  To do this you can run ``git rebase`` as follows (running this on your local branch):

.. code:: bash

    $ git fetch upstream dev
    $ git rebase upstream/dev

If rebase detects conflicts, repeat the following process until all changes have been resolved:

1. ``git status`` shows you the filw with a conflict.  You will need to edit that file and resolve the lines between ``<<<< | >>>>``.
2. Add the modified file: ``git add <file>`` or ``git add .``.
3. Continue rebase: ``git rebase --continue``.
4. Repeat until all conflicts resolved.
