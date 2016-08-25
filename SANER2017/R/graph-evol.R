library(ggplot2)
library(data.table)
library(igraph)
library(logging)

filename <- "zcat ../../%s/data/%s.csv.gz"
filename2 <- "../../%s/data/sizes.csv"
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
  V(g)$version <- packages$version
  g + edges(t(as.matrix(unique(deps))))
}

Sizes <- function(g, sizes) {
  if (length(V(g))) {
    sizes <- sizes[list(V(g)$name, V(g)$version)]
    if (!is.null(sizes$size)) V(g)$size <- sizes$size
    if (!is.null(sizes$loc)) V(g)$loc <- sizes$loc
    if (!is.null(sizes$nfunc)) V(g)$nfunc <- sizes$nfunc
  }
  g
}

dates <- seq.Date(as.Date("2000-01-01"), as.Date("2016-04-01"), by="month")

for (e in ecos) {
  loginfo(e)
  packages <- fread(sprintf(filename, e, "packages"))
  deps <- fread(sprintf(filename, e, "deps"))
  deps <- unique(deps[, list(package, version, dependency)])
  sizes <- setkey(fread(sprintf(filename2, e)), package, version)
  for (d in as.character(dates)) {
    f <- sprintf("../data/graphs/%s-%s.graphml", e, d)
    if (!file.exists(f)) {
      g <- DependencyGraph(d, packages, deps)
      g <- Sizes(g, sizes)
      write_graph(g, f, format="graphml")
    }
  }
}
