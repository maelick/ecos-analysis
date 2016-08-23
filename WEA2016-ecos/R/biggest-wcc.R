library(ggplot2)
library(data.table)
library(igraph)
library(logging)

filename <- "zcat ../../%s/data/%s.csv.gz"
ecos <- c("cran", "npm", "pypi")
basicConfig()

Snapshot <- function(date, packages) {
  packages <- packages[as.Date(time) <= as.Date(date)]
  packages[packages[, .I[which.max(as.POSIXct(time))],
                    by="package"]$V1]
}

DependencyGraph <- function(date, packages, deps) {
  loginfo(date)
  packages <- Snapshot(date, packages)
  deps <- merge(deps, packages, by=c("package", "version"))
  deps <- deps[dependency %in% packages$package, list(package, dependency)]

  g <- graph.empty(directed=TRUE)
  g <- g + vertices(packages$package)
  g + edges(t(as.matrix(unique(deps))))
}

dates <- seq.Date(as.Date("2000-01-01"), as.Date("2016-04-01"), by="month")

res <- lapply(ecos, function(e) {
  loginfo(e)
  packages <- fread(sprintf(filename, e, "packages"))
  deps <- fread(sprintf(filename, e, "deps"))
  deps <- unique(deps[, list(package, version, dependency)])
  rbindlist(lapply(dates, function(d) {
    g <- DependencyGraph(d, packages, deps)
    if (length(V(g))) {
      data.table(ecos=e, date=d, packages=length(V(g)),
                 biggest.wcc=max(components(g)$csize))
    }
  }))
})
res <- rbindlist(res)
res[, ratio := biggest.wcc / packages]

write.csv(res, file="../data/biggest-wcc.csv", row.names=FALSE)

data <- res[packages > 1]
data[, date := as.POSIXct(date)]

pdf("biggest-wcc-evol.pdf")
p <- ggplot(data, aes(x=date, y=ratio, colour=ecos, group=ecos))
p + scale_x_datetime() + geom_line()
dev.off()
