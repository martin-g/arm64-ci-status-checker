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
http --auth elastic:C1VzGS4gm679Z0GTcPpA POST localhost:9200/aarch64-ci-status-YYYY-MM-DD/_doc/ @dummy-data.json
```

## Bulk index data

```
http --auth elastic:C1VzGS4gm679Z0GTcPpA POST localhost:9200/_bulk/ @bulk-index-data.ndjson Content-Type:application/x-ndjson
```

## Delete index

```
http --auth elastic:C1VzGS4gm679Z0GTcPpA DELETE localhost:9200/aarch64-ci-status-2023-09-04
```

## Get data

```
http --auth elastic:C1VzGS4gm679Z0GTcPpA GET localhost:9200/aarch64-ci-status-*/_search
```

## Delete all data

```
http --auth elastic:C1VzGS4gm679Z0GTcPpA POST localhost:9200/aarch64-ci-status-*/_delete_by_query/ @delete-all-docs.json
```
