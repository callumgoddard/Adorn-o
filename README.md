# Adorn-o

Adorn-o is a computationally creative musical performance system for virtuosic bass guitar performance implement in Python developed as part of Callum Goddard's PhD at Queen Mary University of London (QMUL). It is offered as is with no support provided.


## How to start

Check `main.py` for examples.


## Requirements
As (currently) no requirements.txt is provided, running `test_all.py` will run the unit tests for Adorn-o. All the main functions are called and the errors produced will highlight what packages you need to have installed. In addtion to this a non-extensive, non-comprehensive list of requirements are as follows:

 - MacOS is required as a pre-compiled version of melcov is used. For different operating systems the melconv binary files can likely be replaced with the correctly compiled version, but this has not been tested.
 - Python 2.7 (an update to python 3 is in the works)
 - R 3.2.1 to run the rpy2
 - rpy2 version 2.8.6
 - pyguitarpro: https://github.com/Perlence/PyGuitarPro/releases/tag/v0.5
 - matlab python module
 - [bass_guitar_waveguide_model](https://github.com/callumgoddard/bass_guitar_waveguide_model/) for synthesis of the audio output
 - FANTASTIC (a slightly modified version is provided. Original is found here: http://doc.gold.ac.uk/isms/mmm/?page=Software%20and%20Documentation)
 - synpy (provided but sourced from: https://code.soundsoftware.ac.uk/projects/syncopation-dataset/repository/show/synpy)
 - scipy, numpy and likely a few more....


## Contact

Callum Goddard: [c.goddard@qmul.ac.uk](c.goddard@qmul.ac.uk)

## Reference
```
@phdthesis{Goddard:2021,
	address = {Queen Mary University of London},
	author = {Callum Goddard},
	school = {School of Electronic Engineering and Computer Science},
	title = {Virtuosity in Computationally Creative Musical Performance for Bass Guitar},
	year = {2021}}
 ```
