#### Feature-based similarity ###


compute.sim <- function(mel.feat.new,feature,rows,method,eucl.stand,corpus.dens.list.fn){
	
	mel.feat.new <- data.frame(feature=mel.feat.new)
	colnames(mel.feat.new) <- feature
	rownames(mel.feat.new) <- rows
	if(method=="gower"){sim <- 1- daisy(mel.feat.new, metric="gower")}
	else{}
	
	if(method=="euclidean"){
		if(eucl.stand==TRUE){mel.feat.new <- ztransform(mel.feat.new)}
		else{}
		sim <- exp(-dist(mel.feat.new)/length(feature))}
	else{}
	
	if(method=="corpus"){
		sim <- corpus.similarity(mel.feat.new,corpus.dens.list.fn)}
	else{}
	sim
}

corpus.similarity <- function(df,corpus.dens.fn){
	load(corpus.dens.fn)
	combn.matrix <- combn(rownames(df),2)
	dist.mat <- NULL
	weights <- NULL
	for(i in seq(along=colnames(df))) {
		feature <- colnames(df)[i]
		
		if(is.matrix(sum.feature.dens.list[[feature]]) || is.data.frame(sum.feature.dens.list[[feature]])){
			dens.mat <- as.matrix(sum.feature.dens.list[[feature]])
			weights[feature] <- compute.entropy.from.table(dens.mat)
			
			tmp.mat <- matrix(nrow=length(df[,1]),ncol=length(df[,1]),dimnames=list(rownames(df),rownames(df)))
			r.ind <- 2
			c.ind <- 1
			for(j in 1:(length(combn.matrix)/2)) {
				x.mel1 <- which(abs(dens.mat[,1]-df[combn.matrix[1,j],feature]) == min(abs(dens.mat[,1]-df[combn.matrix[1,j],feature])))
				x.mel2 <- which(abs(dens.mat[,1]-df[combn.matrix[2,j],feature]) == min(abs(dens.mat[,1]-df[combn.matrix[2,j],feature])))
				tmp.mat[r.ind,c.ind] <- 1-(abs(cumsum(dens.mat[1:x.mel1,2])[x.mel1] - cumsum(dens.mat[1:x.mel2,2])[x.mel2])/cumsum(dens.mat[,2])[length(dens.mat[,2])])
				if(r.ind==c.ind+1) {
					r.ind <- r.ind+1
					c.ind <- 1}
				else{c.ind <- c.ind+1}
				}
			dist.mat[[feature]] <- tmp.mat	
			}
		else{
			freq.tab <- sum.feature.dens.list[[feature]]
			weights[feature] <- compute.entropy.from.table(freq.tab)
			tmp.mat <- matrix(nrow=length(df[,1]),ncol=length(df[,1]),dimnames=list(rownames(df),rownames(df)))
			r.ind <- 2
			c.ind <- 1
			for(j in 1:(length(combn.matrix)/2)) {
				if(df[combn.matrix[1,j],feature]==df[combn.matrix[2,j],feature]){tmp.mat[r.ind,c.ind] <- 1}
				else{tmp.mat[r.ind,c.ind] <- 0}
				if(r.ind==c.ind+1) {
					r.ind <- r.ind+1
					c.ind <- 1}
				else{c.ind <- c.ind+1}
				}
			dist.mat[[feature]] <- tmp.mat
		}
	}
	for(i in 1:(11-length(colnames(df)))){
		dist.mat[[paste("dummy",i)]] <- matrix(0,nrow=length(df[,1]),ncol=length(df[,1]))
		weights[paste("dummy",i)] <- 0}
	print(weights)
	print(sum(weights))
	mean.dist.mat <- matrix(mapply(sum,weights[1]*dist.mat[[1]],weights[2]*dist.mat[[2]],weights[3]*dist.mat[[3]],weights[4]*dist.mat[[4]],weights[5]*dist.mat[[5]],weights[6]*dist.mat[[6]],weights[7]*dist.mat[[7]],weights[8]*dist.mat[[8]],weights[9]*dist.mat[[9]],weights[10]*dist.mat[[10]])/sum(weights),nrow=length(df[,1]),ncol=length(df[,1]),dimnames=list(rownames(df),rownames(df)))
	mean.dist.mat <- as.dist(mean.dist.mat) 
}

extract.pair.sim <- function(sim.mat.list){
	items <- labels(sim.mat.list[[1]])
	file.a <- items[seq(1,length(items),2)]
	file.b <- items[seq(2,length(items),2)]
	results <- data.frame(file.a,file.b)
	for(i in seq(along=sim.mat.list)){
		sim.mat <- sim.mat.list[[i]]
		dist.mat <- as.matrix(sim.mat)
		similarity <- vector(mode="numeric",length=length(file.a))
		for(j in seq(along=file.a)){
			similarity[j] <- dist.mat[2*j,(2*j)-1]
			}
		results <- data.frame(results,similarity)
		colnames(results)[length(colnames(results))] <- paste(names(sim.mat.list)[i],"similarity",sep=".")
		}
	results 
	}

ztransform <- function(df) {

	for(i in 1:length(colnames(df))){
		if(class(df[,i])=="integer"||class(df[,i])=="numeric") {
			df[,i] <- (df[,i]-mean(df[,i],na.rm=TRUE)) /  (sqrt(var(df[,i],na.rm=TRUE))+0.0000001)
			}
		else{df[,i] <- df[,i]}	
		}
	df
	}

compute.entropy.from.table <- function(freq.table){
	if(is.table(freq.table)){
		frequencies <- as.vector(freq.table)
		}
	else{
		frequencies <- freq.table[,2] / sum(freq.table[,2])
		frequencies <- frequencies[frequencies>0]
		}
	entropy <- -(sum(frequencies*logb(frequencies,2))) / logb(length(frequencies),2)
	
	}