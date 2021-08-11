
compute.stat.ngram.feat.from.melody <- function(corp.ngrams.tab,corp.ngrams.tab.full,melody.fn) {
	
	mel.ngrams.tab <- n.grams.from.melody.main(melody.fn)
	DFs <- tapply(corp.ngrams.tab$count, corp.ngrams.tab$ngram, sum)
	DFs <- data.frame(ngram=names(DFs),corpus.count=DFs)
	TFDF.tab <- merge(mel.ngrams.tab,DFs)
	IDFs <- length(levels(as.factor(corp.ngrams.tab$file.id))) / TFDF.tab$corpus.count
	TFDF.tab <- data.frame(TFDF.tab,corpus.IDFs=IDFs)
	TFDF.tab <- data.frame(TFDF.tab, TFIDFs=round(TFDF.tab$corpus.IDF)*TFDF.tab$count)
	TFDF.spearman <- cor(rank(TFDF.tab$count, ties.method="min"),rank(TFDF.tab$corpus.count,ties.method="min"),method="spearman")
	TFDF.kendall <- cor(rank(TFDF.tab$count,ties.method="min"),rank(TFDF.tab$corpus.count,ties.method="min"),method="kendall")
	normalised.TF <- logb(TFDF.tab$count,2)/sum(logb(TFDF.tab$count,2))
	normalised.DF <- logb(TFDF.tab$corpus.count,2)/sum(logb(TFDF.tab$corpus.count,2))
	mean.log.TFDF <- mean(normalised.TF*normalised.DF)
	norm.log.dist <- sum(abs(normalised.TF-normalised.DF)) / length(normalised.TF)
	log.max.DF <- logb(max(TFDF.tab$corpus.count),2)
	log.min.DF <- logb(min(TFDF.tab$corpus.count),2)
	mean.log.DF <- mean(logb(TFDF.tab$corpus.count,2))
	col.ngram.tab.DFs <- data.frame(ngram=TFDF.tab$ngram,count=TFDF.tab$corpus.count)
	
	DF.ngram.features <- compute.features.from.ngram.table.main(col.ngram.tab.DFs)
	col.ngram.tab.TFIDFs <- data.frame(ngram=TFDF.tab$ngram,count=TFDF.tab$TFIDFs)
	
	TFIDF.ngram.features <- compute.features.from.ngram.table.main(col.ngram.tab.TFIDFs)
	TFIDF.ngram.features <- data.frame(TFIDF.m.entropy=TFIDF.ngram.features$mean.entropy,TFIDF.m.K=TFIDF.ngram.features$mean.Yules.K,TFIDF.m.D=TFIDF.ngram.features$mean.Simpsons.D)
	
	local.weight <- logb((mel.ngrams.tab$count+1),2)
	glob.weights <- compute.glob.weights(mel.ngrams.tab,corp.ngrams.tab.full)
	mean.gl.weight <- mean(glob.weights*local.weight)
	std.gl.weight <- sqrt(var(glob.weights*local.weight))
	mean.g.weight <- mean(glob.weights)
	std.g.weight <- sqrt(var(glob.weights))
	
	results <- data.frame(TFDF.spearman,TFDF.kendall,mean.log.TFDF,norm.log.dist,log.max.DF,log.min.DF,mean.log.DF,mean.g.weight, std.g.weight,mean.gl.weight,std.gl.weight,DF.ngram.features,TFIDF.ngram.features)
	colnames(results) <- paste("mtcf",colnames(results),sep=".")
	results
	}
	

compute.glob.weights <- function(melody.ngrams.tab,corpus.ngrams.tab) {
	## see Quesada (2007, 80-81) ##

	global.freqs <- tapply(corpus.ngrams.tab$count, corpus.ngrams.tab$ngram, sum)
	gweight <- vector(mode="numeric",length=length(melody.ngrams.tab$ngram))

	for(i in seq(along=melody.ngrams.tab$ngram)) {
		local.Freq <- corpus.ngrams.tab$count[corpus.ngrams.tab$ngram==as.character(melody.ngrams.tab$ngram[i])]
		p <- local.Freq / global.freqs[as.character(melody.ngrams.tab$ngram[i])]
		lp <- logb(p,2)
		p <- sum(p*lp)
		gweight[i] <- 1 + (p / logb(length(levels(as.factor(corpus.ngrams.tab$file.id))),2))
		} 
	gweight
}



compute.features.from.ngram.table.main <- function(collapsed.ngram.table) {
	n.gr.lengths <- sapply(as.character(collapsed.ngram.table$ngram), function(x) 1+nchar(x)%/%4)
	min.n <- min(n.gr.lengths)
	max.n <- max(n.gr.lengths)
	
	m.entropy <- compute.m.ngram.entropy(collapsed.ngram.table,n.gr.lengths,min.n,max.n)
	#m.tf <- compute.m.tf(collapsed.ngram.table,n.gr.lengths,min.n,max.n)
	#m.mprob <- compute.m.max.prob(collapsed.ngram.table,n.gr.lengths,min.n,max.n)
	m.prod <- compute.m.productivity(collapsed.ngram.table,n.gr.lengths,min.n,max.n)
	m.D <- compute.simpsons.d(collapsed.ngram.table,n.gr.lengths,min.n,max.n)
	m.K <- compute.yules.k(collapsed.ngram.table,n.gr.lengths,min.n,max.n)
	m.S <- compute.sichels.s(collapsed.ngram.table,n.gr.lengths,min.n,max.n)
	m.H <- compute.honores.h(collapsed.ngram.table,n.gr.lengths,min.n,max.n)
	features <- data.frame(mean.entropy=m.entropy, mean.productivity=m.prod, mean.Simpsons.D=m.D, mean.Yules.K=m.K, mean.Sichels.S=m.S, mean.Honores.H=m.H)
	
	}

n.grams.across.melodies <- function(melody.filenames,n.lim=n.limits,phr.length.lim=phr.length.limits,write.out=FALSE) {
	ngr.tab <- NULL
	for(i in seq(along=melody.filenames)) {
		file.id <- substr(melody.filenames[i],1,nchar(melody.filenames[i])-4)
		print(file.id)
		ngr.mel.tab.collapsed <- n.grams.from.melody.main(melody.filenames[i],n.lim,phr.length.lim)
		if(any(is.na(ngr.mel.tab.collapsed))) next 
		ngr.tab.temp <- data.frame(file.id=file.id,ngr.mel.tab.collapsed)
		ngr.tab <- rbind(ngr.tab,ngr.tab.temp)
		}
	if(write.out==TRUE) {write.table(ngr.tab,file="m-type_counts_several_melodies.txt",sep="\t",row.names=FALSE)}
	ngr.tab
	}

write.both <- function(comb.ngr.tab.collapsed,ngr.tab) {
	write.table(comb.ngr.tab.collapsed,file="m-type_counts_several_melodies_collapsed.csv",sep=";",row.names=FALSE)
	write.table(ngr.tab,file="m-type_counts_several_melodies.csv",sep=";",row.names=FALSE)}

n.grams.from.phrase <- function(phrase.data,n.lim=n.limits,phr.length.lim=phr.length.limits) {
	phr <- list(NA,phrase.data)
	diff.phr <- diff.transform(phr)
	class.diff.phr <- class.transform(diff.phr)
	ngram.phr <- create.ngram.hash(class.diff.phr)
	ngrams.phr.tab <- count.ngrams.in.melody(ngram.phr,n.lim[1],n.lim[2])
	ngrams.phr.tab <- data.frame(ngram=ngrams.phr.tab$ngrams,count=ngrams.phr.tab$Freq)
	rownames(ngrams.phr.tab) <- NULL
	ngrams.phr.tab
	}

n.grams.from.melody.main <- function(melody.filename,n.lim=n.limits,phr.length.lim=phr.length.limits,write.out=FALSE) {
	file.id <- substr(melody.filename,1,nchar(melody.filename)-4)
	phr.list <- make.phrases.from.melody(melody.filename,file.id)
	#print(phr.list)
	excludes <- make.excludes(phr.length.lim,phr.list)
	if(length(excludes) >= length(phr.list)) {
		ngrams.mel.tab.collapsed <- NA
		ngrams.mel.tabs <- NA}
	else{
		diff.phr.list <- diff.transform(phr.list[-excludes])
		class.diff.phr.list <- class.transform(diff.phr.list)
		ngram.phr.list <- create.ngram.hash(class.diff.phr.list)
		ngrams.mel.tab <- count.ngrams.in.melody(ngram.phr.list,n.lim[1],n.lim[2])
		ngrams.mel.tab.collapsed <- tapply(ngrams.mel.tab$Freq, ngrams.mel.tab$ngram, sum)
		ngrams.mel.tab.collapsed <- data.frame(ngram=names(ngrams.mel.tab.collapsed),count=ngrams.mel.tab.collapsed)
		rownames(ngrams.mel.tab.collapsed) <- NULL
		switch(write.out, collapsed=write.table(ngrams.mel.tab.collapsed,file=paste(file.id,"ngram_counts_collapsed.csv",sep="-"),sep=";",row.names=FALSE), full=write.table(ngrams.mel.tab,file=paste(file.id,"ngram_counts.csv",sep="-"), sep=";",row.names=FALSE))
		}
	ngrams.mel.tab.collapsed
	
	
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
	

count.ngrams.in.melody <- function(ngram.phr.list,min.n,max.n) {
	full.table <- NULL
	for(i in 1:(length(ngram.phr.list)-1)) {
		phrase.ngrams <- unlist(ngram.phr.list[[i+1]]["p.tr.hash"])
		ngram.table <- NULL
		for(j in min.n:min(max.n, length(phrase.ngrams))){
			ngrams <- vector(mode="character",length=(length(phrase.ngrams)-j+1))
			for(k in 1:(length(phrase.ngrams)-j+1)){
				ngram.set <- phrase.ngrams[k:(k+j-1)]
				ngrams[k] <- paste(ngram.set,collapse = "_")
				}
			current.ngrams <- table(ngrams)
			current.ngrams <- data.frame(n=j,current.ngrams)
			#print(current.ngrams)
			ngram.table <- data.frame(rbind(ngram.table,current.ngrams))
			#print(ngram.table)
			}
	ngram.table <- data.frame(phr=i,ngram.table)
	full.table <- data.frame(rbind(full.table,ngram.table))
	
	}
	row.names(full.table) <- NULL
	full.table
}

create.ngram.hash <- function(class.diff.phr.list) {
	out.list <- class.diff.phr.list
	for(i in 1:(length(out.list)-1)) {
		out.list[[i+1]][,19] <- as.vector(mapply(function(x,y) paste(x,y,sep=""), out.list[[i+1]]["pitch"],out.list[[i+1]]["tr_durs"],USE.NAMES=FALSE)) 
		colnames(out.list[[i+1]])[19] <- "p.tr.hash"
		}
	out.list
	}

diff.transform <- function(phrases.list) {
	#print(str(phrases.list))
	diff.transf.phr.list <- phrases.list
	for(i in 1:(length(phrases.list)-1)) {
		#print(i)
		diff.transf.phr.list[[i+1]] <- apply(phrases.list[[i+1]],2,diff)
		diff.transf.phr.list[[i+1]] <- data.frame(diff.transf.phr.list[[i+1]],tr_durs=NA,tr_durtic=NA,tr_dur16=NA)
		diff.transf.phr.list[[i+1]][,16:18] <- apply(phrases.list[[i+1]][,7:9],2, ratio)
		}
	diff.transf.phr.list
	}

class.transform <- function(diff.transf.phr.list) {
	diff.class.transf.phr.list <- diff.transf.phr.list
	for(i in 1:(length(diff.transf.phr.list)-1)) {
		diff.class.transf.phr.list[[i+1]]["pitch"] <-  sapply(unlist(diff.class.transf.phr.list[[i+1]]["pitch"]), function(x) p.classify(x,int.class.scheme))
		diff.class.transf.phr.list[[i+1]]["tr_durs"] <- sapply(unlist(diff.class.transf.phr.list[[i+1]]["tr_durs"]), function(x) tr.classify(x,tr.class.scheme))
		diff.class.transf.phr.list[[i+1]]["tr_durtic"] <- sapply(unlist(diff.class.transf.phr.list[[i+1]]["tr_durtic"]), function(x) tr.classify(x,tr.class.scheme))
		diff.class.transf.phr.list[[i+1]]["tr_dur16"] <- sapply(unlist(diff.class.transf.phr.list[[i+1]]["tr_dur16"]), function(x) tr.classify(x,tr.class.scheme))
		}
	diff.class.transf.phr.list
	}




	
	
ratio <- function(vec) {
	vec[2:length(vec)] / vec[1:(length(vec)-1)]}
	
write.csv <- function(melody.list) {
	phrase.pitches <- mel.data$pitch[start:end]
				onset <- mel.data$onset[start:end]
				phrase.onsets <- onset - onset[1]
				phrase.id <- paste(substr(melody.filename,1,nchar(melody.filename)-4),i,sep="-")
				out.file <- file(paste("ph_",i,".file_",file.id,".csv",sep=""),"w")
				cat(firstline, file=out.file, sep="\n")
			cat(colnames(mel.data), file=out.file, sep=";")
			cat("\n", file=out.file)
	
	}

tr.classify <- function(tr,class.scheme) {
	dif <- vector(mode="numeric",length=length(class.scheme))
	mod <- vector(mode="numeric",length=length(class.scheme))
	for(i in seq(along=class.scheme)) {
		dif[i] <- class.scheme[["upper.limits"]][i] - tr
		mod[i] <- tr%/%class.scheme[["upper.limits"]][i]
		}
	if(any(dif>0)) {
		class <- tr.class.scheme[["class.symbols"]][which(mod==min(mod[which(dif>0)]))[1]]}
	else{class <- tr.class.scheme[["class.symbols"]][length(tr.class.scheme[["class.symbols"]])]}
	
	}
	
p.classify <- function(p.int,class.scheme){
	if(p.int<class.scheme$raw.int[1]) {class <- "dl"}
	else{
		if(p.int>class.scheme$raw.int[length(class.scheme$raw.int)]){class <- "ul"}
		else{
			class <- class.scheme$class.int[class.scheme$raw.int==p.int]
			}
		}
	class <- as.character(class)
	}
	
make.excludes <- function(phr.length.lim,phrase.list) {
	phr.lengths <- count.phrase.length(phrase.list)
	excludes <- which(phr.lengths[2:length(phr.lengths)]<=phr.length.lim[1] | phr.lengths[2:length(phr.lengths)]>=phr.length.lim[2])
	excludes <- excludes+1
	excludes <- append(excludes,length(phr.lengths)+1)
	}

count.phrase.length <- function(phrase.list) {
	phrase.lengths <- vector(mode="numeric", length=length(phrase.list)-1)
	phrase.lengths <- sapply(phrase.list[1:length(phrase.list)], function(x) length(x[[1]]))
	}

compute.m.productivity <- function(collapsed.ngram.table,n.gr.lengths,min.n,max.n) {
	prod <- NULL
	weight <- NULL
	n.1grams <- sum(collapsed.ngram.table$count[n.gr.lengths == 1])
	for(i in min.n:max.n) {
		tab <- collapsed.ngram.table$count[n.gr.lengths == i]
		prod[i] <- sum(tab[tab==1]) / sum(tab)
		#weight[i] <- n.1grams / sum(tab)
		#prod[i] <- prod[i]*(1/weight[i])
	}
	#mean.prod <- sum(prod) / sum(weight)
	mean.prod <- mean(prod)
	}

compute.m.max.prob <- function(collapsed.ngram.table,n.gr.lengths,min.n,max.n) {
	max.prob <- NULL
	for(i in min.n:max.n) {
		tab <- collapsed.ngram.table$count[n.gr.lengths == i]
		normal.tab <- tab / sum(tab)
		max.prob[i] <- max(normal.tab)
		}
	mean.max.prob <- mean(max.prob)
}

compute.m.ngram.entropy <- function(collapsed.ngram.table,n.gr.lengths,min.n,max.n) {
	entropy <- NULL
	for(i in min.n:max.n) {
		tab <- collapsed.ngram.table$count[n.gr.lengths == i]
		normal.tab <- tab / sum(tab)
		if(sum(tab)==1) {entropy[i] <- 0}
		else{entropy[i] <- -(sum(normal.tab*logb(normal.tab,2))) / logb(sum(tab),2)}
	}
	mean.entropy <- mean(entropy)
}

compute.m.tf <- function(collapsed.ngram.table,n.gr.lengths,min.n,max.n) {
	tf <- NULL
	weight <- NULL
	n.1grams <- sum(collapsed.ngram.table$count[n.gr.lengths == 1])
	for(i in min.n:max.n) {
		tab <- collapsed.ngram.table$count[n.gr.lengths == i]
		tf[i] <- mean(tab) / sum(tab)
		#weight[i] <- n.1grams / sum(tab)
		#tf[i] <- tf[i]*weight[i]
		}
	#mean.tf <- sum(tf) / sum(weight)
	mean.tf <- mean(tf)
		
	}

make.spc <- function(collapsed.ngram.table) {
	tab <- table(collapsed.ngram.table$count)
	#print(tab)
	tab <- data.frame(m=as.numeric(rownames(tab)),Vm=as.vector(tab))
	}
	
compute.simpsons.d <- function(collapsed.ngram.table,n.gr.lengths,min.n,max.n) {
	sum.D <- vector(mode="numeric",length=max.n-min.n+1)
	for(i in min.n:max.n) {
		freq.spc <- make.spc(collapsed.ngram.table[n.gr.lengths==i,])
		N <- sum(freq.spc$m*freq.spc$Vm)
		if(N==1) {
			sum.D <- 0}
		else{
			D <- vector(mode="numeric",length=length(freq.spc$m))
			for(j in seq(along=freq.spc$m)) {
				D[j] <- freq.spc$Vm[j]*(j/N)*((j-1)/(N-1))
				}
			sum.D[i] <- sum(D)
		}
	}
	m.D <- mean(sum.D)
	}
	
compute.yules.k <- function(collapsed.ngram.table,n.gr.lengths,min.n,max.n) {
	K <- vector(mode="numeric",length=max.n-min.n+1)
	for(i in min.n:max.n) {
		freq.spc <- make.spc(collapsed.ngram.table[n.gr.lengths==i,])
		N <- sum(freq.spc$m*freq.spc$Vm)
		denom.K <- vector(mode="numeric",length=length(freq.spc$m))
		for(j in seq(along=freq.spc$m)) {
			denom.K[j] <- freq.spc$Vm[j]*j^2
			}
		K[i] <- 10000*((sum(denom.K)-N)/N^2)
	}
	m.K <- mean(K)
	}

compute.sichels.s <- function(collapsed.ngram.table,n.gr.lengths,min.n,max.n) {
	S <- vector(mode="numeric",length=max.n-min.n+1)
	for(i in min.n:max.n) {
		freq.spc <- make.spc(collapsed.ngram.table[n.gr.lengths==i,])
		if(length(freq.spc[freq.spc$m==2,2])<1) {
			S[i] <- 0}
		else{
			S[i] <- freq.spc[freq.spc$m==2,2] / sum(freq.spc$Vm)}
		}
	m.S <- mean(S)	
	}
	
compute.honores.h <- function(collapsed.ngram.table,n.gr.lengths,min.n,max.n) {
	H <- vector(mode="numeric",length=max.n-min.n+1)
	for(i in min.n:max.n) {
		freq.spc <- make.spc(collapsed.ngram.table[n.gr.lengths==i,])
		if(length(freq.spc[freq.spc$m==1,2])<1) {
			H[i] <- 0}
		else{
			N <- sum(freq.spc$m*freq.spc$Vm)
			H[i] <- 100*( log(N) / 1-(freq.spc[freq.spc$m==1,2]/sum(freq.spc$Vm)))
			}
		}
	m.H <- mean(H)	
	}
	
compute.zipfs.z <- function(collapsed.ngram.table) {
	n.gr.lengths <- sapply(as.character(collapsed.ngram.table$ngram), function(x) 1+nchar(x)%/%4)
	min.n <- min(n.gr.lengths)
	max.n <- max(n.gr.lengths)
	require(zipfR)
	Z <- vector(mode="numeric",length=max.n-min.n+1)
	N <- vector(mode="numeric",length=max.n-min.n+1)
	for(i in min.n:max.n) {
		freq.spc <- make.spc(collapsed.ngram.table[n.gr.lengths==i,])
		N[i] <- sum(freq.spc$m*freq.spc$Vm)
		freq.spc <- spc(freq.spc$Vm)
		if(length(freq.spc[freq.spc$m==1,2])<1) {
			Z[i] <- NA}
		else{
			Z[i] <- lnre("gigp",freq.spc)$param2$Z
			Z[i] <- Z[i]
			}
		}
	print(N)
	print(Z)
	m.Z <- mean(Z,na.rm=TRUE)			
	}

