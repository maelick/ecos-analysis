library(data.table)
library(rjson)

deps <- fromJSON(file="data/deps.json")
deps <- deps[sort(names(deps))]

ParseDependencies <- function(p) {
  print(p)
  versions <- deps[[p]]
  if (is.null(names(versions))) {
    names(versions) <- sapply(versions, function(v) v$version)
    versions <- lapply(versions, function(v) v$dependencies)
  }
  versions <- versions[grepl(".*\\..*\\..*", names(versions))]
  rbindlist(lapply(names(versions), function(v) {
    deps <- versions[[v]]
    if (length(deps)) {
      deps <- deps[sapply(deps, inherits, "character")]
      deps <- deps[sapply(deps, length) == 1]
      if (length(deps)) {
        data.table(package=p, version=v, dependency=names(deps), constraint=deps)
      }
    }
  }))
}

deps <- rbindlist(lapply(names(deps), ParseDependencies))
if (inherits(deps$version, "list")) {
  deps[, version := unlist(version)]
}
write.csv(deps, gzfile("data/deps.csv.gz"), row.names=FALSE)
