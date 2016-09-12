library(RCurl)
library(data.table)
library(logging)
library(parallel)

logging::basicConfig()
n <- 10000
url <- "https://rubygems.org/downloads/%s-%s.gem"

packages <- fread("data/versions.csv")[, list(package, version)]
setkey(packages, package, version)
if (nrow(fread("data/sizes.csv"))) {
    packages <- packages[!fread("data/sizes.csv")[, list(package, version)]]
}

HTTPHeader <- function(url) {
  curl <- getCurlHandle()
  getURL(url, header=1, nobody=1, curl=curl)
  res <- getCurlInfo(curl)
  loginfo("HTTP response code %d for %s", res$response.code, url)
  if (res$response.code == 302) {
      HTTPHeader(res$redirect.url)
  } else res
}

GetSize <- function(package, version) {
  url <- sprintf(url, package, version)
  header <- HTTPHeader(url)
  if (header$response.code == 200) {
    header$content.length.download
  } else NA_integer_
}

InitCluster <- function(n=4) {
  cl <- makeCluster(n, type="PSOCK", outfile="")
  clusterExport(cl, list(url="url", "HTTPHeader", "GetSize"), envir=environment())
  clusterCall(cl, function() {
    library(RCurl)
    library(data.table)
    library(logging)
    logging::basicConfig()
  })
  cl
}

cl <- InitCluster(8)

while (nrow(packages)) {
  todo <- head(packages, n)
  todo[, size := clusterMap(cl, GetSize, package, version, SIMPLIFY=TRUE)]
  write.csv(rbind(fread("data/sizes.csv"), todo[, list(package, version, size)]),
            "data/sizes.csv", row.names=FALSE)
  packages <- tail(packages, -n)
}

stopCluster(cl)

sizes <- fread("data/sizes.csv")
setkey(sizes, package, version)
write.csv(sizes[!is.na(size)], "data/sizes.csv", row.names=FALSE)
