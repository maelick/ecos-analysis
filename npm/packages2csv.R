library(data.table)
library(rjson)

packages <- fromJSON(file="data/versions.json")
packages <- lapply(packages, function(versions) {
  versions <- versions[grepl(".*\\..*\\..*", names(versions))]
  unlist(versions)
})
packages <- packages[sapply(packages, length) > 0]
packages <- packages[sort(names(packages))]
packages <- rbindlist(lapply(names(packages), function(p) {
  print(p)
  versions <- packages[[p]]
  data.table(package=p, version=names(versions), time=versions)
}))
write.csv(packages, gzfile("data/packages.csv.gz"), row.names=FALSE)
