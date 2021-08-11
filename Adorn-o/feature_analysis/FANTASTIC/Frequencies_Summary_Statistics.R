m.type.features <- c("mean.entropy","mean.productivity","mean.Simpsons.D","mean.Yules.K","mean.Sichels.S","mean.Honores.H")
discrete.features <- c("p.range","i.abs.range","i.mode","d.mode","len","int.cont.glob.dir","int.cont.dir.change")
multidim.features <- c("poly.coeff1","poly.coeff2","poly.coeff3")
retained.vars <- c("file.id","phr.id")
ul.p.range <- 36
ul.glob.duration <- 10

compute.freqs.from.features <- function(feature.data.frame,excluded.features=m.type.features,disc.features=discrete.features,multi.dim.features=multidim.features,retained.variables=retained.vars,returns="densities",takes="no.dens.list") {
		retained.col.ind <- sapply(retained.variables, function(x) which(colnames(feature.data.frame)==x))
		retained.col.ind <- na.exclude(as.numeric(retained.col.ind))
		names.ret.vars <- colnames(feature.data.frame)[retained.col.ind]
		excluded.col.ind <- sapply(excluded.features, function(x) which(colnames(feature.data.frame)==x))
		excluded.col.ind <- na.exclude(as.numeric(excluded.col.ind))
		multidim.col.ind <- sapply(multi.dim.features, function(x) which(colnames(feature.data.frame)==x))
		multidim.col.ind <- na.exclude(as.numeric(multidim.col.ind))
		discfeat.col.ind <- sapply(disc.features, function(x) which(colnames(feature.data.frame)==x))
		discfeat.col.ind <- na.exclude(as.numeric(discfeat.col.ind))
		tmp <- as.numeric(c(retained.col.ind,excluded.col.ind,multidim.col.ind,discfeat.col.ind))
		numeric.cols <- feature.data.frame[,-tmp]
		numeric.cols <- numeric.cols[,which(sapply(numeric.cols,is.numeric))]
		factor.cols <- feature.data.frame[,-tmp]
		factor.cols <- factor.cols[,which(sapply(factor.cols,is.factor))]
		
		rm(tmp)
	
	if(class(takes) == "character"){
		dens.list <- compute.feat.dens(numeric.cols,factor.cols,feature.data.frame[,disc.features],feature.data.frame[,multidim.col.ind])
		}
	else{dens.list <- takes}
	if(returns=="dens.list") {return(invisible(dens.list))}
	else{
		densities <- replace.val.dens(numeric.cols,factor.cols,feature.data.frame[,disc.features],feature.data.frame[,retained.col.ind],names.ret.vars,dens.list)}
	}


compute.feat.dens <- function(unidim.feat.df,fac.feat.df,disc.feat.df,multidim.feat.df) {
	#require(KernSmooth)
	unidim.feat.df <- unidim.feat.df[disc.feat.df$p.range<= ul.p.range,]
	unidim.feat.df <- unidim.feat.df[unidim.feat.df$glob.duration<=ul.glob.duration,]
	disc.feat.df <- disc.feat.df[disc.feat.df$p.range<= ul.p.range,]
	disc.feat.df <- disc.feat.df[unidim.feat.df$glob.duration<=ul.glob.duration,]
	
	dens.num.feat <- lapply(unidim.feat.df, function (z) {
		z <- na.exclude(z)
		tmp <- density((z-mean(z))/sqrt(var(z))) 
		cbind(sqrt(var(z))*tmp$x+mean(z),tmp$y)})
	
	#dens.multidim.feat <- NULL
	#dens.multidim.feat[["poly.coeff"]] <- function(z) {
		#tmp <- kde2d(multidim.feat.df[,1],multidim.feat.df[,2])$z
		#cbind(tmp$x,tmp$y,tmp$z)}
	
	dens.cat.feat <- lapply(fac.feat.df,function (x) table(x)/sum(table(x)))
	dens.disc.feat <- lapply(disc.feat.df,function (x) {
		tab <- as.data.frame(table(x)/sum(table(x)))
		tab[,1] <- as.numeric(levels(tab[,1]))
		tab})
	feat.dens <- list(dens.num.feat,dens.cat.feat,dens.disc.feat)
	feat.dens <- unlist(feat.dens,recursive=FALSE)
	}
	
replace.val.dens <- function(unidim.feat.df,fac.feat.df,disc.feat.df,retained.vars, colnames.ret.vars,dens.list) {
	dens.df <- data.frame(retained.vars)
	colnames(dens.df) <- colnames.ret.vars
	
	h <- length(colnames(dens.df))
	for(i in seq(along=colnames(unidim.feat.df))){
		fname <- colnames(unidim.feat.df)[i] 
		feature <- unidim.feat.df[,fname]
		dens.df[,h+i] <- unlist(sapply(feature, function (x) dens.list[[fname]][which(abs(dens.list[[fname]][,1] - x ) == min(abs(dens.list[[fname]][,1] - x)))[1],2]))
		colnames(dens.df)[h+i] <- paste("dens",fname,sep=".")
		}
	j <- length(colnames(dens.df))
	for(i in seq(along=colnames(fac.feat.df))) {
		fname <- colnames(fac.feat.df)[i] 
		feature <- fac.feat.df[,fname]
		dens.df[,i+j] <- unlist(sapply(feature, function (x) dens.list[[fname]][x]))
		colnames(dens.df)[i+j] <- paste("dens",fname,sep=".")
		}
	
	k <- length(colnames(dens.df))
	for(i in seq(along=colnames(disc.feat.df))){
		fname <- colnames(disc.feat.df)[i] 
		feature <- as.numeric(disc.feat.df[,fname])
		dens.df[,k+i] <- unlist(sapply(feature, function (x) dens.list[[fname]][which(abs(dens.list[[fname]][,1] - x ) == min(abs(dens.list[[fname]][,1] - x)))[1],2]))
		colnames(dens.df)[k+i] <- paste("dens",fname,sep=".")
		}
	
	#for(i in seq(along=colnames(multidim.feat.df))) {
	#	k <- length(colnames(retained.vars))+length(colnames(unidim.feat.df))+length(colnames(fac.feat.df))
		#dens.df[,i+k] <- dens.list[["poly.coeff"]][which(abs(dens.list[["poly.coeff"]][,1] - x ) == min(abs(dens.list[["poly.coeff"]][,1] - x)))[1],2]))
		#}	
	dens.df	
	}

