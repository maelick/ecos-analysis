library(RCurl)
library(data.table)
library(logging)
library(parallel)

logging::basicConfig()
n <- 50000
url <- "http://registry.npmjs.org/%s/-/%s-%s.tgz"

packages <- fread("zcat data/packages.csv.gz")
setkey(packages, package, version)
packages <- packages[!fread("data/sizes.csv")[, list(package, version)]]

HTTPHeader <- function(url) {
  curl <- getCurlHandle()
  getURL(url, header=1, nobody=1, curl=curl)
  res <- getCurlInfo(curl)
  loginfo("HTTP response code %d for %s", res$response.code, url)
  res
}

GetSize <- function(package, version) {
  url <- sprintf(url, package, package, version)
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
