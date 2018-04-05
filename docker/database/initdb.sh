set -e

psql -v ON_ERROR_STOP=1 --username "postgres" -d db -c "CREATE EXTENSION hstore;"
psql -v ON_ERROR_STOP=1 --username "postgres" -d db -c "CREATE EXTENSION pg_trgm;"