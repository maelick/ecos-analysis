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

DiskUsage <- function(path) {
  res <- system2("du", c("-hs", path), stdout=TRUE)
  strsplit(res, "\t")[[1]][1]
}

system.time(res <- with(data, mapply(function(source, repository, ref) {
  path <- file.path(datadir, "cran/packages",
                    repository, ref, repository)
  print(path)
  if (file.exists(path)) {
    DiskUsage(path)
  } else "0"
}, source, repository, ref)))

data$size <- res

write.csv(data, "data/pkg-sizes.csv", row.names=FALSE)
