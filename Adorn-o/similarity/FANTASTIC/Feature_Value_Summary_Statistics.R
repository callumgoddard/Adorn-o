## Phrase Summary Features ##

maj.vector <- c(6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88)
min.vector <- c(6.33,2.68,3.52,5.38,2.6,3.53,2.54,4.75,3.98,2.69,3.34,3.17)


summary.phr.features <- function(phr.data,poly.contour=TRUE){
	phr.data <- phr.data[,1:9]

	pitch <- as.numeric(phr.data$pitch)
	onset <- as.numeric(phr.data$onset)
	durs <- as.numeric(phr.data$durs)
	dur16 <- as.numeric(phr.data$dur16)
	
	p.min <- min(pitch)
	p.max <- max(pitch)
	p.range <- p.max - p.min
	#p.mean <- mean(pitch)
	p.std <- sqrt(var(pitch))
	p.entropy <- compute.entropy(pitch,phr.length.limits[2])
	#p.results <- data.frame(p.min,p.max,p.range,p.var,p.mean,p.entropy)
	p.results <- data.frame(p.range,p.entropy,p.std)
	
	intervals <- pitch[2:length(pitch)] - pitch[1:length(pitch)-1]
	#i.min <- min(intervals)
	#i.max <- max(intervals)
	#i.range <- i.max - i.min
	i.abs.range <- max(abs(intervals)) - min(abs(intervals))
	#i.mean <- mean(intervals)
	i.abs.mean <- mean(abs(intervals))
	#i.median <- median(intervals)
	#i.abs.median <- median(abs(intervals))
	i.abs.std <- sqrt(var(abs(intervals)))
	i.modes <- which(table(intervals) == max(table(intervals)))
	i.mode <- i.modes[length(i.modes)]
	#i.var <- var(intervals)
	i.entropy <- compute.entropy(intervals,(phr.length.limits[2]-1))
	#i.results <- data.frame(i.min,i.max,i.range,i.abs.range,i.var,i.mean,i.abs.mean,i.median,i.abs.median,i.mode,i.entropy)
	i.results <- data.frame(i.abs.range,i.abs.mean,i.abs.std,i.mode,i.entropy)
	
	d.min <- min(durs)
	d.max <- max(durs)
	d.range <- d.max - d.min
	d.median <- median(dur16)
	d.modes <- which(table(dur16) == max(table(dur16)))
	d.mode <- d.modes[length(d.modes)]
	d.ratios <- round(dur16[1:length(dur16)-1]/ dur16[2:length(dur16)],2)
	d.eq.trans <- sum(sign(d.ratios[d.ratios==1])) / length(d.ratios)
	d.half.trans <- (sum(sign(d.ratios[d.ratios==0.5])) + sum(sign(d.ratios[round(d.ratios,0)==2]))) / length(d.ratios)
	d.dotted.trans <- (sum(sign(d.ratios[d.ratios==(1/3)])) + sum(sign(d.ratios[round(d.ratios,0)==3]))) / length(d.ratios)
	#d.var <- var(logb(dur16,2))
	d.entropy <- compute.entropy(dur16,phr.length.limits[2])
	#d.results <- data.frame(d.min,d.max,d.range,d.var,d.median,d.mode,d.entropy)
	d.results <- data.frame(d.range,d.median,d.mode,d.entropy,d.eq.trans,d.half.trans,d.dotted.trans)
	
	len <- length(pitch)
	glob.duration <- onset[length(onset)] - onset[1]
	note.dens <- len / glob.duration
	h.contour <- huron.contour(onset,pitch)
	#av.tf <- average.term.frequency(intervals,2,min(5,length(intervals)))
	#agg.results <- data.frame(len,glob.duration,note.dens,h.contour,av.tf)
	agg.results <- data.frame(len,glob.duration,note.dens)
	
	tonality.vector <- compute.tonality.vector(pitch,dur16,make.tonal.weights(maj.vector,min.vector))
	ton.results <- compute.tonal.features(tonality.vector)
	
	h.contour <- huron.contour(onset,pitch)
	
	int.contour.gradients <- line.contour(onset,pitch)
	int.contour <- compute.int.cont.feat(int.contour.gradients)
	
	step.contour.vector <- step.contour(pitch,dur16)
	step.contour <- compute.step.cont.feat(step.contour.vector)
	
	if(poly.contour==TRUE) {
		if(step.contour$step.cont.loc.var==0) {
			coeffs <- data.frame(poly.coeff1=0,poly.coeff2=0,poly.coeff3=0)}
		else{
			require(MASS)
			if((onset[length(onset)]-onset[1]) > 30) {
				coeffs <- data.frame(poly.coeff1=NA,poly.coeff2=NA,poly.coeff3=NA)}
			else{
				coeffs <- poly.contour(onset, pitch)
				coeffs <- data.frame(poly.coeff1=coeffs[1],poly.coeff2=coeffs[2],poly.coeff3=coeffs[3])}
			}
		con.results <- data.frame(h.contour,int.contour,step.contour,coeffs)			}
	else{
		con.results <- data.frame(h.contour,int.contour,step.contour)
		}
	results <- data.frame(p.results,i.results,d.results,agg.results,ton.results,con.results)

	
	rownames(results) <- NULL
	results
	
	}
compute.entropy <- function(integer.vector,alphabet.size=2) {
	tab <- table(integer.vector)
	normal.tab <- tab / sum(tab)
	entropy <- -(sum(normal.tab*logb(normal.tab,2))) / logb(alphabet.size,2)
	
	}
	
huron.contour <- function (onset, pitch) {
	contour.class <- vector(mode="character", length=1)
	reduced.pitch <- vector(mode="numeric", length = 3)
	reduced.onset <- c(1,2,3)
	first.pitch <- pitch[1]
	last.pitch <- pitch[length(pitch)]
	average.pitch <- round(mean(pitch[2:(length(pitch)-1)]))
	if(average.pitch > first.pitch){
		if(last.pitch < average.pitch){
			reduced.pitch <- c(0,1,0)
			contour.class <- "convex"}
		else{
			if(last.pitch == average.pitch){
				reduced.pitch <- c(0,1,1)
				contour.class <- "asc-horiz"}
			else{
				reduced.pitch <- c(-1,0,1)
				contour.class <- "ascending"}
			}
		}
	else{
		if(average.pitch == first.pitch) {
			if(last.pitch == average.pitch){
				reduced.pitch <- c(0,0,0)
				contour.class <- "horizontal"}
			else{
				if(last.pitch < average.pitch){
					reduced.pitch <- c(0,0,-1)
					contour.class <- "horiz-desc"}
				else{
					reduced.pitch <- c(0,0,1)
					contour.class <- "horiz-asc"}
					}
					}
		if(average.pitch < first.pitch) {
			if(last.pitch == average.pitch) {
					reduced.pitch <- c(1,0,0)
					contour.class <- "desc-horiz"}
				else{
					if(last.pitch < average.pitch){
						reduced.pitch <- c(1,0,-1)
						contour.class <- "descending"}
					else{
						reduced.pitch <- c(1,0,1)
						contour.class <- "concave"}
					}
			}
		}	
	contour.class
}

average.term.frequency <- function(int.vector,lower.n,upper.n){
	tf <- vector(mode="numeric",length=(upper.n-lower.n+1))
	n.weights <- c(1, 1.656225, 2.271947, 2.859356, 3.396732)
	indx <- 1
	for(i in lower.n:upper.n) {
		tf[indx] <- mean.term.frequency(int.vector,i) * n.weights[i]
		indx <- indx+1
		}
	av.tf <- sum(tf)/sum(n.weights[lower.n:upper.n])
	
	}

mean.term.frequency <- function(int.vector,n) {
	
	string <- as.character(int.vector)	
	if(n==2){
		n1 <- vector(mode="character",length=length(int.vector)-1)
		n2 <- vector(mode="character",length=length(int.vector)-1)
		for(i in 1:(length(string)-1)) {
		n1[i] <- string[i]
		n2[i] <- string[i+1]
		}
		tarray <- data.frame(n1,n2)
		tab <- table(tarray)
		tab <- as.data.frame(tab)
		tab <- tab[tab$Freq>0,]
		mean.tf <- mean(tab$Freq/(length(string)-1))
	}	
	else{
		if(n==3){
			n1 <- vector(mode="character",length=length(int.vector)-2)
			n2 <- vector(mode="character",length=length(int.vector)-2)
			n3 <- vector(mode="character",length=length(int.vector)-2)
			for(i in 1:(length(string)-2)) {
				n1[i] <- string[i]
				n2[i] <- string[i+1]
				n3[i] <- string[i+2]
			}
			tarray <- data.frame(n1,n2,n3)
			tab <- table(tarray)
			tab <- as.data.frame(tab)
			tab <- tab[tab$Freq>0,]
			mean.tf <- mean(tab$Freq/(length(string)-2))
			}
			if(n==4){
				n1 <- vector(mode="character",length=length(int.vector)-3)
				n2 <- vector(mode="character",length=length(int.vector)-3)
				n3 <- vector(mode="character",length=length(int.vector)-3)
				n4 <- vector(mode="character",length=length(int.vector)-3)
				for(i in 1:(length(string)-3)) {
					n1[i] <- string[i]
					n2[i] <- string[i+1]
					n3[i] <- string[i+2]
					n4[i] <- string[i+3]
				}
				tarray <- data.frame(n1,n2,n3,n4)
				tab <- table(tarray)
				tab <- as.data.frame(tab)
				tab <- tab[tab$Freq>0,]
				mean.tf <- mean(tab$Freq/(length(string)-3))
			}
		else{
			if(n==5){
				n1 <- vector(mode="character",length=length(int.vector)-4)
				n2 <- vector(mode="character",length=length(int.vector)-4)
				n3 <- vector(mode="character",length=length(int.vector)-4)
				n4 <- vector(mode="character",length=length(int.vector)-4)
				n5 <- vector(mode="character",length=length(int.vector)-4)
				for(i in 1:(length(string)-4)) {
					n1[i] <- string[i]
					n2[i] <- string[i+1]
					n3[i] <- string[i+2]
					n4[i] <- string[i+3]
					n5[i] <- string[i+4]
				}
				tarray <- data.frame(n1,n2,n3,n4,n5)
				tab <- table(tarray)
				tab <- as.data.frame(tab)
				tab <- tab[tab$Freq>0,]
				mean.tf <- mean(tab$Freq/(length(string)-4))
				}
			}
	mean.tf	}
	}
	
compute.tonality.vector <- function(pitch,dur16,tonal.weights) {
	data <- data.frame(p.class=as.factor(pitch%%12),weighted.p=pitch*dur16)
	tab <- tapply(data$weighted.p,data$p.class,sum)
	full.tab <- rep(0,12)
	#names(full.tab) <- seq(0:11)
	full.tab[as.numeric(names(tab))+1] <- tab
	corrmat <- apply(tonal.weights,2, function(x) cor(x,full.tab))
	}

compute.tonal.features <- function(tonality.vector) {
	A0 <- max(tonality.vector)
	A1 <- sort(tonality.vector, decreasing=TRUE)[2]
	ratio.A0A1 <- A0/A1
	tonal.spike <- A0/sum(tonality.vector[tonality.vector>0])
	if(which(tonality.vector==max(tonality.vector))>12) {
		mode <- "minor"}
	else{mode <- "major"}
	results <- data.frame(tonalness=A0,tonal.clarity=ratio.A0A1,tonal.spike,mode)
	rownames(results) <- NULL
	results
	
	}
	
make.tonal.weights <- function(maj.vector,min.vetor) {
	w.matrix <- matrix(data=NA,nrow=12,ncol=24)
	for(i in 1:12) {
		if(i==1){j <- 0}
		else{j <- 1}
		h <- i-1
		k <- h-1
		#print(c(maj.vector[((12-k)*j):(12*j)], maj.vector[1:(12-h)]))
		w.matrix[,i] <- c(maj.vector[((12-k)*j):(12*j)], maj.vector[1:(12-h)])
		w.matrix[,i+12] <- c(min.vector[((12-k)*j):(12*j)], min.vector[1:(12-h)])
		}
	w.matrix <- as.data.frame(w.matrix)			
colnames(w.matrix) <- c("C","C#","D","D#","E","F","F#","G","G#","A","A#","B", "c","c#","d","d#","e","f","f#","g","g#","a","a#","b")
	w.matrix
	}


make.duration <- function(onset) {
	dur <- vector(mode="numeric", length=2)
	dur[1] <- onset[1]
	dur[2] <- onset[length(onset)]
	dur
}


poly.contour <- function(onset, pitch) {
	onset <- onset - (onset[1]+((onset[length(onset)] - onset[1])/2))
	dur <- make.duration(onset)
	coeff.expo <- NULL
	winner.model <- poly.contour.model(onset, pitch, dur)
	poly.order <- length(winner.model$coefficients)-1
	coeffs <- coeff.extraction(winner.model)
	coeffs <- coeffs[2:4]
	}

poly.contour.model <- function (onset, pitch, dur) {
	V1 <- onset
	variables <- data.frame(V1)
	for(i in 2:(length(V1)/2)) {
		column <- V1^i
		variables[,i] <- column 
		}
		variables
	all.models <- lm(pitch ~ ., data = variables)
	winner.model <- stepAIC(all.models, trace = FALSE, direction = "both", k = log(length(V1)))
	winner.model
	#print(winner.model)
	}
	
coeff.extraction <- function(winner.model) {
		
		coefficients <- vector(mode = "numeric", length = 12)
		exponents <- vector(mode="numeric", length=11)
		var <- attr(winner.model$terms,"term.labels")
	
	for(i in 1:length(winner.model$coefficients)) {
		coefficients[i] <- winner.model$coefficients[i]
		}
	#print(coefficients)
	
	for(i in 1:length(var)) {
    		exponents[i] <- as.numeric(substring(var[i],2,3))}
		
		pc1 <- coefficients[1]
		if(length(pc1)==0) pc1 <- 0
		coefficients <- coefficients[2:12]
		
		pc2 <- coefficients[which(exponents==1)]
		if(length(pc2)==0) pc2 <- 0
		pc3 <- coefficients[which(exponents==2)]
		if(length(pc3)==0) pc3 <- 0
		pc4 <- coefficients[which(exponents==3)]
		if(length(pc4)==0) pc4 <- 0
		pc5 <- coefficients[which(exponents==4)]
		if(length(pc5)==0) pc5 <- 0
		pc6 <- coefficients[which(exponents==5)]
		if(length(pc6)==0) pc6 <- 0
		pc7 <- coefficients[which(exponents==6)]
		if(length(pc7)==0) pc7 <- 0
		pc8 <- coefficients[which(exponents==7)]
		if(length(pc8)==0) pc8 <- 0
		pc9 <- coefficients[which(exponents==8)]
		if(length(pc9)==0) pc9 <- 0
		pc10 <- coefficients[which(exponents==9)]
		if(length(pc10)==0) pc10 <- 0
		pc11 <- coefficients[which(exponents==10)]
		if(length(pc11)==0) pc11 <- 0
		pc12 <- coefficients[which(exponents==11)]
		if(length(pc12)==0) pc12 <- 0
	
		coefficients.in.order <- c(pc1,pc2,pc3,pc4,pc5,pc6,pc7,pc8,pc9,pc10,pc11,pc12)
	
	}


line.contour <- function (onset, pitch) {
	orig.melody <- data.frame(onset,pitch)
	candidate.points.pitch <- NULL
	candidate.points.onset <- NULL
	candidate.points.pitch[1] <- pitch[1]
	candidate.points.onset[1] <- onset[1]
	k <- 2
	if(length(pitch)==3 || length(pitch)==4) {
		for(i in 2:(length(pitch)-1)) {
			if( ((pitch[i] > pitch[i-1]) && (pitch[i] > pitch[i+1])) ||
				((pitch[i] < pitch[i-1]) && (pitch[i] < pitch[i+1]))  ) {
					candidate.points.pitch[k] <- pitch[i]
					candidate.points.onset[k] <- onset[i]
					k <- k+1
			}
			else{}	
		}
					
	}
	else{for(i in 3:(length(pitch)-2)) {
			if( ((pitch[i-1] < pitch[i]) && (pitch[i] > pitch[i+1])) ||
				((pitch[i-1] > pitch[i]) && (pitch[i] < pitch[i+1])) ||
				((pitch[i-1] == pitch[i]) && (pitch[i-2] < pitch[i]) && (pitch[i] > pitch[i+1])) ||
				((pitch[i-1] < pitch[i]) && (pitch[i] == pitch[i+1]) && (pitch[i+2] > pitch[i])) ||
				((pitch[i-1] == pitch[i]) && (pitch[i-2] > pitch[i]) && (pitch[i] < pitch[i+1])) ||
				((pitch[i-1] > pitch[i]) && (pitch[i] == pitch[i+1]) && (pitch[i+2] < pitch[i])) )
			 	{
					candidate.points.pitch[k] <- pitch[i]
					candidate.points.onset[k] <- onset[i]
					k <- k+1
					}
			}
		}
		candidate.points <- data.frame(candidate.points.onset, candidate.points.pitch)
		#print(candidate.points.pitch)
		#print(candidate.points.onset)
		turning.points.pitch <- NULL
		turning.points.onset <- NULL
		turning.points.pitch[1] <- pitch[1]
		turning.points.onset[1] <- onset[1]
		if(length(candidate.points.pitch) > 2) {
			j <- 2
			for(i in 2:(length(orig.melody$onset)-1)) {
				if(any(orig.melody$onset[i] == candidate.points$candidate.points.onset)) {
					if(orig.melody$pitch[i-1] != orig.melody$pitch[i+1]) {
						turning.points.pitch[j] <- pitch[i]
						turning.points.onset[j] <- onset[i]
					j <- j+1
					}
					}
				}
			}
			turning.points.pitch
			turning.points.onset
			turning.points.pitch[length(turning.points.pitch)+1] <- pitch[length(pitch)]
			turning.points.onset[length(turning.points.onset)+1] <- onset[length(onset)]
			#print(turning.points.pitch)
			#print(turning.points.onset)
			gradients <- (turning.points.pitch[2:length(turning.points.pitch)] - turning.points.pitch[1:(length(turning.points.pitch)-1)]) / (turning.points.onset[2:length(turning.points.onset)] - turning.points.onset[1:(length(turning.points.onset)-1)])
			#print(gradients)
			durations <- turning.points.onset[2:length(turning.points.onset)] - turning.points.onset[1:(length(turning.points.onset)-1)]
			#print(durations)
			weighted.gradients <- rep(gradients[1:length(gradients)],round(10*durations[1:length(durations)]))
			#print(weighted.gradients)
			#int.contour <- approx(seq(along=weighted.gradients),weighted.gradients,method="constant",rule=2,n=4)$y
			#print(int.contour)
			#int.contour
				
	}
	
compute.int.cont.feat <- function(int.cont.gradients) {
	n.grad.changes <- sum(abs(sign(diff(int.cont.gradients))))
	
	int.cont.glob.dir <- as.factor(sign(sum(int.cont.gradients)))
	int.cont.grad.mean <- mean(abs(int.cont.gradients)) 
	int.cont.grad.std <- sqrt(var(int.cont.gradients))
	tmp.enum  <- sign(int.cont.gradients[1:length(int.cont.gradients)-1]*int.cont.gradients[2:length(int.cont.gradients)])
	tmp.enum <- abs(sum(tmp.enum[tmp.enum==-1]))
	int.cont.dir.change <- tmp.enum / n.grad.changes
	int.cont.dir.change[is.na(int.cont.dir.change)] <- 0
	int.cont.grad.red <- approx(seq(along=int.cont.gradients),int.cont.gradients,method="constant",rule=2,n=4)$y
	int.cont.grad.red <- int.cont.grad.red/4
	int.cont.grad.red.c <- vector(mode="numeric",length=length(int.cont.grad.red))
	int.cont.grad.red.c[int.cont.grad.red<0.45 & int.cont.grad.red > -0.45 ] <- 0
	int.cont.grad.red.c[int.cont.grad.red<1.45 & int.cont.grad.red >= 0.45 ] <- 1
	int.cont.grad.red.c[int.cont.grad.red> -1.45 & int.cont.grad.red <= -0.45 ] <- -1
	int.cont.grad.red.c[int.cont.grad.red >= 1.45 ] <- 2
	int.cont.grad.red.c[int.cont.grad.red <= -1.45 ] <- -2
	int.contour.class <- paste(letters[int.cont.grad.red.c+3], sep="", collapse="")
	int.cont.feat <- data.frame(int.cont.glob.dir,int.cont.grad.mean,int.cont.grad.std,int.cont.dir.change,int.contour.class)

	}

	
step.contour <- function(pitch,dur16) {
	norm.dur16 <- (dur16/(sum(dur16)))*64
	if(length(which(round(norm.dur16) > 0)) < 2) {norm.pitch <- rep(pitch,round(norm.dur16)+1)}
	else{norm.pitch <- rep(pitch,round(norm.dur16))}
	}

compute.step.cont.feat <- function(step.cont.vector) {
	step.cont.glob.var <- sqrt(var(step.cont.vector))
	step.cont.loc.var <- mean(abs(diff(step.cont.vector)))
	if(step.cont.loc.var==0) {step.cont.glob.dir <- 0}
	else{step.cont.glob.dir <- cor(step.cont.vector,seq(along=step.cont.vector))}
	
	step.cont.feat <- data.frame(step.cont.glob.var,step.cont.glob.dir,step.cont.loc.var)

	}