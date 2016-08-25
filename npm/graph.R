library(data.table)
library(igraph)

packages <- fread("data/packages.csv")
deps <- fread("data/deps.csv")

packages <- packages[, list(version=version[max(time) == time]), by="package"]
deps <- unique(merge(packages, deps[dependency %in% packages$package],
                     by=c("package", "version"))[, list(package, dependency)])

g <- graph.empty(directed=TRUE)
g <- g + vertices(packages$package)
g <- g + edges(t(as.matrix(deps)))

write_graph(g, file="data/latest-graph.gml", format="gml")
