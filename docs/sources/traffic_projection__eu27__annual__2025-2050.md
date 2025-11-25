# Traffic Projection Index (EU27, 2025-2050)

- **Dataset**: `traffic_projection__eu27__annual__2025-2050.csv`

- **Method**: Generated via `etl/clean_flights_to_index.py` from Eurostat `avia_tf_cm`. Aggregates monthly flights to annual, filters EU27, creates index with 2025=100.

- **Use case**: Demand driver for Objective 1 total fuel calculations.

- **Note**: 2025=100 baseline. Missing future years extrapolated in Obj1 computation.

