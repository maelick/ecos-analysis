library(data.table)
library(igraph)

packages <- as.data.table(read.csv(gzfile("data/packages.csv.gz"), stringsAsFactors=FALSE))
packages <- packages[, list(version=version[time == max(time)]), by="package"]
deps <- as.data.table(read.csv(gzfile("data/deps.csv.gz"), stringsAsFactors=FALSE))

deps <- merge(deps, packages, by=c("package", "version"))
deps <- unique(deps[dependency %in% packages$package, list(package, dependency)])

g <- graph.empty(directed=TRUE)
g <- g + vertices(packages$package)
g <- g + edges(t(as.matrix(deps)))

write_graph(g, file="data/latest-graph.gml", format="gml")
