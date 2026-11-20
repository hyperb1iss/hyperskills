## Related work

Prior work agrees that restoring from a snapshot beats full initialization once function images exceed a modest size [Varnell2019; Teskey2022]. Varnell measured restore paths on a 2 GB image and reported median cold starts of 410 ms, against 1.9 s for full initialization [Varnell2019]. Teskey extended the comparison to warm pools and found that the gap narrows under sustained load [Teskey2022, Fig. 3]. Our study asks whether the advantage survives when snapshots are encrypted at rest.
