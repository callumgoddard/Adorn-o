
###############################################################
###### Fantastic: A program for Melodic Feature Analysis ######
######                  Daniel Müllensiefen              ######
######               Version: 1.0, May 2009            ######
###############################################################

############################
##### Global Parameters ####
############################


#### Limits of phrase length, in number of notes
phr.length.limits <- c(2,24)

#### Assignment scheme for intervals in semitones to interval classes as 2 digits sequences of letters and numbers
int.class.scheme <- data.frame(raw.int=c(-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,0,1,2,3,4,5,6,7,8,9,10,11,12), class.int=c("d8","d7","d7","d6","d6","d5","dt","d4","d3","d3","d2","d2","s1","u2","u2","u3","u3","u4","ut","u5","u6","u6","u7","u7","u8"))

#### Assignement scheme for time ratios to relative rhythm classes ("quicker", "equal", "longer"). 
tr.class.scheme <- list(class.symbols=c("q","e","l"), upper.limits=c(0.8118987,1.4945858))

#### Limits for m-term lengths to be used for analysis, in number of notes
n.limits <- c(1,5)


source("Feature_Value_Summary_Statistics.R")
source("M-Type_Summary_Statistics.R")
source("Feature_Similarity.R")

compute.features <- function(melody.filenames=list.files(path=dir,pattern=".csv"),dir=".",output="melody.wise", use.segmentation=TRUE, write.out=FALSE) {
	if(output!="melody.wise" & use.segmentation==FALSE) {
		print("Usage error: use.segmentation must be TRUE if phrase-wise output is requested")
		return(NA)}
	
	mel.features <- NULL
	phr.features.full <- NULL
	no.non.pos.onset.files <- 0
	if(dir!=".") {
		#melody.filenames <- list.files(path=dir,pattern=".csv")
		if(substr(dir,1,1) != .Platform$file.sep) {melody.filenames <- file.path(getwd(),dir,melody.filenames)}
		else{
			tmp.fns <- sapply(melody.filenames, function(x) strsplit(x,.Platform$file.sep)[[1]][length(strsplit(x,.Platform$file.sep)[[1]])])
			melody.filenames <- file.path(dir,tmp.fns)
			}
		}
	else{
		if(substr(melody.filenames[1],1,1) != .Platform$file.sep) {
			melody.filenames <- file.path(getwd(),melody.filenames)}
		else{melody.filenames <- melody.filenames}}
	for(i in seq(along=melody.filenames)) {
		fn <- unlist(strsplit(melody.filenames[i],"/"))
		file.id <- substr(fn[length(fn)],1,nchar(fn[length(fn)])-4)
		print(file.id)
		tonsets <- read.table(melody.filenames[i],sep=";",dec=",",skip=1,header=TRUE)[,"onset"]
		if(length(tonsets) < 2) next
		if(any((tonsets[2:length(tonsets)]-tonsets[1:(length(tonsets)-1)])<0)) {
			no.non.pos.onset.files <- no.non.pos.onset.files + 1
			print("Onsets not  monotonically positive")}
		if(any((tonsets[2:length(tonsets)]-tonsets[1:(length(tonsets)-1)])<0)) next
		
		sum.feat <- NULL
		phr.features <- NULL
		if(use.segmentation=="TRUE") {
			phrase.list <- make.phrases.from.melody(melody.filenames[i],file.id)
			for(j in 1:(length(phrase.list)-1)){
				## compute summary features phrase-wise 
				
				phr.length <- length(phrase.list[[j+1]][,"pitch"])
				if(phr.length <= phr.length.limits[1] | phr.length >= phr.length.limits[2]) { 
					if(j==1) next
					summary.features <- matrix(NA,1,length(colnames(summary.features)),dimnames=list((j),colnames(summary.features)))
					sum.feat <- rbind(sum.feat,summary.features)}
				else{
					summary.features <- summary.phr.features(phrase.list[[j+1]])
					sum.feat <- rbind(sum.feat,summary.features)
					}
				}
			}
		else{
			mel.data <- read.table(melody.filenames[i],sep=";",dec=",",skip=1,header=TRUE)
			mel.data <- mel.data[,1:15]
			summary.features <- summary.phr.features(mel.data,poly.contour=FALSE)
			sum.feat <- rbind(sum.feat,summary.features)
			}
		if(output=="melody.wise") {
		## for melody-wise output, average summary-features over phrases (there is only 1 phrase if segmentation is not requested) and compute ngram-features over entire melody
		
			ngram.mel.features <- data.frame(file.id,compute.features.from.ngram.table.main(n.grams.from.melody.main(melody.filenames[i])))
			#m.Z <- compute.zipfs.z(n.grams.from.melody.main(melody.filenames[i]))
			factors <- which(sapply(sum.feat,is.factor))
			m.sum.feat <- matrix(apply(sum.feat[,-factors],2, function(x) mean(x,na.rm=TRUE)),nrow=1,ncol=length(colnames(sum.feat)[-factors]),dimnames=list(i,colnames(sum.feat)[-factors]))
			m.freq.sum.feat <- matrix(apply(sum.feat[,factors],2, function(x) names(which(table(x)==max(table(x)))[1])), nrow=1,ncol=length(colnames(sum.feat)[factors]),dimnames=list(i,colnames(sum.feat)[factors]))
			mel.features <- rbind(mel.features,data.frame(ngram.mel.features,m.sum.feat,m.freq.sum.feat))
		}
		else{
		## for phrase-wise output, compute ngram-features for each phrase and append phrase-wise summary features computed above
		
			for(j in 1:(length(phrase.list)-1)){
				#print(j)
				phr.length <- length(phrase.list[[j+1]][,"pitch"])
				if(phr.length <= phr.length.limits[1] | phr.length >= phr.length.limits[2]) { 
					if(j==1) next
					ngram.phr.features <- data.frame(file.id,phr.id=j,mean.entropy=NA, mean.productivity=NA, mean.Simpsons.D=NA, mean.Yules.K=NA, mean.Sichels.S=NA, mean.Honores.H=NA)
					phr.features <- rbind(phr.features,ngram.phr.features)}
				else{
					ngram.phr.features <- data.frame(file.id,phr.id=j, compute.features.from.ngram.table.main(n.grams.from.phrase(phrase.list[[j+1]])))
					phr.features <- rbind(phr.features,ngram.phr.features)
					}
				}
			phr.features.full <- rbind(phr.features.full,data.frame(phr.features,sum.feat))
			#print(colnames(phr.features.full))
			}

	}
	if(output=="melody.wise"){final.results <- mel.features}
	else{final.results <- phr.features.full}
	if(write.out==TRUE) {write.table(final.results,file="feature_computation.txt",sep="\t",row.names=FALSE)}
	#cat("Number of files with non-positive increase in onset times:  ", no.non.pos.onset.files,"\n",sep=" ")
	final.results
}


make.phrases.from.melody <- function(melody.filename,file.id) {
	### Takes csv file with Grouper segmentation as input and outputs one csv file for each phrase ###
	mel.data <- read.table(melody.filename,sep=";",dec=",",skip=1,header=TRUE)
	mel.data <- mel.data[,1:15]
			if(sum(mel.data$temperley)<1){
			cat("csv file has no segmentation - please segment first","\n","\n",sep=" ")
			line1 <- readLines(melody.filename)[1]
			mel.list <- list(line1=line1)
			mel.list[[paste("file",file.id,"single_phrase",sep="-")]] <- mel.data
			}
		else{
			line1 <- readLines(melody.filename)[1]
			boundaries <- which(mel.data$temperley==1)
			start <- 1
			mel.list <- list(line1=line1)
			for(i in seq(along=boundaries)) {
				end <- boundaries[i]
				#print(mel.data[start:end,])
				mel.list[[paste("file",file.id,"ph",i,sep="-")]] <- mel.data[start:end,]
				start <- end+1
				}
			}
	mel.list
	} 
	
compute.corpus.based.feature.frequencies <- function(analysis.melodies="analysis_dir",ana.dir="analysis_dir",corpus="corpus_dir",write.out.corp.freq=TRUE,comp.feat.use.seg=TRUE,comp.feat.output="phrase.wise") {
	source("Frequencies_Summary_Statistics.R")
	
	if((substring(analysis.melodies[1],nchar(analysis.melodies[1])-3,nchar(analysis.melodies[1])-3)) == ".") {
		if((substring(analysis.melodies[1],nchar(analysis.melodies[1])-2,nchar(analysis.melodies[1]))) == "txt") {
			sum.feature.dataframe <- read.table(analysis.melodies,sep="\t",header=TRUE)}
		else{
			sum.feature.dataframe <- compute.features(analysis.melodies,dir=ana.dir,output=comp.feat.output,use.segmentation=comp.feat.use.seg)}
		}
	else{
		sum.feature.dataframe <- compute.features(dir=analysis.melodies,output=comp.feat.output,use.segmentation=comp.feat.use.seg)}
		
	if(corpus[1]==analysis.melodies[1]){
		sum.feature.dens.list <- compute.freqs.from.features(sum.feature.dataframe,returns="dens.list")
		densities.dataframe <- compute.freqs.from.features(sum.feature.dataframe,takes=sum.feature.dens.list)}
	else{
		if((substring(corpus[1],nchar(corpus)-3,nchar(corpus)-3)) != ".") {
			sum.feature.dens.list <- compute.freqs.from.features(compute.features(dir=corpus,output=comp.feat.output,use.segmentation=comp.feat.use.seg),returns="dens.list")
			densities.dataframe <- compute.freqs.from.features(sum.feature.dataframe,takes=sum.feature.dens.list)}
		else{
			value <- try(read.table(file=corpus,header=TRUE,sep="\t"))
			if(class(value) != "try-error") {
				sum.feature.dens.list <- compute.freqs.from.features(value,returns="dens.list")
				densities.dataframe <- compute.freqs.from.features(sum.feature.dataframe,takes=sum.feature.dens.list)}			else{
				load(corpus)
				densities.dataframe <- compute.freqs.from.features(sum.feature.dataframe,takes=sum.feature.dens.list)
			}
		}
	}
	if(write.out.corp.freq==TRUE) {
		save(sum.feature.dens.list, file="feature_densities_list.txt")
	write.table(densities.dataframe,file="densities_of_feature_values.txt",sep="\t",row.names=FALSE)}
	else{}
	densities.dataframe
	}


	
compute.m.type.corpus.based.features <- function(analysis.melodies,ana.dir=".",corpus,corpus.dir="."){
	source("M-Type_Corpus_Features.R")
	
	#print(analysis.melodies)
	if(ana.dir!=".") {
		if(substr(ana.dir,1,1) != .Platform$file.sep) {
			mel.fns <- file.path(getwd(),ana.dir,analysis.melodies)}
		else{
			mel.fns <- file.path(ana.dir,analysis.melodies)}
		}
	else{mel.fns <- list.files(pattern=".csv")}
	
	if((corpus[1]==analysis.melodies[1]) && (ana.dir == corpus.dir)) {
		corp.ngrams.tab <- n.grams.across.melodies(melody.filenames=mel.fns,n.lim=n.limits,phr.length.lim=phr.length.limits,write.out=TRUE)
		}
	else{
		if(substr(corpus[1],nchar(corpus[1])-3,nchar(corpus[1]))==".txt") {
			corp.ngrams.tab <- read.table(corpus,header=TRUE,sep="\t")}
		else{corp.mel.fns <- file.path(corpus.dir,corpus)
			corp.ngrams.tab <- n.grams.across.melodies(melody.filenames=corp.mel.fns,n.lim=n.limits,phr.length.lim=phr.length.limits,write.out=TRUE)}
		}	
	
	corp.ngrams.tab.full <- corp.ngrams.tab
	corp.ngrams.tab$count <- 1
	file.id <- NULL
	results <- NULL
	for(i in seq(along=mel.fns)) {
		fn.split <- strsplit(mel.fns[i],.Platform$file.sep)[[1]]
		file.id[i] <- substring(fn.split[length(fn.split)],1,nchar(fn.split[length(fn.split)])-4)
		print(file.id[i])
		temp.results <- compute.stat.ngram.feat.from.melody(corp.ngrams.tab,corp.ngrams.tab.full,mel.fns[i])
		results <- rbind(results,temp.results)
		}
	res.tab <- data.frame(file.id=file.id,results)
	write.table(res.tab,file="mtype_corpus_based_features.txt",sep="\t",row.names=FALSE)
	res.tab
	
	}
	
	

feature.similarity <- function(mel.fns=list.files(path=dir,pattern=".csv"),dir=".",features=c("p.range","step.cont.glob.var","tonalness","d.eq.trans"),use.segmentation=FALSE,method="euclidean",eucl.stand=TRUE,corpus.dens.list.fn=NULL,average=TRUE){
	# next line moved to the top of the file as this 
  # fixes an issue with rpy2
	#source("Feature_Similarity.R")
	require(cluster)
	mel.feat <- compute.features(melody.filenames=mel.fns,dir=dir,output="melody.wise",use.segmentation=use.segmentation)
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