# Adorn-o

Adorn-o is a computationally creative musical performance system for virtuosic bass guitar performance implement in Python developed as part of Callum Goddard's PhD at Queen Mary University of London (QMUL). It is offered as is with no support provided.


## How to start

Check `Adorn-o/main.py` for examples.

## Requirements

Adorn-o is best run from a virtual environment setup in the root folder. In addition to the python packages required, some additional components need to be downloaded and added.

Once you have added each of these running: `Adorn-o/test_all.py` will test Adorn-o, if the tested complete with no error all requirements are installed correctly.

## Python Packages

The required python packages are provided in: `requirements.txt`


### Adding and updating Synpy:
Synpy is required as part of the musical feature analysis. However the version provided here: https://code.soundsoftware.ac.uk/projects/syncopation-dataset/repository/show/synpy needs to be converted to run with python 3.

You can download and place the `synpy` folder within the root directory and call:
```
2to3 --output-dir=synpy -W -n Adorn-o/synpy
```

Which _should_ update and add the synpy files required into the correct location using [2to3](https://docs.python.org/3/library/2to3.html). You may need to correct the the tabs within `synpy/syncopation.py` as these can be  inconsistent after the 2to3 conversion is applied.

older are required to be placed within `Adorn-o/synpy`

### Adding and Updating FANTASTIC:

The [FANTASTIC](http://doc.gold.ac.uk/isms/mmm/?page=Software%20and%20Documentation) source files from: [http://www.doc.gold.ac.uk/isms/m4s/FANTASTIC.zip](http://www.doc.gold.ac.uk/isms/m4s/FANTASTIC.zip) are required to be extracted to:
```
Adorn-o/feature_analysis/
```

Once extracted, the following code is then needed to be added to line 247 of `Adorn-o/feature_analysis/FANTASTIC/Fantastic.R`:

```
callums.feature.similarity <- function(df.in = data.frame(),mel.fns=list.files(path=dir,pattern=".csv"),dir=".",features=c("p.range","step.cont.glob.var","tonalness","d.eq.trans"),use.segmentation=FALSE,method="euclidean",eucl.stand=TRUE,corpus.dens.list.fn=NULL,average=TRUE){
  
  #source("Feature_Similarity.R")
  require(cluster)
  
  # This is the melody features that similarity is calculated on...
  # can have a dataframe input here...
  if(length(df.in) == 0){
    mel.feat <- compute.features(melody.filenames=mel.fns,dir=dir,output="melody.wise",use.segmentation=use.segmentation)
    }else{
    mel.feat <-df.in
  }
  
  mel.feat.new <- as.data.frame(mel.feat[,features])
  
  
  row.names(mel.feat.new) <- mel.feat[,"file.id"]
  colnames(mel.feat.new) <- features
  sim <- NULL
  if(average==FALSE){
    
    for(i in seq(along=features)){
      sim[[paste(method,features[i],sep=".")]] <- compute.sim(mel.feat.new[,features[i]],features[i],row.names(mel.feat.new),method,eucl.stand,corpus.dens.list.fn)}
  }
  else{sim[["av.sim"]] <- compute.sim(mel.feat.new,features,row.names(mel.feat.new),method,eucl.stand,corpus.dens.list.fn) }
  
  sim
}
```

### Adding the bass guitar digital waveguide

To be able to render audio output the contents of the `waveguide_model` folder from: [https://github.com/callumgoddard/bass_guitar_waveguide_model](https://github.com/callumgoddard/bass_guitar_waveguide_model) are required to be placed within: `Adorn-o/waveguide_model`.

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
