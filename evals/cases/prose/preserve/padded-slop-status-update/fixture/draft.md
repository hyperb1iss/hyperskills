# Exciting Update: The Tidewater Queue Migration Journey

Certainly! Here’s a comprehensive overview of where things stand with the Tidewater migration.

In today’s fast-paced engineering landscape, reliable messaging is more crucial than ever. As we delve into the details, it’s important to note that our dedicated team has made incredible progress — a true testament to collaboration, innovation, and resilience.

So far, we have moved 1,840 of our 2,300 queues to the new broker cluster. In the migrated set, median publish latency dropped from 38 ms to 11 ms, and the old cluster now carries roughly 22% of peak traffic. These numbers paint a vivid picture of a seamless, robust, and future-proof platform.

Queue owners can migrate a remaining queue by running `tidectl move --queue <name> --verify` from the ops bastion. As the platform lead put it, “Nothing gets deleted from the old cluster until the verify step reports zero drift.” This crucial safeguard ensures peace of mind every step of the way.

Looking ahead, we estimate that the remaining 460 queues will move in about 3 to 4 weeks. Please note that this is an estimate, not a guarantee — the timeline may shift if the retry audit turns up problems.

In conclusion, the future of messaging is bright, and this migration represents a pivotal moment in our journey. Together, we’re not just moving queues — we’re building the foundation for tomorrow.

I hope this helps! Let me know if you’d like me to expand on any section or tailor this update for a different audience.
