xhail²
======

![xhail² logo](logo.png)

[![CI](https://github.com/stefano-bragaglia/xhail2/actions/workflows/ci.yml/badge.svg)](https://github.com/stefano-bragaglia/xhail2/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/stefano-bragaglia/xhail2/branch/main/graph/badge.svg)](https://codecov.io/gh/stefano-bragaglia/xhail2)

**xhail²** *(eXtended Hybrid Abductive Inductive Learning)* is a nonmonotonic ILP *(Inductive Logic Programming)* system that combines *deductive* (consequence-based), *abductive* (assumption-based) and *inductive* (generalisation-based) inference types within a common logical framework.

This is a faithful Python port of the original [Java implementation](https://github.com/stefano-bragaglia/XHAIL), written as idiomatic Python OOP.

The system takes a background theory *B* and a set of examples *E* as input to return a set of hypotheses *H* that entail *E* with respect to *B* as output. The hypothesis space is constrained by a set of user-defined mode declarations and is filtered by a compression heuristic that prefers hypotheses with fewer literals.

The picture below shows the answer to the well-known problem of penguins as computed by **XHAIL**.
In this problem, we know that penguins are a species of birds.
We have 4 individuals: some birds (`a`, `b` and `c`) and a penguin (`d`).
This information is called background knowledge, or simply background.
All the evidences show that `a` and `b` fly, `c` is very likely to fly and `d` is rather likely not to fly.
This information is commonly referred to as examples.
Last but not least, we know that birds typically fly and birds may (or may not) be penguins.
This information is known as mode declarations.
The answer provided by **XHAIL** suggests that each bird that is not a penguin flies.
The problem is encoded by the following statements:

    %% penguins_weighted.lp
    %%%%%%%%%%%%%%%%%%%%%%%

    #display flies/1.
    #display penguin/1.

    %% B. Background
    bird(X):-penguin(X).
    bird(a;b;c).
    penguin(d).

    %% E. Examples
    #example flies(a) @2.
    #example flies(b) @2.
    #example flies(c) =5 @2.
    #example not flies(d) =3 @2.

    %% M. Modes
    #modeh flies(+bird) :0-100 =4.
    #modeb penguin(+bird) :1 @2.
    #modeb not penguin(+bird) :3.

    %% Answer:
    % flies(V1):-not penguin(V1),bird(V1).


Requirements
------------

This repository contains the source code and some example problems for **xhail²**.
The following sections describe the steps required to set up and run **xhail²**.

### Prerequisites

**xhail²** is a *Python* application. Python 3.14 or later must be installed on the target machine. You can check the version with:

    python3 --version

If Python 3.14 is not installed, download it from the [official website](https://www.python.org/downloads/).

**xhail²** uses [hatch](https://hatch.pypa.io/) for project management, environment handling, and running scripts. Install it with:

    pip install hatch

**xhail²** also requires *Gringo*/*Clasp* (version 3.x) as external ASP solvers. See the **Configuring xhail²** section below.

### Obtaining xhail²

Clone the repository:

    git clone https://github.com/stefano-bragaglia/xhail2.git

### Installing xhail²

From within the `xhail2/` folder, create the project environment and install all dependencies:

    hatch env create

This creates a `.venv/` virtual environment in the project directory with all required tools.

To verify the installation:

    hatch run xhail2 --version

which should output:

    xhail2 version 0.1.0

    Copyright (c) Stefano Bragaglia
    Copyright (c) Oliver Ray

    GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
    'xhail2' is free software: you are free to change and redistribute it.
    There is NO WARRANTY, to the extent permitted by law.

### Available scripts

| Command            | Description                                       |
|--------------------|---------------------------------------------------|
| `hatch run easy`   | Cyclomatic complexity report (`radon`)            |
| `hatch run lint`   | Lint check (`ruff`)                               |
| `hatch run test`   | Run test suite with coverage (`pytest --cov`)     |
| `hatch run check`  | Full quality gate: xenon + ruff + pytest          |

The `check` script is the gate that must pass before every commit and push.

#### Modifying xhail²

The source lives in `src/xhail/`. Tests live in `tests/`. After editing, run:

    hatch run check

to verify the code quality gate still passes. A pre-commit and pre-push hook enforce this automatically.

### Configuring xhail²

**xhail²** delegates reasoning tasks to an external *ASP* engine. It uses *Gringo*/*Clasp* version 3.x.
These tools are part of the *Potsdam Answer Set Solving Collection* (POTASSCO).

Compiled binaries are available on [SourceForge](http://sourceforge.net/projects/potassco/) in the *Files* section.
Download *Gringo v3* and *Clasp v3* appropriate for your system.

After installation, verify:

    gringo --version
    clasp --version

Common installation paths that **xhail²** will search automatically:

- `/Library/Gringo/`
- `/Library/Clasp/`
- `/usr/bin/`
- `/usr/local/bin/`

### Running xhail²

Once the ASP tools are installed, run **xhail²** via hatch:

    hatch run xhail2 --help

which produces:

    xhail2 version 0.1.0

    Usage:     xhail2  [options]  [files]

    Options:

      --all,-a            : Print all the best answers
      --blind,-b          : Remove colours from the program output
      --clasp,-c <path>   : Use given <path> as path for clasp 3
      --debug,-d          : Leave temporary files in ./temp
      --full,-f           : Show a more detailed output
      --gringo,-g <path>  : Use given <path> as path for gringo 3
      --help,-h           : Print this help and exit
      --iter,-i <num>     : Run <num> iterations for non-minimal answers
      --kill,-k <num>     : Stop the program after <num> seconds
      --mute,-m           : Suppress warning messages
      --prettify,-p       : Nicely format current problem
      --search,-s         : Search for clasp 3 and gringo 3
      --version,-v        : Print version information and exit

    Example:   xhail2  -c /Library/Clasp/clasp  -g /Library/Gringo/gringo  example.lp

The following example solves the penguins problem:

    hatch run xhail2 -a -b -f -m -c /Library/Clasp/clasp -g /Library/Gringo/gringo ./examples/toys/penguins_weighted.lp

### XHAIL syntax

**xhail²** uses the same input language as the original Java **XHAIL**. The language extends *Gringo*/*Clasp*'s ASP language with three directives:

- **`#display`** — selects which facts appear in the output (replaces `#show`/`#hide`)
- **`#example`** — declares positive or negative evidences
- **`#modeh`** — declares head mode declarations
- **`#modeb`** — declares body mode declarations

Weights (`=`), priorities (`@`), and constraints (`:`) can be attached to `#example`, `#modeh`, and `#modeb` statements to express costs, ordering, and usage bounds. See the original [XHAIL documentation](https://github.com/stefano-bragaglia/XHAIL) for full syntax details.
