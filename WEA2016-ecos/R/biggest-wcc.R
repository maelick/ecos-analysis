library(ggplot2)
library(data.table)
library(igraph)
library(logging)

filename <- "zcat ../../%s/data/%s.csv.gz"
ecos <- c("cran", "npm", "pypi")
basicConfig()

files <- dir("../data/graphs", full.names=TRUE, pattern="\\.graphml$")

res <- rbindlist(lapply(ecos, function(e) {
  loginfo(e)
  files <- grep(sprintf("(^|/)%s-[^/]+\\.graphml$", e), files, value=TRUE)
  rbindlist(lapply(files, function(f) {
    d <- sub("^.*/[a-z]+-([-0-9]+)\\.graphml$", "\\1", f)
    print(d)
    g <- read_graph(f, "graphml")
    if (length(V(g))) {
      components <- components(g)$csize
      data.table(ecos=e, date=d, packages=length(V(g)),
                 biggest.wcc=max(components),
                 isolated=length(components[components == 1]))
    }
  }))
}))

write.csv(res, file="../data/biggest-wcc.csv", row.names=FALSE)
res <- fread("../data/biggest-wcc.csv")

pdf("biggest-wcc-evol.pdf")

data <- res[packages > 1]
data[, biggest.wcc := biggest.wcc / packages]
data[, isolated := isolated / packages]
data[, date := as.POSIXct(date)]
data <- melt(data, id.vars=c("ecos", "date"),
             measure.vars=c("biggest.wcc", "isolated"))

p <- ggplot(data, aes(x=date, y=value, group=paste(ecos, variable)))
p <- p + scale_x_datetime() + geom_line(aes(colour=ecos, linetype=variable))
p + ylab("Relative number of packages") + xlab("Time")

data <- res[packages > 1]
data[, date := as.POSIXct(date)]
data[, biggest.wcc := as.integer(biggest.wcc)]
data <- melt(data, id.vars=c("ecos", "date"),
             measure.vars=c("packages", "biggest.wcc", "isolated"))

for (e in unique(data$ecos)) {
  p <- ggplot(data[ecos == e], aes(x=date, y=value, group=paste(ecos, variable)))
  p <- p + scale_x_datetime() + geom_line(aes(colour=ecos, linetype=variable))
  print(p + ylab(sprintf("# of %s packages", e)) + xlab("Time"))
}

dev.off()
