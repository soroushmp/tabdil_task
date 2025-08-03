#!/bin/bash

set -e

# Wait for Grafana to be ready
echo "Waiting for Grafana..."
until $(curl --output /dev/null --silent --head --fail http://grafana:3000); do
    printf '.'
    sleep 5
done
echo "Grafana is up and running!"

# Create the Prometheus data source
echo "Creating Prometheus data source..."
curl -s -X POST -H "Content-Type: application/json" -d '{
    "name":"Prometheus",
    "type":"prometheus",
    "url":"http://prometheus:9090",
    "access":"proxy",
    "isDefault":true
}' http://admin:admin@grafana:3000/api/datasources

# Import the dashboard
echo "Importing dashboard..."
curl -s -X POST -H "Content-Type: application/json" -d '{
    "dashboard": $(cat /etc/grafana/provisioning/dashboards/tabdil-dashboard.json),
    "overwrite": true,
    "folderId": 0
}' http://admin:admin@grafana:3000/api/dashboards/db

echo "Grafana initialization completed!"