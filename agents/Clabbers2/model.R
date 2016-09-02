df = read.csv('fulltrainingdataset.csv', header = F, col.names= c('x1','x2','x3','x4','x5','x6','x7','y'), colClasses = c('numeric','numeric','numeric','numeric','numeric','numeric','numeric','numeric'))
model = lm(y ~ ., data = df)

a = as.data.frame(coef(model))
rownames(a) <- NULL
write.table(a, 'newweights.csv', quote=F, row.names=F, col.names=F, sep=",")
