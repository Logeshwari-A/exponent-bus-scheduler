# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

- 2026-05-31: Fix: Ensure station capacity bookings do not overlap.
  - Reason: candidate simulation and commit logic previously differed, allowing overlapping bookings when capacity=1.
  - Fix: Commit now frees expired slots and consumes earliest slot when capacity is full; simulation mirrors this behavior.
  - Tests: Added `tests/test_capacity_tie.py` to assert no overlaps for equal-arrival edge cases.
