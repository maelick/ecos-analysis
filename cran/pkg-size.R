library(data.table)

datadir <- "/data/rdata"

index <- readRDS(file.path(datadir, "rds/index.rds"))
functions <- readRDS(file.path(datadir, "rds/functions.rds"))
functions <- functions[global == TRUE, list(loc=sum(body.loc), nfunc=.N),
                       by=c("source", "repository", "ref")]

data <- merge(index[source == "cran"], functions,
              by=c("source", "repository", "ref"), all.x=TRUE)
data[is.na(loc), loc := 0]
data[is.na(nfunc), nfunc := 0]
.
DiskUsage <- function(path) {
  res <- system2("du", c("-s", path), stdout=TRUE)
  strsplit(res, "\t")[[1]][1]
}

system.time(data$size <- with(data, mapply(function(source, repository, ref) {
  path <- file.path(datadir, "cran/packages",
                    repository, ref, repository)
  DiskUsage(path)
}, source, repository, ref)))

write.csv(data[, list(package=repository, version=ref, size, nfunc, loc)],
               "data/sizes.csv", row.names=FALSE)
