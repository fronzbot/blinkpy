# Contributing to blinkpy

Everyone is welcome to contribute to blinkpy! The process to get started is described below.

## Fork the Repository

You can do this right in gituhb: just click the 'fork' button at the top right.

## Setup Local Repository

```shell
$ git clone https://github.com/<YOUR_GIT_USERNAME>/blinkpy.git
$ cd blinkpy
$ git remote add upstream https://github.com/fronzbot/blinkpy.git
```

## Create a Local Branch

First, you need to make sure you're on the 'dev' branch:
``git checkout dev``
Next, you will want to create a new branch to hold your changes:
``git checkout -b <your-branch-name>``

## Make changes

Now you can make changes to your code.  It is worthwhile to test your code as you progress (see the **Testing** section)

## Commit Your Changes

To commit changes to your branch, simply add the files you want and the commit them to the branch.  After that, you can push to your fork on GitHub:

```shell
$ git add .
$ git commit -m "Put your commit text here.  Please be concise, but descriptive."
$ git push origin HEAD
```

## Testing

It is important to test the code to make sure your changes don't break anything major and that they pass PEP8 style conventions.
FIrst, you need to locally install ``tox``

```shell
$ pip3 install tox
```

You can then run all of the tests with the following command:

```shell
$ tox
```

### Tips

If you only want to see if you can pass the local tests, you can run ``tox -e py34``.  If you just want to check for style violations, you can run ``tox -e lint``.  Regardless, when you submit a pull request, your code MUST pass both the unit tests, and the linters.

If you need to change anything in ``requirements.txt`` for any reason, you'll want to regenerate the virtual envrionments used by ``tox`` by running with the ``-r`` flag: ``tox -r``

Please do not locally disable any linter warnings within the ``blinkpy.py`` module itself (it's ok to do this in any of the ``test_*.py`` files)

# Catching Up With Reality

If your code is taking a while to develop, you may be behind the ``dev`` branch, in which case you need to catch up before creating your pull-request.  To do this you can run ``git rebase`` as follows (running this on your local branch):

```shell
$ git fetch upstream dev
$ git rebase upstream/dev
```

If rebase detects conflicts, repeat the following process until all changes have been resolved:

1. ``git status`` shows you the filw with a conflict.  You will need to edit that file and resolve the lines between ``<<<< | >>>>`.
2. Add the modified file: ``git add <file>`` or ``git add .``.
3. Continue rebase: ``git rebase --continue``.
4. Repeat until all conflicts resolved.

# Creating a Pull Request

Please follow these steps to create a pull request against the ``dev`` branch: [Creating a Pull Request](https://help.github.com/articles/creating-a-pull-request/)

# Monitor Build Status

Once you create your PR, you can monitor the status of your build [here](https://travis-ci.org/fronzbot/blinkpy),  Your code will be tested to ensure it passes and won't cause any problems after merging.