# Elasticsearch

## Create index template

```
http --auth $ES_USER:$ES_PASSWORD --verify=false PUT $ES_URL/_index_template/aarch64-ci-status @aarch64-ci-status-index-template.json
```

## Delete index template

```
http --auth $ES_USER:$ES_PASSWORD --verify=false DELETE $ES_URL/_index_template/aarch64-ci-status
```

## Index some data

```
http --auth $ES_USER:$ES_PASSWORD --verify=false POST $ES_URL/aarch64-ci-status-YYYY-MM-DD/_doc/ @dummy-data.json
```

## Bulk index data

```
http --auth $ES_USER:$ES_PASSWORD --verify=false POST $ES_URL/_bulk/ @bulk-index-data.ndjson Content-Type:application/x-ndjson
```

## Delete index

```
http --auth $ES_USER:$ES_PASSWORD --verify=false DELETE $ES_URL/aarch64-ci-status-2023-09-03
```

## Get data

```
http --auth $ES_USER:$ES_PASSWORD --verify=false GET $ES_URL/aarch64-ci-status-*/_search
```

## Delete all data

```
http --auth $ES_USER:$ES_PASSWORD --verify=false POST $ES_URL/aarch64-ci-status-*/_delete_by_query/ @delete-all-docs.json
```
