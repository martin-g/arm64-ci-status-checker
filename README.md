# Elasticsearch

## Create index template

```
http --auth elastic:C1VzGS4gm679Z0GTcPpA PUT localhost:9200/_index_template/aarch64-ci-status @aarch64-ci-status-index-template.json
```

## Delete index template

```
http --auth elastic:C1VzGS4gm679Z0GTcPpA DELETE localhost:9200/_index_template/aarch64-ci-status
```

## Index some data

```
cat dummy-data.json | http --auth elastic:C1VzGS4gm679Z0GTcPpA POST localhost:9200/aarch64-ci-status-1/_doc/
```

## Bulk index data

```
http --auth elastic:C1VzGS4gm679Z0GTcPpA POST localhost:9200/_bulk/ @bulk-index-data.ndjson Content-Type:application/x-ndjson
```

## Get data

```
http --auth elastic:C1VzGS4gm679Z0GTcPpA GET localhost:9200/aarch64-ci-status-*/_search
```

## Delete all data

```
http --auth elastic:C1VzGS4gm679Z0GTcPpA POST localhost:9200/aarch64-ci-status-*/_delete_by_query/ @delete-all-docs.json
```
