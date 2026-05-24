# schema-enum-constant-skill

## Purpose

Prevent ad-hoc strings, dictionaries, literals, and untyped structures.

## Mandatory Checks

Before adding or changing code, ask:

1. Should this be an enum?
2. Should this be a constant?
3. Should this be a config value?
4. Should this be a schema?
5. Should this be a typed object?
6. Does an equivalent already exist?
7. Is there a canonical module for this?
8. Is this repeated elsewhere?
9. Is this scientific or operational?
10. Is this stable enough to centralize?

## Preferred Design

1. Enums for baselines, regimes, stages, statuses, and artifact types
2. Constants for filenames, metric keys, marker names, and path segments
3. Schemas for configs, manifests, metrics, and result payloads
4. Objects for grouped parameters
5. Config values for scientific parameters

## Required Output

1. Existing structures found
2. New structures needed
3. Structures reused
4. Structures deleted or merged