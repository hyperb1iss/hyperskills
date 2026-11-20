## Contributing factors

The March 4 checkout slowdown was caused by the connection-pool change shipped in build 4127, which lowered the per-host pool size from 64 to 16. The retry storm that followed extended the incident by 20 minutes, based on load-balancer logs. Rolling back the pool change restored p99 to its baseline within 6 minutes, which confirms the pool change as the root cause, and the same fix will hold for the two regions that were drained during the incident.
