#!/bin/sh

# Execute file to configure new database for testing

psql -U postgres --dbname postgres -c "create database pofftest"
psql -U poff pofftest < ./pg-schema.sql
